import uuid
from fastapi_users import schemas
from pydantic import ConfigDict


class UserRead(schemas.BaseUser[uuid.UUID]):
    full_name: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    full_name: str


class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = None
