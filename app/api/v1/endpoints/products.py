from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.infrastructure.session import get_db
from app.infrastructure.models import Product
from app.schemas.products import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])

class SeedResult(BaseModel):
    total: int
    inserted: int
    skipped: int


def build_seed_products() -> List[ProductCreate]:
    # Простой набор популярных продуктов (примерные значения на 100г)
    base = [
        ("Chicken breast", 165, 31.0, 3.6, 0.0, 350),
        ("Turkey breast", 135, 29.0, 1.5, 0.0, 380),
        ("Beef (lean)", 250, 26.0, 15.0, 0.0, 650),
        ("Egg", 155, 13.0, 11.0, 1.1, 120),
        ("Tuna canned", 116, 26.0, 1.0, 0.0, 520),
        ("Salmon", 208, 20.0, 13.0, 0.0, 900),
        ("Milk 2.5%", 52, 3.2, 2.5, 4.8, 80),
        ("Kefir", 52, 3.0, 2.5, 4.0, 70),
        ("Cottage cheese 5%", 121, 17.0, 5.0, 3.0, 180),
        ("Greek yogurt", 59, 10.0, 0.4, 3.6, 160),
        ("Rice (dry)", 365, 7.0, 0.7, 80.0, 70),
        ("Buckwheat (dry)", 343, 13.0, 3.4, 71.0, 90),
        ("Oats (dry)", 389, 17.0, 7.0, 66.0, 120),
        ("Pasta (dry)", 371, 13.0, 1.5, 75.0, 100),
        ("Potato", 77, 2.0, 0.1, 17.0, 35),
        ("Carrot", 41, 0.9, 0.2, 10.0, 40),
        ("Tomato", 18, 0.9, 0.2, 3.9, 60),
        ("Cucumber", 15, 0.7, 0.1, 3.6, 55),
        ("Onion", 40, 1.1, 0.1, 9.3, 30),
        ("Banana", 89, 1.1, 0.3, 23.0, 75),
        ("Apple", 52, 0.3, 0.2, 14.0, 60),
        ("Orange", 47, 0.9, 0.1, 12.0, 65),
        ("Bread", 265, 9.0, 3.2, 49.0, 90),
        ("Lavash", 280, 9.0, 1.5, 58.0, 95),
        ("Olive oil", 884, 0.0, 100.0, 0.0, 650),
        ("Butter", 717, 0.9, 81.0, 0.1, 700),
        ("Peanut butter", 588, 25.0, 50.0, 20.0, 600),
        ("Peanuts", 567, 26.0, 49.0, 16.0, 450),
        ("Almonds", 579, 21.0, 50.0, 22.0, 900),
        ("Beans canned", 110, 7.0, 0.5, 20.0, 160),
        ("Lentils (dry)", 352, 25.0, 1.1, 60.0, 180),
        ("Chickpeas (dry)", 364, 19.0, 6.0, 61.0, 200),
        ("Cheese", 350, 25.0, 28.0, 1.0, 900),
        ("Sugar", 387, 0.0, 0.0, 100.0, 60),
        ("Honey", 304, 0.3, 0.0, 82.0, 300),
        ("Chocolate", 546, 7.6, 31.0, 61.0, 500),
        ("Whey protein", 400, 80.0, 7.0, 8.0, 1200),
    ]

    # Добиваем до ~100: добавим варианты фруктов/овощей/круп
    fruits = ["Pear", "Grapes", "Peach", "Plum", "Kiwi", "Pomegranate", "Strawberry", "Watermelon", "Melon", "Mango"]
    veggies = ["Broccoli", "Cabbage", "Bell pepper", "Zucchini", "Spinach", "Garlic", "Eggplant", "Beetroot", "Pumpkin", "Mushrooms"]
    grains = ["Corn flakes", "Couscous (dry)", "Quinoa (dry)", "Barley (dry)", "Millet (dry)"]

    items: List[ProductCreate] = []
    for (name, kcal, p, f, c, price) in base:
        items.append(ProductCreate(
            name=name,
            kcal_per_100g=int(kcal),
            protein_per_100g=float(p),
            fat_per_100g=float(f),
            carbs_per_100g=float(c),
            price_kzt_per_100g=float(price),
        ))

    # простые оценки по фруктам/овощам
    for x in fruits:
        items.append(ProductCreate(name=x, kcal_per_100g=55, protein_per_100g=0.6, fat_per_100g=0.2, carbs_per_100g=14.0, price_kzt_per_100g=80))
    for x in veggies:
        items.append(ProductCreate(name=x, kcal_per_100g=30, protein_per_100g=2.0, fat_per_100g=0.3, carbs_per_100g=6.0, price_kzt_per_100g=60))
    for x in grains:
        items.append(ProductCreate(name=x, kcal_per_100g=370, protein_per_100g=10.0, fat_per_100g=3.0, carbs_per_100g=75.0, price_kzt_per_100g=140))

    # чтобы было ровно 100: добавим "Chicken thigh 1.."
    i = 1
    while len(items) < 100:
        items.append(ProductCreate(
            name=f"Chicken thigh #{i}",
            kcal_per_100g=209,
            protein_per_100g=18.0,
            fat_per_100g=15.0,
            carbs_per_100g=0.0,
            price_kzt_per_100g=320,
        ))
        i += 1

    return items[:100]


@router.post("", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(Product).where(Product.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Product with this name already exists")

    obj = Product(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/bulk", response_model=List[ProductOut])
def create_products_bulk(payload: List[ProductCreate], db: Session = Depends(get_db)):
    created = []
    for item in payload:
        existing = db.execute(select(Product).where(Product.name == item.name)).scalar_one_or_none()
        if existing:
            continue

        obj = Product(**item.model_dump())
        db.add(obj)
        created.append(obj)

    db.commit()
    for obj in created:
        db.refresh(obj)
    return created


@router.post("/seed", response_model=SeedResult)
def seed_products(db: Session = Depends(get_db)):
    items = build_seed_products()
    inserted = 0
    skipped = 0

    for item in items:
        existing = db.execute(select(Product).where(Product.name == item.name)).scalar_one_or_none()
        if existing:
            skipped += 1
            continue
        db.add(Product(**item.model_dump()))
        inserted += 1

    db.commit()
    return SeedResult(total=len(items), inserted=inserted, skipped=skipped)


@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    rows = db.execute(select(Product).order_by(Product.name)).scalars().all()
    return rows

@router.post("", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # простая защита от дублей по имени
    existing = db.execute(select(Product).where(Product.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Product with this name already exists")

    obj = Product(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/bulk", response_model=List[ProductOut])
def create_products_bulk(payload: List[ProductCreate], db: Session = Depends(get_db)):
    created = []
    for item in payload:
        existing = db.execute(select(Product).where(Product.name == item.name)).scalar_one_or_none()
        if existing:
            continue  # пропускаем дубли

        obj = Product(**item.model_dump())
        db.add(obj)
        created.append(obj)

    db.commit()
    for obj in created:
        db.refresh(obj)
    return created


@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    rows = db.execute(select(Product).order_by(Product.name)).scalars().all()
    return rows
