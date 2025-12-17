from pydantic import BaseModel
from uuid import UUID

class UserOut(BaseModel):
    user_id: UUID
