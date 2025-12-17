from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fastapi import Depends




from app.infrastructure.session import get_db
from app.infrastructure.models import User
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, MeOut
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, MeOut
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)




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

    token = create_access_token(str(user.id))
    return TokenOut(access_token=token, user_id=str(user.id))

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return TokenOut(access_token=token, user_id=str(user.id))

@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return MeOut(user_id=str(current_user.id), email=current_user.email)

def current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
     db: Session = Depends(get_db) # заменим ниже через get_db
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = creds.credentials
    try:
        user_id_str = decode_access_token(token)
        user_uuid = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user