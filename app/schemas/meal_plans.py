from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
import datetime as dt


class MealPlanGenerateIn(BaseModel):
    user_id: UUID
    plan_date: Optional[dt.date] = None

    # optional overrides (если хочешь вручную)
    target_kcal: Optional[int] = None
    budget_kzt: Optional[int] = None


class MealPlanItemOut(BaseModel):
    meal_type: str
    product_id: UUID
    name: str
    grams: int
    kcal: int
    cost_kzt: float


class MealPlanOut(BaseModel):
    id: UUID
    user_id: UUID
    plan_date: dt.date
    target_kcal: int
    total_kcal: int
    total_cost_kzt: float
    items: List[MealPlanItemOut]

class ShoppingItemOut(BaseModel):
    product_id: UUID
    name: str
    total_grams: int
    total_kcal: int
    total_cost_kzt: float


class MealPlanWeekGenerateIn(BaseModel):
    user_id: UUID
    start_date: Optional[dt.date] = None
    days: int = 7
    reuse_existing: bool = True  # если уже есть план на дату — не перегенерить


class MealPlanWeekOut(BaseModel):
    user_id: UUID
    start_date: dt.date
    end_date: dt.date
    total_week_kcal: int
    total_week_cost_kzt: float
    plans: List[MealPlanOut]
    shopping_list: List[ShoppingItemOut]
