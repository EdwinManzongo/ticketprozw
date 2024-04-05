from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import models.users as users_model
import models.events as events_model
import models.orders as orders_model
import models.tickets as tickets_model
from database import engine, SessionLocal

users_model.Base.metadata.create_all(bind=engine)
events_model.Base.metadata.create_all(bind=engine)
orders_model.Base.metadata.create_all(bind=engine)
tickets_model.Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)