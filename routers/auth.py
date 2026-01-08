"""Authentication endpoints for login, register, and token management."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from core.auth import get_current_user
from dependencies import get_db
from models.users import Users
from schemas.auth import Token, RefreshTokenRequest, AccessTokenResponse
from schemas.users import UserBase

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"]
)

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Limit to 5 registrations per hour per IP
async def register(request: Request, user: UserBase, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Args:
        user: User registration data
        db: Database session

    Returns:
        JWT tokens for the new user

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = db.query(Users).filter(Users.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user with hashed password
    db_user = Users(
        firstname=user.firstname,
        surname=user.surname,
        email=user.email,
        password=hash_password(user.password),
        phone_number=user.phone_number,
        street_address=user.street_address,
        active=user.active,
        role="user"  # Default role
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate tokens
        access_token = create_access_token(data={"sub": str(db_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(db_user.id)})

        logger.info(f"New user registered: {db_user.email}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Limit to 10 login attempts per minute per IP
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Query user by email (username field contains email)
    user = db.query(Users).filter(Users.email == form_data.username).first()

    # Use constant-time comparison to prevent timing attacks
    # Return same error for both "user not found" and "wrong password"
    if not user or not verify_password(form_data.password, user.password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user account is active
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User logged in: {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit("20/minute")  # Limit to 20 token refreshes per minute per IP
async def refresh_access_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.

    Args:
        refresh_request: Request containing refresh token
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user ID (convert from string to int)
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

    # Verify user exists and is active
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me")
async def get_current_user_info(current_user: Users = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token

    Returns:
        User information (excluding password)
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firstname": current_user.firstname,
        "surname": current_user.surname,
        "role": current_user.role,
        "active": current_user.active,
        "is_verified": current_user.is_verified
    }
