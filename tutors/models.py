import uuid
from sqlalchemy import String, Integer, Text, ForeignKey, Time, Boolean, SmallInteger
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
    availability_patterns = relationship("AvailabilityPattern", back_populates="tutor", cascade="all, delete-orphan")


class AvailabilityPattern(Base):
    __tablename__ = "availability_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tutor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_profiles.user_id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False) # 0=Sunday, 6=Saturday
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tutor = relationship("TutorProfile", back_populates="availability_patterns")
