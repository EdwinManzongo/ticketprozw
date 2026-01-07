from pydantic import BaseModel, Field, field_validator, ConfigDict


class TicketTypeBase(BaseModel):
    """Ticket type base schema with validation."""
    event_id: int = Field(..., gt=0, description="Event ID")
    name: str = Field(..., min_length=3, max_length=100, description="Ticket type name")
    description: str = Field(..., min_length=10, max_length=1000, description="Ticket type description")
    price: float = Field(..., ge=0, le=100000, description="Ticket price")
    quantity: int = Field(..., ge=1, le=100000, description="Total quantity available")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate and round price."""
        if v < 0:
            raise ValueError('Price cannot be negative')
        return round(v, 2)

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 100000:
            raise ValueError('Quantity exceeds maximum allowed (100,000)')
        return v


class TicketTypeCreate(BaseModel):
    """Ticket type creation schema."""
    event_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    price: float = Field(..., ge=0, le=100000)
    quantity: int = Field(..., ge=1, le=100000)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Price cannot be negative')
        return round(v, 2)


class TicketTypeUpdate(BaseModel):
    """Ticket type update schema."""
    name: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, min_length=10, max_length=1000)
    price: float | None = Field(None, ge=0, le=100000)
    quantity: int | None = Field(None, ge=1, le=100000)


class TicketTypeResponse(BaseModel):
    """Ticket type response schema."""
    id: int
    event_id: int
    name: str
    description: str
    price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    """Ticket base schema with validation."""
    order_id: int = Field(..., gt=0, description="Order ID")
    ticket_type_id: int = Field(..., gt=0, description="Ticket type ID")
    seat_number: str = Field(..., max_length=50, description="Seat number")
    qr_code: str = Field(default="", max_length=500, description="QR code data")
    checked_in: bool = Field(default=False, description="Check-in status")
    checked_out: bool = Field(default=False, description="Check-out status")


class TicketCreate(BaseModel):
    """Ticket creation schema (order_id will be set from context)."""
    ticket_type_id: int = Field(..., gt=0)
    seat_number: str = Field(..., max_length=50)


class TicketUpdate(BaseModel):
    """Ticket update schema."""
    seat_number: str | None = Field(None, max_length=50)
    checked_in: bool | None = None
    checked_out: bool | None = None


class TicketResponse(BaseModel):
    """Ticket response schema."""
    id: int
    order_id: int
    ticket_type_id: int
    seat_number: str
    qr_code: str
    checked_in: bool
    checked_out: bool

    model_config = ConfigDict(from_attributes=True)


