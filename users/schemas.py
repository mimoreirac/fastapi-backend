import uuid
from typing import Literal
from fastapi_users import schemas
from pydantic import ConfigDict


class UserRead(schemas.BaseUser[uuid.UUID]):
    full_name: str
    role: Literal["client", "tutor", "admin"]
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    full_name: str
    role: Literal["client", "tutor"] = "client"


class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = None
    role: Literal["client", "tutor", "admin"] | None = None
