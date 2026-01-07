from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from datetime import datetime


class EventBase(BaseModel):
    """Event creation schema with validation."""
    event_name: str = Field(..., min_length=3, max_length=200, description="Event name")
    description: str = Field(..., min_length=10, max_length=5000, description="Event description")
    location: str = Field(..., min_length=3, max_length=200, description="Event location")
    date: datetime = Field(..., description="Event date and time")
    image: str = Field(..., max_length=500, description="Event image URL")

    @field_validator('date')
    @classmethod
    def validate_event_date(cls, v: datetime) -> datetime:
        """Validate that event date is in the future."""
        if v <= datetime.utcnow():
            raise ValueError('Event date must be in the future')
        return v


class EventCreate(BaseModel):
    """Event creation schema (organizer_id will be set from auth token)."""
    event_name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    location: str = Field(..., min_length=3, max_length=200)
    date: datetime
    image: str = Field(..., max_length=500)

    @field_validator('date')
    @classmethod
    def validate_event_date(cls, v: datetime) -> datetime:
        """Validate that event date is in the future."""
        if v <= datetime.utcnow():
            raise ValueError('Event date must be in the future')
        return v


class EventUpdate(BaseModel):
    """Event update schema - all fields optional."""
    event_name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=5000)
    location: str | None = Field(None, min_length=3, max_length=200)
    date: datetime | None = None
    image: str | None = Field(None, max_length=500)

    @field_validator('date')
    @classmethod
    def validate_event_date(cls, v: datetime | None) -> datetime | None:
        """Validate that event date is in the future."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError('Event date must be in the future')
        return v


class EventResponse(BaseModel):
    """Event response schema."""
    id: int
    event_name: str
    description: str
    organizer_id: int
    location: str
    date: datetime
    image: str

    model_config = ConfigDict(from_attributes=True)

