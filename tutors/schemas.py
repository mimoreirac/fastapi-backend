from pydantic import BaseModel, Field, ConfigDict

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
