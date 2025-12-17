from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductCreate(BaseModel):
    name: str
    kcal_per_100g: int
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    price_kzt_per_100g: float

class ProductOut(ProductCreate):
    id: UUID
