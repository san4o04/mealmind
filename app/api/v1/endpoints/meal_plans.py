import uuid
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.infrastructure.session import get_db
from app.infrastructure.models import Profile, Product, MealPlan, MealPlanItem
from app.schemas.meal_plans import (
    MealPlanGenerateIn,
    MealPlanOut,
    MealPlanItemOut,
    MealPlanWeekGenerateIn,
    MealPlanWeekOut,
    ShoppingItemOut,
)

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])

def kcal_for(product: Product, grams: int) -> int:
    return int(round((grams / 100.0) * float(product.kcal_per_100g)))

def cost_for(product: Product, grams: int) -> float:
    return round((grams / 100.0) * float(product.price_kzt_per_100g), 2)

def totals(items: list[dict]) -> tuple[int, float]:
    kcal = sum(kcal_for(x["product"], x["grams"]) for x in items)
    cost = round(sum(cost_for(x["product"], x["grams"]) for x in items), 2)
    return kcal, cost

def cost_per_kcal(prod: Product) -> float:
    kcal100 = float(prod.kcal_per_100g)
    if kcal100 <= 0:
        return 10**9
    return float(prod.price_kzt_per_100g) / kcal100

def scale_to_target(items: list[dict], target_kcal: int) -> None:
    total_kcal, _ = totals(items)
    if total_kcal <= 0:
        return
    scale = target_kcal / total_kcal
    scale = max(0.6, min(1.8, scale))
    for x in items:
        x["grams"] = max(20, int(round(x["grams"] * scale / 10)) * 10)

def reduce_cost(items: list[dict], budget_kzt: int) -> None:
    cheapest = min((x["product"] for x in items), key=cost_per_kcal)

    for _ in range(50):
        _, total_cost = totals(items)
        if total_cost <= budget_kzt:
            break

        most_exp = max((x["product"] for x in items), key=cost_per_kcal)
        exp_item = next((x for x in items if x["product"].id == most_exp.id), None)
        cheap_item = next((x for x in items if x["product"].id == cheapest.id), None)

        if not exp_item:
            break

        if not cheap_item:
            cheap_item = {"meal_type": "dinner", "product": cheapest, "grams": 0}
            items.append(cheap_item)

        if exp_item["grams"] <= 50:
            break

        old_kcal = kcal_for(exp_item["product"], exp_item["grams"])
        exp_item["grams"] = max(50, exp_item["grams"] - 20)
        new_kcal = kcal_for(exp_item["product"], exp_item["grams"])
        removed_kcal = max(0, old_kcal - new_kcal)

        kcal_per_g = float(cheapest.kcal_per_100g) / 100.0
        if kcal_per_g > 0 and removed_kcal > 0:
            add_g = int(round((removed_kcal / kcal_per_g) / 10)) * 10
            cheap_item["grams"] += max(10, add_g)

def top_up_to_target(items: list[dict], target_kcal: int, budget_kzt: int) -> None:
    cheapest = min((x["product"] for x in items), key=cost_per_kcal)

    for _ in range(20):
        total_kcal, total_cost = totals(items)
        if total_kcal >= int(target_kcal * 0.95):
            break
        if total_cost >= budget_kzt:
            break

        cheap_item = next((x for x in items if x["product"].id == cheapest.id), None)
        if not cheap_item:
            cheap_item = {"meal_type": "dinner", "product": cheapest, "grams": 0}
            items.append(cheap_item)
        cheap_item["grams"] += 10



def fit_plan(items: list[dict], target_kcal: int, budget_kzt: int) -> list[dict]:
    if not items:
        return items

    scale_to_target(items, target_kcal)
    reduce_cost(items, budget_kzt)
    top_up_to_target(items, target_kcal, budget_kzt)

    return items



