import uuid
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    public_handle: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    user = relationship("User", backref="tutor_profile")
