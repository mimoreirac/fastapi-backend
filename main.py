import uuid
from fastapi import FastAPI, APIRouter
from fastapi_users import FastAPIUsers

from db import engine, Base
from users.auth import auth_backend
from users.manager import get_user_manager
from users.models import User
from users.schemas import UserRead, UserCreate, UserUpdate
from tutors.router import router as tutors_router

app = FastAPI()

# Main API Router
api_router = APIRouter(prefix="/api/v1")

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Auth Routes
api_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

api_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

api_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Tutor Routes
api_router.include_router(
    tutors_router,
    prefix="/tutors",
    tags=["tutors"]
)

# Mount the API router to the main app
app.include_router(api_router)


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def main():
    return {"message": "Hello from fastapi-backend!"}
