import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from datetime import datetime

class GuestDetails(BaseModel):
    name: str
    email: EmailStr

class AppointmentBase(BaseModel):
    tutor_id: uuid.UUID
    start_datetime: datetime
    end_datetime: datetime
    notes: str | None = None

    @field_validator('end_datetime')
    def check_time_order(cls, v, values):
        if 'start_datetime' in values.data and v <= values.data['start_datetime']:
            raise ValueError('end_datetime must be after start_datetime')
        return v

class AppointmentCreate(AppointmentBase):
    guest_details: GuestDetails | None = None

class AppointmentRead(AppointmentBase):
    id: int
    client_id: uuid.UUID | None = None
    guest_details: GuestDetails | None = None
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AppointmentUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|declined|cancelled)$")
