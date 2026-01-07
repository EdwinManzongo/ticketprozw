from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import models.users as users_model
import models.events as events_model
import models.orders as orders_model
import models.tickets as tickets_model
from database import engine, SessionLocal
from core.security import verify_password, hash_password

users_model.Base.metadata.create_all(bind=engine)
events_model.Base.metadata.create_all(bind=engine)
orders_model.Base.metadata.create_all(bind=engine)
tickets_model.Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
