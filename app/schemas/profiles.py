from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ProfileCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sex: str = Field(..., examples=["male", "female"])
    age: int
    height_cm: int
    weight_kg: float
    goal: str = Field(..., examples=["lose_fat", "maintain", "gain"])
    activity_level: str = Field(..., examples=["low", "medium", "high"])
    budget_kzt_per_day: int


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sex: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    budget_kzt_per_day: Optional[int] = None


class ProfileOut(ProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
