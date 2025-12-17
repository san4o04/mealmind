from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.session import get_db
from app.infrastructure.models import User
from app.schemas.users import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut, status_code=201)
def create_user(db: Session = Depends(get_db)):
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(user_id=user.id)