def calc_target_kcal(profile: Profile) -> int:
    w = float(profile.weight_kg)
    h = float(profile.height_cm)
    a = int(profile.age)

    sex = (profile.sex or "").lower()
    if sex == "male":
        bmr = 10 * w + 6.25 * h - 5 * a + 5
    else:
        bmr = 10 * w + 6.25 * h - 5 * a - 161

    activity = (profile.activity_level or "medium").lower()
    mult = {"low": 1.2, "medium": 1.55, "high": 1.725}.get(activity, 1.55)

    tdee = bmr * mult

    goal = (profile.goal or "maintain").lower()
    if goal == "lose_fat":
        target = tdee - 400
    elif goal == "gain":
        target = tdee + 250
    else:
        target = tdee

    target = max(1400, min(3200, target))
    return int(round(target))


def get_product_by_name(db: Session, name: str) -> Product | None:
    return db.execute(select(Product).where(Product.name == name)).scalar_one_or_none()


@router.post("/generate", response_model=MealPlanOut)
def generate_meal_plan(payload: MealPlanGenerateIn, db: Session = Depends(get_db)):
    plan_date = payload.plan_date or dt.date.today()

    profile = db.execute(
        select(Profile).where(Profile.user_id == payload.user_id)
    ).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for this user_id")

    any_product = db.execute(select(Product).limit(1)).scalar_one_or_none()
    if not any_product:
        raise HTTPException(status_code=400, detail="No products in database. Add products first.")

    target_kcal = calc_target_kcal(profile)
    budget_kzt = int(getattr(profile, "budget_kzt_per_day", 10**9) or 10**9)

    plan_template = [
        ("breakfast", [("Oats", 80), ("Banana", 120), ("Kefir 2.5%", 250)]),
        ("lunch",     [("Chicken breast (raw)", 200), ("Rice (dry)", 90)]),
        ("snack",     [("Cottage cheese 5%", 200), ("Apple", 200)]),
        ("dinner",    [("Lentils (dry)", 80), ("Buckwheat (dry)", 80)]),
    ]

    # 1) соберём raw items
    raw_items: list[dict] = []
    for meal_type, parts in plan_template:
        for prod_name, grams in parts:
            prod = get_product_by_name(db, prod_name)
            if prod:
                raw_items.append({"meal_type": meal_type, "product": prod, "grams": grams})

    if not raw_items:
        raise HTTPException(status_code=400, detail="Could not build plan: required products not found.")

    # 2) подгоним под target/budget
    raw_items = fit_plan(raw_items, target_kcal=target_kcal, budget_kzt=budget_kzt)

    # 3) сохранить
    items_to_save: list[MealPlanItem] = []
    items_out: list[MealPlanItemOut] = []
    total_kcal = 0
    total_cost = 0.0

    for x in raw_items:
        prod: Product = x["product"]
        grams: int = int(x["grams"])
        meal_type: str = x["meal_type"]

        kcal = kcal_for(prod, grams)
        cost = cost_for(prod, grams)

        items_to_save.append(
            MealPlanItem(
                meal_type=meal_type,
                product_id=prod.id,
                grams=grams,
                kcal=kcal,
                cost_kzt=cost,
            )
        )
        items_out.append(
            MealPlanItemOut(
                meal_type=meal_type,
                product_id=prod.id,
                name=prod.name,
                grams=grams,
                kcal=kcal,
                cost_kzt=cost,
            )
        )

        total_kcal += kcal
        total_cost = round(total_cost + cost, 2)

    meal_plan = MealPlan(
        user_id=payload.user_id,
        plan_date=plan_date,
        target_kcal=target_kcal,
        total_cost_kzt=total_cost,
    )
    db.add(meal_plan)
    db.flush()

    for it in items_to_save:
        it.meal_plan_id = meal_plan.id
        db.add(it)

    db.commit()
    db.refresh(meal_plan)

    return MealPlanOut(
        id=meal_plan.id,
        user_id=meal_plan.user_id,
        plan_date=meal_plan.plan_date,
        target_kcal=meal_plan.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(meal_plan.total_cost_kzt),
        items=items_out,
    )

import uuid

