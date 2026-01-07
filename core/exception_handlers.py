"""Global exception handlers for TicketProZW."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from core.exceptions import TicketProException

logger = logging.getLogger(__name__)


async def ticketpro_exception_handler(request: Request, exc: TicketProException) -> JSONResponse:
    """Handle custom TicketProException errors."""
    logger.warning(f"TicketProException: {exc.message} - Path: {request.url.path}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error: {errors} - Path: {request.url.path}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": errors,
            "path": str(request.url.path)
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(f"Database error: {str(exc)} - Path: {request.url.path}", exc_info=True)

    # Check if it's an integrity error (unique constraint, foreign key, etc.)
    if isinstance(exc, IntegrityError):
        message = "Database constraint violation. The operation could not be completed."

        # Try to extract meaningful error message
        error_str = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

        if "unique constraint" in error_str.lower():
            message = "A record with this information already exists."
        elif "foreign key" in error_str.lower():
            message = "Referenced resource does not exist."

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "IntegrityError",
                "message": message,
                "path": str(request.url.path)
            }
        )

    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "A database error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )
