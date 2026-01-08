"""
Tickets router - Complete CRUD operations for tickets and ticket types
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from dependencies import get_db
from models.tickets import Tickets, TicketTypes
from models.orders import Orders
from models.events import Events
from models.users import Users
from schemas.tickets import (
    TicketCreate, TicketUpdate, TicketResponse,
    TicketTypeCreate, TicketTypeUpdate, TicketTypeResponse
)
from schemas.common import PaginatedResponse, MessageResponse
from core.auth import get_current_user
from core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from core.pagination import paginate


router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["tickets"]
)


# ====================== TICKETS ENDPOINTS ======================


@router.get("", response_model=PaginatedResponse[TicketResponse])
def list_tickets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    checked_in: Optional[bool] = Query(None, description="Filter by check-in status"),
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List tickets with optional filtering and pagination.

    Requires authentication.
    Users can only see tickets from their own orders unless they are admin.
    """
    # Base query - join with orders to filter by user
    query = db.query(Tickets).join(Orders).filter(Tickets.deleted_at == None)

    # Filter by user unless admin
    if current_user.role != "admin":
        query = query.filter(Orders.user_id == current_user.id)

    # Apply filters
    if order_id:
        query = query.filter(Tickets.order_id == order_id)

    if event_id:
        query = query.filter(Orders.event_id == event_id)

    if checked_in is not None:
        query = query.filter(Tickets.checked_in == checked_in)

    # Order by creation date
    query = query.order_by(Tickets.created_at.desc())

    # Paginate
    return paginate(query, skip, limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single ticket by ID.

    Requires authentication.
    Users can only view tickets from their own orders unless they are admin.
    """
    ticket = db.query(Tickets).join(Orders).filter(
        and_(Tickets.id == ticket_id, Tickets.deleted_at == None)
    ).first()

    if not ticket:
        raise NotFoundException(detail="Ticket not found")

    # Authorization check
    if ticket.order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to view this ticket")

    return ticket


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new ticket.

    Requires authentication.
    Users can only create tickets for their own orders unless they are admin.
    """
    # Verify order exists and belongs to user
    order = db.query(Orders).filter(
        and_(Orders.id == ticket_data.order_id, Orders.deleted_at == None)
    ).first()

    if not order:
        raise NotFoundException(detail="Order not found")

    # Authorization check
    if order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to create ticket for this order")

    # Verify ticket type exists and lock row to prevent race conditions
    ticket_type = db.query(TicketTypes).filter(
        and_(TicketTypes.id == ticket_data.ticket_type_id, TicketTypes.deleted_at == None)
    ).with_for_update().first()

    if not ticket_type:
        raise NotFoundException(detail="Ticket type not found")

    # Check inventory availability
    if ticket_type.available_quantity is None or ticket_type.available_quantity < 1:
        raise BadRequestException(
            detail=f"No tickets available for {ticket_type.name}. Sold out!"
        )

    try:
        # Create ticket
        db_ticket = Tickets(
            order_id=ticket_data.order_id,
            ticket_type_id=ticket_data.ticket_type_id,
            seat_number=ticket_data.seat_number,
            qr_code=ticket_data.qr_code,
            checked_in=ticket_data.checked_in or False,
            checked_out=ticket_data.checked_out or False
        )

        # Decrement inventory atomically
        ticket_type.available_quantity -= 1
        ticket_type.sold_quantity = (ticket_type.sold_quantity or 0) + 1

        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)

        return db_ticket

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to create ticket: {str(e)}")


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing ticket.

    Requires authentication.
    Users can only update tickets from their own orders unless they are admin.
    """
    # Get ticket with order
    ticket = db.query(Tickets).join(Orders).filter(
        and_(Tickets.id == ticket_id, Tickets.deleted_at == None)
    ).first()

    if not ticket:
        raise NotFoundException(detail="Ticket not found")

    # Authorization check
    if ticket.order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to update this ticket")

    try:
        # Update fields (only if provided)
        update_data = ticket_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(ticket, field, value)

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to update ticket: {str(e)}")


@router.delete("/{ticket_id}", response_model=MessageResponse)
def cancel_ticket(
    ticket_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a ticket (soft delete).

    Requires authentication.
    Users can only cancel tickets from their own orders unless they are admin.

    Note: This is a soft delete - the ticket is marked as deleted but not removed from the database.
    """
    # Get ticket with order
    ticket = db.query(Tickets).join(Orders).filter(
        and_(Tickets.id == ticket_id, Tickets.deleted_at == None)
    ).first()

    if not ticket:
        raise NotFoundException(detail="Ticket not found")

    # Authorization check
    if ticket.order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to cancel this ticket")

    # Check if ticket has been used
    if ticket.checked_in:
        raise BadRequestException(detail="Cannot cancel a ticket that has been checked in")

    try:
        # Soft delete
        ticket.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Ticket cancelled successfully"}

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to cancel ticket: {str(e)}")


