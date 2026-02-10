import uuid
from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import cast
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from db import get_async_session
from users.models import User
from users.manager import get_user_manager
from users.auth import auth_backend
from fastapi_users import FastAPIUsers

from tutors.models import TutorProfile, AvailabilityPattern
from tutors.schemas import (
    TutorProfileCreate, TutorProfileUpdate, TutorProfileRead,
    AvailabilityPatternCreate, AvailabilityPatternUpdate, AvailabilityPatternRead,
    SlotRead
)
from appointments.models import Appointment

router = APIRouter()

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)


async def get_current_tutor(user: User = Depends(current_active_user)):
    if user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users with role 'tutor' can access this resource",
        )
    return user


@router.post("/me", response_model=TutorProfileRead)
async def create_my_profile(
    profile_data: TutorProfileCreate,
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session),
):
    # Check if profile already exists
    result = await session.execute(
        select(TutorProfile).where(TutorProfile.user_id == user.id)
    )
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")

    # Check if handle is taken
    result_handle = await session.execute(
        select(TutorProfile).where(
            TutorProfile.public_handle == profile_data.public_handle
        )
    )
    if result_handle.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Public handle already taken")

    new_profile = TutorProfile(**profile_data.model_dump(), user_id=user.id)
    session.add(new_profile)
    await session.commit()
    await session.refresh(new_profile)

    # Manually attach full_name for the response since it's on the user object
    response = TutorProfileRead.model_validate(new_profile)
    response.full_name = user.full_name
    return response


