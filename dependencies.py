import bcrypt

from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def verify_password(verify_pwd: str, hashed: str) -> bool:
    try:
        verify_pwd_bytes = verify_pwd.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')

        is_valid = bcrypt.checkpw(verify_pwd_bytes, hashed_bytes)
        return is_valid
    except ValueError:
        return False


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')
