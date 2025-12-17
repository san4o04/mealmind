from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

from app.db.base import Base  # если у тебя реально есть app/db/base.py

def utcnow():
    return datetime.now(timezone.utc)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True)  # ❗️только если ты так делал; иначе Integer
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    jti = Column(String(36), unique=True, nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
