import uuid
from fastapi import FastAPI
from fastapi_users import FastAPIUsers

from db import engine, Base
from users.auth import auth_backend
from users.manager import get_user_manager
from users.models import User
from users.schemas import UserRead, UserCreate, UserUpdate

app = FastAPI()

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def main():
    return {"message": "Hello from fastapi-backend!"}