# ====================== TICKET TYPES ENDPOINTS ======================


@router.get("/types", response_model=PaginatedResponse[TicketTypeResponse])
def list_ticket_types(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    db: Session = Depends(get_db)
):
    """
    List all ticket types with optional filtering and pagination.

    Public endpoint - no authentication required.
    Only returns non-deleted ticket types.
    """
    query = db.query(TicketTypes).filter(TicketTypes.deleted_at == None)

    # Apply filters
    if event_id:
        query = query.filter(TicketTypes.event_id == event_id)

    # Order by event ID and price
    query = query.order_by(TicketTypes.event_id.asc(), TicketTypes.price.asc())

    # Paginate
    return paginate(query, skip, limit)


@router.get("/types/{ticket_type_id}", response_model=TicketTypeResponse)
def get_ticket_type(ticket_type_id: int, db: Session = Depends(get_db)):
    """
    Get a single ticket type by ID.

    Public endpoint - no authentication required.
    """
    ticket_type = db.query(TicketTypes).filter(
        and_(TicketTypes.id == ticket_type_id, TicketTypes.deleted_at == None)
    ).first()

    if not ticket_type:
        raise NotFoundException(detail="Ticket type not found")

    return ticket_type


@router.post("/types", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(
    ticket_type_data: TicketTypeCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new ticket type for an event.

    Requires authentication.
    Only event organizers and admins can create ticket types for their events.
    """
    # Verify event exists
    event = db.query(Events).filter(
        and_(Events.id == ticket_type_data.event_id, Events.deleted_at == None)
    ).first()

    if not event:
        raise NotFoundException(detail="Event not found")

    # Authorization check - must be event organizer or admin
    if current_user.role != "admin" and event.organizer_id != current_user.id:
        raise ForbiddenException(
            detail="Only event organizers can create ticket types for their events"
        )

    # Check for duplicate ticket type name for same event
    existing_type = db.query(TicketTypes).filter(
        and_(
            TicketTypes.event_id == ticket_type_data.event_id,
            TicketTypes.name == ticket_type_data.name,
            TicketTypes.deleted_at == None
        )
    ).first()

    if existing_type:
        raise BadRequestException(
            detail="Ticket type with this name already exists for this event"
        )

    try:
        # Create ticket type with inventory management
        db_ticket_type = TicketTypes(
            event_id=ticket_type_data.event_id,
            name=ticket_type_data.name,
            description=ticket_type_data.description,
            price=ticket_type_data.price,
            quantity=ticket_type_data.quantity,
            available_quantity=ticket_type_data.quantity,  # Initialize with total quantity
            sold_quantity=0  # Start with zero sold
        )

        db.add(db_ticket_type)
        db.commit()
        db.refresh(db_ticket_type)

        return db_ticket_type

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to create ticket type: {str(e)}")


@router.put("/types/{ticket_type_id}", response_model=TicketTypeResponse)
def update_ticket_type(
    ticket_type_id: int,
    ticket_type_data: TicketTypeUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing ticket type.

    Requires authentication.
    Only event organizers and admins can update ticket types for their events.
    """
    # Get ticket type with event
    ticket_type = db.query(TicketTypes).join(Events).filter(
        and_(TicketTypes.id == ticket_type_id, TicketTypes.deleted_at == None)
    ).first()

    if not ticket_type:
        raise NotFoundException(detail="Ticket type not found")

    # Authorization check
    if current_user.role != "admin" and ticket_type.event.organizer_id != current_user.id:
        raise ForbiddenException(
            detail="Only event organizers can update ticket types for their events"
        )

    try:
        # Update fields (only if provided)
        update_data = ticket_type_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(ticket_type, field, value)

        db.commit()
        db.refresh(ticket_type)

        return ticket_type

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to update ticket type: {str(e)}")


@router.delete("/types/{ticket_type_id}", response_model=MessageResponse)
def delete_ticket_type(
    ticket_type_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a ticket type (soft delete).

    Requires authentication.
    Only event organizers and admins can delete ticket types for their events.

    Note: This is a soft delete - the ticket type is marked as deleted but not removed from the database.
    """
    # Get ticket type with event
    ticket_type = db.query(TicketTypes).join(Events).filter(
        and_(TicketTypes.id == ticket_type_id, TicketTypes.deleted_at == None)
    ).first()

    if not ticket_type:
        raise NotFoundException(detail="Ticket type not found")

    # Authorization check
    if current_user.role != "admin" and ticket_type.event.organizer_id != current_user.id:
        raise ForbiddenException(
            detail="Only event organizers can delete ticket types for their events"
        )

    try:
        # Soft delete
        ticket_type.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Ticket type deleted successfully"}

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to delete ticket type: {str(e)}")
