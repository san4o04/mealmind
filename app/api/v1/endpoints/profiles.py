from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from app.infrastructure.session import get_db
from app.infrastructure.models import Profile, User
from app.schemas.profiles import ProfileCreate, ProfileOut, ProfileUpdate
from app.auth.deps import get_current_user




router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.post("/me", response_model=ProfileOut, status_code=201)
def create_my_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if exists:
        raise HTTPException(status_code=409, detail="Profile already exists")

    profile = Profile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)

    db.commit()
    db.refresh(profile)
    return profile

from fastapi import HTTPException
from sqlalchemy import select

@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.post("/me", response_model=ProfileOut, status_code=201)
def create_my_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if exists:
        raise HTTPException(status_code=409, detail="Profile already exists")

    profile = Profile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)

    db.commit()
    db.refresh(profile)
    return profile
