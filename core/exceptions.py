"""Custom exception classes for TicketProZW."""


class TicketProException(Exception):
    """Base exception for TicketProZW application."""

    def __init__(self, message: str | None = None, status_code: int = 500, detail: str | None = None):
        # Support both 'message' and 'detail' parameters for compatibility
        self.message = detail if detail is not None else (message if message is not None else "An error occurred")
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(TicketProException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Resource not found")
        super().__init__(message=msg, status_code=404)


class BadRequestException(TicketProException):
    """Exception raised for invalid client requests."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Bad request")
        super().__init__(message=msg, status_code=400)


class UnauthorizedException(TicketProException):
    """Exception raised for authentication failures."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Unauthorized")
        super().__init__(message=msg, status_code=401)


class ForbiddenException(TicketProException):
    """Exception raised for authorization failures."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Forbidden")
        super().__init__(message=msg, status_code=403)


class ConflictException(TicketProException):
    """Exception raised for resource conflicts."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Resource conflict")
        super().__init__(message=msg, status_code=409)


class ValidationException(TicketProException):
    """Exception raised for validation errors."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Validation error")
        super().__init__(message=msg, status_code=422)


class DatabaseException(TicketProException):
    """Exception raised for database errors."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Database error")
        super().__init__(message=msg, status_code=500)


class PaymentException(TicketProException):
    """Exception raised for payment processing errors."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Payment processing error")
        super().__init__(message=msg, status_code=402)


class InventoryException(TicketProException):
    """Exception raised for inventory/stock issues."""

    def __init__(self, message: str | None = None, detail: str | None = None):
        msg = detail if detail is not None else (message if message is not None else "Insufficient inventory")
        super().__init__(message=msg, status_code=409)
