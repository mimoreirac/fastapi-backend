from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="client", nullable=False)
