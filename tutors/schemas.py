from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import time

class TutorProfileBase(BaseModel):
    public_handle: str = Field(..., max_length=50, pattern="^[a-z0-9-]+$")
    specialty: str | None = Field(None, max_length=100)
    bio: str | None = None
    session_duration_minutes: int = Field(60, ge=15, le=180)

class TutorProfileCreate(TutorProfileBase):
    pass

class TutorProfileUpdate(BaseModel):
    public_handle: str | None = Field(None, max_length=50, pattern="^[a-z0-9-]+$")
    specialty: str | None = Field(None, max_length=100)
    bio: str | None = None
    session_duration_minutes: int | None = Field(None, ge=15, le=180)

class TutorProfileRead(TutorProfileBase):
    # We might want to include the user's full name here in the future
    full_name: str | None = None 
    
    model_config = ConfigDict(from_attributes=True)


class AvailabilityPatternBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    start_time: time
    end_time: time
    is_active: bool = True

    @field_validator('end_time')
    def check_time_order(cls, v, values):
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class AvailabilityPatternCreate(AvailabilityPatternBase):
    pass

class AvailabilityPatternUpdate(BaseModel):
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None

class AvailabilityPatternRead(AvailabilityPatternBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
