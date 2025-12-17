import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def utcnow():
    return datetime.now(timezone.utc)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)

def issue_refresh_token(db: Session, user_id) -> str:
    raw, token_hash = _new_refresh_token()
    jti = str(uuid.uuid4())
    expires_at = utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db.execute(
        text("""
            INSERT INTO refresh_tokens (user_id, jti, token_hash, expires_at, created_at)
            VALUES (:user_id, :jti, :token_hash, :expires_at, :created_at)
        """),
        {
            "user_id": user_id,
            "jti": jti,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "created_at": utcnow(),
        },
    )
    db.commit()
    return raw

def rotate_refresh_token(db: Session, refresh_token: str) -> object:
    token_hash = hash_token(refresh_token)

    row = db.execute(
        text("""
            SELECT user_id, expires_at, revoked_at
            FROM refresh_tokens
            WHERE token_hash = :token_hash
            LIMIT 1
        """),
        {"token_hash": token_hash},
    ).mappings().first()

    if not row:
        raise ValueError("not_found")
    if row["revoked_at"] is not None:
        raise ValueError("revoked")
    if row["expires_at"] <= utcnow():
        raise ValueError("expired")

    # revoke old token
    db.execute(
        text("""
            UPDATE refresh_tokens
            SET revoked_at = :now
            WHERE token_hash = :token_hash AND revoked_at IS NULL
        """),
        {"now": utcnow(), "token_hash": token_hash},
    )

    # issue new one
    new_raw, new_hash = _new_refresh_token()
    new_jti = str(uuid.uuid4())
    new_exp = utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db.execute(
        text("""
            INSERT INTO refresh_tokens (user_id, jti, token_hash, expires_at, created_at)
            VALUES (:user_id, :jti, :token_hash, :expires_at, :created_at)
        """),
        {
            "user_id": row["user_id"],
            "jti": new_jti,
            "token_hash": new_hash,
            "expires_at": new_exp,
            "created_at": utcnow(),
        },
    )

    db.commit()
    return row["user_id"], new_raw

def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    db.execute(
        text("""
            UPDATE refresh_tokens
            SET revoked_at = :now
            WHERE token_hash = :token_hash AND revoked_at IS NULL
        """),
        {"now": utcnow(), "token_hash": token_hash},
    )
    db.commit()
