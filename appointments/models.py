import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from db import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tutor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_profiles.user_id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    guest_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    tutor = relationship("TutorProfile", backref="appointments")
    client = relationship("User", backref="appointments")
