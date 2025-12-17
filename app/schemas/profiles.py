from pydantic import BaseModel, Field
from typing import Optional
from pydantic import BaseModel


class ProfileCreate(BaseModel):
    sex: str = Field(..., examples=["male", "female"])
    age: int
    height_cm: int
    weight_kg: float
    goal: str = Field(..., examples=["lose_fat", "maintain", "gain"])
    activity_level: str = Field(..., examples=["low", "medium", "high"])
    budget_kzt_per_day: int

class ProfileUpdate(BaseModel):
    sex: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    budget_kzt_per_day: Optional[int] = None

class ProfileOut(ProfileCreate):
    user_id: str
