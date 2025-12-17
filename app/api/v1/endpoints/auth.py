from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.session import get_db
from app.infrastructure.models import User
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, MeOut, RefreshIn, LogoutIn

from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.deps import get_current_user

from app.auth.refresh_store import (
    issue_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    exists = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=email, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(str(user.id))
    refresh = issue_refresh_token(db, user.id)

    return TokenOut(access_token=access, refresh_token=refresh, user_id=str(user.id))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    refresh = issue_refresh_token(db, user.id)

    return TokenOut(access_token=access, refresh_token=refresh, user_id=str(user.id))


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    try:
        user_id, new_refresh = rotate_refresh_token(db, payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(str(user_id))
    return TokenOut(access_token=access, refresh_token=new_refresh, user_id=str(user_id))


@router.post("/logout")
def logout(payload: LogoutIn, db: Session = Depends(get_db)):
    revoke_refresh_token(db, payload.refresh_token)
    return {"detail": "ok"}


@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return MeOut(user_id=str(current_user.id), email=current_user.email)
