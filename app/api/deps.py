from typing import Generator
from sqlalchemy.orm import Session
from app.db import SessionLocal  # <-- файл из шага 1 (проверь имя!)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
