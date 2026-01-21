import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from db import get_async_session
from users.models import User
from users.manager import get_user_manager
from users.auth import auth_backend
from fastapi_users import FastAPIUsers

from appointments.models import Appointment
from appointments.schemas import AppointmentCreate, AppointmentRead, AppointmentUpdateStatus
from tutors.models import TutorProfile

router = APIRouter()

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
optional_current_user = fastapi_users.current_user(active=True, optional=True)

@router.post("/", response_model=AppointmentRead)
async def create_appointment(
    appointment_data: AppointmentCreate,
    user: Optional[User] = Depends(optional_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Validation: If not logged in, guest_details required
    if not user and not appointment_data.guest_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest details required for unauthenticated users"
        )

    # Check if tutor exists
    tutor_result = await session.execute(
        select(TutorProfile).where(TutorProfile.user_id == appointment_data.tutor_id)
    )
    if not tutor_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tutor not found")

    # Check for overlaps
    # Overlap logic: (StartA < EndB) and (EndA > StartB)
    overlap_query = select(Appointment).where(
        Appointment.tutor_id == appointment_data.tutor_id,
        Appointment.status.in_(['pending', 'confirmed']),
        Appointment.start_datetime < appointment_data.end_datetime,
        Appointment.end_datetime > appointment_data.start_datetime
    )
    result = await session.execute(overlap_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked or pending"
        )

    # Prepare data
    data = appointment_data.model_dump()
    if user:
        data['client_id'] = user.id
        data['guest_details'] = None # Ensure guest details are null if registered
    else:
        data['client_id'] = None
        # data['guest_details'] is already in data
        # Serialize Pydantic model to dict for JSON field if necessary, 
        # though Pydantic's model_dump usually handles it, SQLAlchemy JSONB expects dict/list.
        if data.get('guest_details'):
             # Ensure it's a dict, not a Pydantic model (model_dump handles nested models usually)
             pass 

    new_appointment = Appointment(**data)
    session.add(new_appointment)
    await session.commit()
    await session.refresh(new_appointment)
    
    return new_appointment

@router.get("/me", response_model=List[AppointmentRead])
async def get_my_appointments(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Return appointments where user is client OR user is tutor
    query = select(Appointment).where(
        or_(
            Appointment.client_id == user.id,
            Appointment.tutor_id == user.id
        )
    ).order_by(Appointment.start_datetime)
    
    result = await session.execute(query)
    return result.scalars().all()

@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentUpdateStatus,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Fetch appointment
    result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Only the Tutor owning the appointment can change status
    # (Optional: Admin logic could be added here)
    if appointment.tutor_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the designated tutor can update the status of this appointment"
        )

    appointment.status = status_update.status
    await session.commit()
    await session.refresh(appointment)
    return appointment
