import logging

from fastapi import APIRouter
from schemas import users as users_schema
from models import users as users_model
from dependencies import db_dependency, HTTPException, verify_password, hash_password

router = APIRouter(
    prefix="/api/v1/user"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/auth")
def authenticate_user(auth_user: users_schema.AuthUserBase, db: db_dependency):
    user = db.query(users_model.Users).filter(users_model.Users.email == auth_user.username).first()
    if not user:
        logger.warning("User not found: %s", auth_user.username)
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(auth_user.password, user.password):
        logger.warning("Invalid credentials for user: %s", auth_user.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info("User authenticated: %s", auth_user.username)
    return user


@router.get("/{user_id}")
async def read_user(user_id: int, db: db_dependency):
    result = db.query(users_model.Users).filter(users_model.Users.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.post("/")
async def create_user(user: users_schema.UserBase, db: db_dependency):
    existing_user = db.query(users_model.Users).filter(users_model.Users.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = users_model.Users(
        firstname=user.firstname, surname=user.surname, email=user.email,
        password=hash_password(user.password),
        phone_number=user.phone_number, street_address=user.street_address, active=user.active
    )
    db.add(db_user)
    db.commit()
    # Optional: To return the newly created user
    # db.refresh(db_user)
    # return db_user
    return {"statusCode": 200, "message": "User created successfully"}
