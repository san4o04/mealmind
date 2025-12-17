from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    refresh_token: Optional[str] = None


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


class MeOut(BaseModel):
    user_id: str
    email: EmailStr