@router.get("/me", response_model=TutorProfileRead)
async def get_my_profile(
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(TutorProfile).where(TutorProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    response = TutorProfileRead.model_validate(profile)
    response.full_name = user.full_name
    return response


@router.put("/me", response_model=TutorProfileRead)
async def update_my_profile(
    profile_update: TutorProfileUpdate,
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(TutorProfile).where(TutorProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = profile_update.model_dump(exclude_unset=True)

    if "public_handle" in update_data:
        # Check uniqueness if changing handle
        if update_data["public_handle"] != profile.public_handle:
            result_handle = await session.execute(
                select(TutorProfile).where(
                    TutorProfile.public_handle == update_data["public_handle"]
                )
            )
            if result_handle.scalar_one_or_none():
                raise HTTPException(
                    status_code=400, detail="Public handle already taken"
                )

    for key, value in update_data.items():
        setattr(profile, key, value)

    await session.commit()
    await session.refresh(profile)

    response = TutorProfileRead.model_validate(profile)
    response.full_name = user.full_name
    return response


GUAYAQUIL_TZ = ZoneInfo("America/Guayaquil")


@router.get("/availability", response_model=list[SlotRead])
async def get_availability_slots(
    tutor_id: uuid.UUID,
    date: date,
    session: AsyncSession = Depends(get_async_session),
):
    # 1. Get day of week (0=Sunday, 6=Saturday)
    # Python: Mon=0, Sun=6.
    day_of_week = (date.weekday() + 1) % 7

    # 2. Get Tutor Profile and Availability Patterns
    tutor_query = select(TutorProfile).where(TutorProfile.user_id == tutor_id)
    tutor_result = await session.execute(tutor_query)
    tutor = tutor_result.scalar_one_or_none()

    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    patterns_query = select(AvailabilityPattern).where(
        and_(
            AvailabilityPattern.tutor_id == tutor_id,
            AvailabilityPattern.day_of_week == day_of_week,
            AvailabilityPattern.is_active,
        )
    )
    patterns_result = await session.execute(patterns_query)
    patterns = patterns_result.scalars().all()

    # 3. Get Appointments for that day
    # Define the range for the requested date in Guayaquil time
    start_of_day = datetime.combine(date, time.min, tzinfo=GUAYAQUIL_TZ)
    end_of_day = datetime.combine(date, time.max, tzinfo=GUAYAQUIL_TZ)

    appointments_query = select(Appointment).where(
        and_(
            Appointment.tutor_id == tutor_id,
            Appointment.status.in_(["pending", "confirmed"]),
            Appointment.start_datetime >= start_of_day,
            Appointment.start_datetime <= end_of_day,
        )
    )
    appointments_result = await session.execute(appointments_query)
    appointments = appointments_result.scalars().all()

    slots = []
    duration = timedelta(minutes=tutor.session_duration_minutes)

    for pattern in patterns:
        current_time = datetime.combine(date, cast(time, pattern.start_time), tzinfo=GUAYAQUIL_TZ)
        pattern_end = datetime.combine(date, cast(time, pattern.end_time), tzinfo=GUAYAQUIL_TZ)

        while current_time + duration <= pattern_end:
            slot_start = current_time
            slot_end = current_time + duration

            # Check overlap with appointments
            is_available = True
            for appt in appointments:
                # Overlap logic: (StartA < EndB) and (EndA > StartB)
                if (slot_start < appt.end_datetime) and (slot_end > appt.start_datetime):
                    is_available = False
                    break

            slots.append(
                SlotRead(
                    start_datetime=slot_start,
                    end_datetime=slot_end,
                    available=is_available,
                    pattern_id=pattern.id,
                )
            )
            current_time += duration

    return slots


@router.get("/{public_handle}", response_model=TutorProfileRead)
async def get_tutor_profile(
    public_handle: str, session: AsyncSession = Depends(get_async_session)
):
    # Join with User to get the full name
    result = await session.execute(
        select(TutorProfile, User.full_name)
        .join(User, TutorProfile.user_id == User.id)
        .where(TutorProfile.public_handle == public_handle)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Tutor not found")

    profile, full_name = row
    response = TutorProfileRead.model_validate(profile)
    response.full_name = full_name
    return response

# Availability Patterns Endpoints

@router.post("/me/availability", response_model=AvailabilityPatternRead)
async def create_availability_pattern(
    pattern_data: AvailabilityPatternCreate,
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session)
):
    # Ensure tutor profile exists
    result = await session.execute(select(TutorProfile).where(TutorProfile.user_id == user.id))
    if not result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Tutor profile must be created first")

    new_pattern = AvailabilityPattern(**pattern_data.model_dump(), tutor_id=user.id)
    session.add(new_pattern)
    await session.commit()
    await session.refresh(new_pattern)
    return new_pattern

@router.get("/{public_handle}/availability", response_model=list[AvailabilityPatternRead])
async def get_tutor_availability(
    public_handle: str,
    session: AsyncSession = Depends(get_async_session)
):
    # Verify tutor exists
    result_tutor = await session.execute(select(TutorProfile).where(TutorProfile.public_handle == public_handle))
    tutor = result_tutor.scalar_one_or_none()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    result = await session.execute(
        select(AvailabilityPattern)
        .where(AvailabilityPattern.tutor_id == tutor.user_id)
        .where(AvailabilityPattern.is_active)
    )
    return result.scalars().all()

@router.put("/me/availability/{pattern_id}", response_model=AvailabilityPatternRead)
async def update_availability_pattern(
    pattern_id: int,
    pattern_update: AvailabilityPatternUpdate,
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(AvailabilityPattern)
        .where(AvailabilityPattern.id == pattern_id)
        .where(AvailabilityPattern.tutor_id == user.id)
    )
    pattern = result.scalar_one_or_none()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Availability pattern not found")

    update_data = pattern_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pattern, key, value)

    await session.commit()
    await session.refresh(pattern)
    return pattern

@router.delete("/me/availability/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_pattern(
    pattern_id: int,
    user: User = Depends(get_current_tutor),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(AvailabilityPattern)
        .where(AvailabilityPattern.id == pattern_id)
        .where(AvailabilityPattern.tutor_id == user.id)
    )
    pattern = result.scalar_one_or_none()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Availability pattern not found")

    await session.delete(pattern)
    await session.commit()
    return None
