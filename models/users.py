from sqlalchemy import Boolean, Column, Integer, String
from database import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, index=True)
    surname = Column(String, index=True)
    email = Column(String, unique=True)
    password = Column(String, index=True)
    phone_number = Column(String, index=True)
    street_address = Column(String, index=True)
    active = Column(Boolean, default=True)

