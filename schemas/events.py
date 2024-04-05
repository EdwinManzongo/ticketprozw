from pydantic import BaseModel
from datetime import datetime


class EventBase(BaseModel):
    event_name: str
    description: str
    organizer_id: int
    location: str
    date: datetime
    image: str