@router.get("", response_model=MealPlanOut)
def get_meal_plan(user_id: uuid.UUID, date: dt.date, db: Session = Depends(get_db)):
    mp = db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user_id, MealPlan.plan_date == date)
        .order_by(desc(MealPlan.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if not mp:
        raise HTTPException(status_code=404, detail="No meal plan for this date")

    rows = db.execute(
        select(MealPlanItem, Product)
        .join(Product, MealPlanItem.product_id == Product.id)
        .where(MealPlanItem.meal_plan_id == mp.id)
    ).all()

    items_out = []
    total_kcal = 0
    total_cost = 0.0

    for it, prod in rows:
        items_out.append(
            MealPlanItemOut(
                meal_type=it.meal_type,
                product_id=it.product_id,
                name=prod.name,
                grams=it.grams,
                kcal=it.kcal,
                cost_kzt=float(it.cost_kzt),
            )
        )
        total_kcal += int(it.kcal)
        total_cost = round(total_cost + float(it.cost_kzt), 2)

    return MealPlanOut(
        id=mp.id,
        user_id=mp.user_id,
        plan_date=mp.plan_date,
        target_kcal=mp.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(mp.total_cost_kzt),
        items=items_out,
    )



@router.get("/latest", response_model=MealPlanOut)
def latest_meal_plan(user_id: str, db: Session = Depends(get_db)):
    mp = db.execute(
        select(MealPlan).where(MealPlan.user_id == user_id).order_by(desc(MealPlan.created_at)).limit(1)
    ).scalar_one_or_none()
    if not mp:
        raise HTTPException(status_code=404, detail="No meal plans for this user")

    rows = db.execute(
        select(MealPlanItem, Product)
        .join(Product, MealPlanItem.product_id == Product.id)
        .where(MealPlanItem.meal_plan_id == mp.id)
    ).all()

    items_out = []
    total_kcal = 0
    total_cost = 0.0

    for it, prod in rows:
        items_out.append(
            MealPlanItemOut(
                meal_type=it.meal_type,
                product_id=it.product_id,
                name=prod.name,
                grams=it.grams,
                kcal=it.kcal,
                cost_kzt=float(it.cost_kzt),
            )
        )
        total_kcal += int(it.kcal)
        total_cost = round(total_cost + float(it.cost_kzt), 2)

    return MealPlanOut(
        id=mp.id,
        user_id=mp.user_id,
        plan_date=mp.plan_date,
        target_kcal=mp.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(mp.total_cost_kzt),
        items=items_out,
    )

@router.get("", response_model=MealPlanOut)
def get_meal_plan(user_id: str, date: dt.date, db: Session = Depends(get_db)):
    mp = db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user_id)
        .where(MealPlan.plan_date == date)
        .order_by(desc(MealPlan.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if not mp:
        raise HTTPException(status_code=404, detail="Meal plan not found for this date")

    # дальше просто reuse логики из /latest (твоя часть rows/items_out)
    rows = db.execute(
        select(MealPlanItem, Product)
        .join(Product, MealPlanItem.product_id == Product.id)
        .where(MealPlanItem.meal_plan_id == mp.id)
    ).all()

    items_out = []
    total_kcal = 0
    total_cost = 0.0
    for it, prod in rows:
        items_out.append(
            MealPlanItemOut(
                meal_type=it.meal_type,
                product_id=it.product_id,
                name=prod.name,
                grams=it.grams,
                kcal=it.kcal,
                cost_kzt=float(it.cost_kzt),
            )
        )
        total_kcal += int(it.kcal)
        total_cost = round(total_cost + float(it.cost_kzt), 2)

    return MealPlanOut(
        id=mp.id,
        user_id=mp.user_id,
        plan_date=mp.plan_date,
        target_kcal=mp.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(mp.total_cost_kzt),
        items=items_out,
    )

from fastapi import Query

@router.get("", response_model=MealPlanOut)
def get_meal_plan(user_id: str = Query(...), date: dt.date = Query(...), db: Session = Depends(get_db)):
    mp = db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user_id, MealPlan.plan_date == date)
        .order_by(desc(MealPlan.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if not mp:
        raise HTTPException(status_code=404, detail="Meal plan not found for this date")

    rows = db.execute(
        select(MealPlanItem, Product)
        .join(Product, MealPlanItem.product_id == Product.id)
        .where(MealPlanItem.meal_plan_id == mp.id)
    ).all()

    items_out = []
    total_kcal = 0
    total_cost = 0.0
    for it, prod in rows:
        items_out.append(MealPlanItemOut(
            meal_type=it.meal_type,
            product_id=it.product_id,
            name=prod.name,
            grams=it.grams,
            kcal=it.kcal,
            cost_kzt=float(it.cost_kzt),
        ))
        total_kcal += int(it.kcal)
        total_cost = round(total_cost + float(it.cost_kzt), 2)

    return MealPlanOut(
        id=mp.id,
        user_id=mp.user_id,
        plan_date=mp.plan_date,
        target_kcal=mp.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(mp.total_cost_kzt),
        items=items_out,
    )
def _plan_out_from_db(db: Session, user_id: uuid.UUID, date: dt.date) -> MealPlanOut | None:
    mp = db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user_id, MealPlan.plan_date == date)
        .order_by(desc(MealPlan.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if not mp:
        return None

    rows = db.execute(
        select(MealPlanItem, Product)
        .join(Product, MealPlanItem.product_id == Product.id)
        .where(MealPlanItem.meal_plan_id == mp.id)
    ).all()

    items_out: list[MealPlanItemOut] = []
    total_kcal = 0
    total_cost = 0.0

    for it, prod in rows:
        items_out.append(
            MealPlanItemOut(
                meal_type=it.meal_type,
                product_id=it.product_id,
                name=prod.name,
                grams=it.grams,
                kcal=it.kcal,
                cost_kzt=float(it.cost_kzt),
            )
        )
        total_kcal += int(it.kcal)
        total_cost = round(total_cost + float(it.cost_kzt), 2)

    return MealPlanOut(
        id=mp.id,
        user_id=mp.user_id,
        plan_date=mp.plan_date,
        target_kcal=mp.target_kcal,
        total_kcal=total_kcal,
        total_cost_kzt=float(mp.total_cost_kzt),
        items=items_out,
    )


def _shopping_from_plans(plans: list[MealPlanOut]) -> tuple[list[ShoppingItemOut], int, float]:
    agg: dict[str, dict] = {}
    total_kcal = 0
    total_cost = 0.0

    for p in plans:
        for it in p.items:
            total_kcal += int(it.kcal)
            total_cost = round(total_cost + float(it.cost_kzt), 2)

            key = str(it.product_id)
            if key not in agg:
                agg[key] = {
                    "product_id": it.product_id,
                    "name": it.name,
                    "total_grams": 0,
                    "total_kcal": 0,
                    "total_cost_kzt": 0.0,
                }
            agg[key]["total_grams"] += int(it.grams)
            agg[key]["total_kcal"] += int(it.kcal)
            agg[key]["total_cost_kzt"] = round(agg[key]["total_cost_kzt"] + float(it.cost_kzt), 2)

    shopping = [
        ShoppingItemOut(**v) for v in sorted(agg.values(), key=lambda x: x["total_cost_kzt"], reverse=True)
    ]
    return shopping, total_kcal, total_cost


@router.post("/generate-week", response_model=MealPlanWeekOut)
def generate_week(payload: MealPlanWeekGenerateIn, db: Session = Depends(get_db)):
    start = payload.start_date or dt.date.today()
    days = max(1, min(14, int(payload.days or 7)))  # ограничим, чтобы не улетать в бесконечность

    plans: list[MealPlanOut] = []

    for i in range(days):
        d = start + dt.timedelta(days=i)

        if payload.reuse_existing:
            existing = _plan_out_from_db(db, payload.user_id, d)
            if existing:
                plans.append(existing)
                continue

        created = generate_meal_plan(MealPlanGenerateIn(user_id=payload.user_id, plan_date=d), db)
        plans.append(created)

    shopping_list, total_week_kcal, total_week_cost = _shopping_from_plans(plans)

    return MealPlanWeekOut(
        user_id=payload.user_id,
        start_date=start,
        end_date=start + dt.timedelta(days=days - 1),
        total_week_kcal=total_week_kcal,
        total_week_cost_kzt=float(total_week_cost),
        plans=plans,
        shopping_list=shopping_list,
    )
