from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database import Base


class Events(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, index=True)
    description = Column(String, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    location = Column(String, index=True)
    date = Column(DateTime, index=True)
    image = Column(String, index=True)

