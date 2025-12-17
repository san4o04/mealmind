import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.models import User, Profile
from app.infrastructure.session import get_db
from app.schemas.profiles import ProfileCreate, ProfileOut
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


import uuid
from fastapi import HTTPException
from sqlalchemy import select

from app.schemas.profiles import ProfileOut, ProfileUpdate
from app.infrastructure.models import Profile


router = APIRouter(prefix="/profiles", tags=["profiles"])



@router.post("", response_model=ProfileOut)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    user = User(id=uuid.uuid4())
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        sex=payload.sex,
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        goal=payload.goal,
        activity_level=payload.activity_level,
        budget_kzt_per_day=payload.budget_kzt_per_day,
    )
    db.add(profile)
    db.commit()

    return ProfileOut(user_id=str(user.id), **payload.model_dump())


@router.get("/profiles/{user_id}")
def get_profile(user_id: UUID, db: Session = Depends(get_db)):
    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.put("/{user_id}", response_model=ProfileOut)
def update_profile(user_id: uuid.UUID, payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)

    db.commit()
    db.refresh(profile)
    return profile

