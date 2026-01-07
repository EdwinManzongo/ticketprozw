"""Authentication dependencies for protecting endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from core.security import decode_token
from core.config import settings
from models.users import Users
from dependencies import get_db

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Users:
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Extract user ID from token
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Verify token type is access token
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user from database
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role

    Example:
        @router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    async def role_checker(current_user: Users = Depends(get_current_user)) -> Users:
        """Check if current user has required role."""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


# Common role dependencies for convenience
async def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_organizer_or_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Require organizer or admin role."""
    if current_user.role not in ["organizer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organizer or admin access required"
        )
    return current_user
