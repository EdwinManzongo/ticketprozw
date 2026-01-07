"""
Ticket validation endpoints for QR code scanning and check-in/check-out
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json

from database import get_db
from models.users import Users
from models.tickets import Tickets, TicketTypes
from models.orders import Orders
from models.events import Events
from schemas.validation import (
    TicketValidationRequest,
    TicketValidationResponse,
    TicketCheckInRequest,
    TicketCheckInResponse,
    TicketCheckOutRequest,
    TicketCheckOutResponse,
    TicketStatusResponse
)
from services.qr_service import qr_service
from core.auth import get_current_user, require_role


router = APIRouter(prefix="/api/v1/validation", tags=["validation"])
logger = logging.getLogger(__name__)


@router.post("/validate", response_model=TicketValidationResponse)
def validate_ticket(
    validation_request: TicketValidationRequest,
    current_user: Users = Depends(require_role(["admin", "organizer"])),
    db: Session = Depends(get_db)
):
    """
    Validate a ticket by scanning its QR code

    Only admin and event organizers can validate tickets

    Args:
        validation_request: QR code data and event ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Validation result with ticket details
    """
    try:
        # Decode QR code data
        try:
            qr_data = qr_service.decode_ticket_qr_code(validation_request.qr_code_data)
        except ValueError as e:
            return TicketValidationResponse(
                valid=False,
                message=str(e)
            )

        # Validate QR code data against event
        if not qr_service.validate_qr_code_data(qr_data, validation_request.event_id):
            return TicketValidationResponse(
                valid=False,
                message="Invalid QR code for this event"
            )

        # Get ticket from database
        ticket_id = qr_data.get("ticket_id")
        ticket = db.query(Tickets).filter(
            Tickets.id == ticket_id,
            Tickets.deleted_at.is_(None)
        ).first()

        if not ticket:
            return TicketValidationResponse(
                valid=False,
                message="Ticket not found"
            )

        # Get order and check payment status
        order = db.query(Orders).filter(Orders.id == ticket.order_id).first()
        if not order or order.payment_status != "completed":
            return TicketValidationResponse(
                valid=False,
                message="Payment not confirmed for this ticket",
                ticket_id=ticket.id,
                order_id=ticket.order_id
            )

        # Get ticket type
        ticket_type = db.query(TicketTypes).filter(
            TicketTypes.id == ticket.ticket_type_id
        ).first()

        # Get customer info
        user = db.query(Users).filter(Users.id == order.user_id).first()
        customer_name = f"{user.firstname} {user.surname}" if user else "Unknown"

        # Check if organizer is authorized for this event (if not admin)
        if current_user.role != "admin":
            event = db.query(Events).filter(Events.id == validation_request.event_id).first()
            if event and event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to validate tickets for this event"
                )

        # Return validation result
        return TicketValidationResponse(
            valid=True,
            message="Ticket is valid" if not ticket.checked_in else "Ticket already checked in",
            ticket_id=ticket.id,
            order_id=ticket.order_id,
            ticket_type=ticket_type.name if ticket_type else "Unknown",
            customer_name=customer_name,
            already_checked_in=ticket.checked_in,
            checked_in_at=ticket.validated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/checkin", response_model=TicketCheckInResponse)
def check_in_ticket(
    checkin_request: TicketCheckInRequest,
    current_user: Users = Depends(require_role(["admin", "organizer"])),
    db: Session = Depends(get_db)
):
    """
    Check in a ticket (mark as validated and allow entry)

    Only admin and event organizers can check in tickets

    Args:
        checkin_request: Ticket ID to check in
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Check-in confirmation
    """
    try:
        # Get ticket
        ticket = db.query(Tickets).filter(
            Tickets.id == checkin_request.ticket_id,
            Tickets.deleted_at.is_(None)
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Check if already checked in
        if ticket.checked_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticket already checked in at {ticket.validated_at}"
            )

        # Get order and verify payment
        order = db.query(Orders).filter(Orders.id == ticket.order_id).first()
        if not order or order.payment_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment not confirmed for this ticket"
            )

        # Check authorization (organizer must own the event)
        if current_user.role != "admin":
            event = db.query(Events).filter(Events.id == order.event_id).first()
            if event and event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to check in tickets for this event"
                )

        # Get ticket type
        ticket_type = db.query(TicketTypes).filter(
            TicketTypes.id == ticket.ticket_type_id
        ).first()

        # Get customer name
        user = db.query(Users).filter(Users.id == order.user_id).first()
        customer_name = f"{user.firstname} {user.surname}" if user else "Unknown"

        # Update ticket
        ticket.checked_in = True
        ticket.validated_at = datetime.now()
        ticket.validated_by = current_user.id

        db.commit()
        db.refresh(ticket)

        logger.info(f"Ticket {ticket.id} checked in by user {current_user.id}")

        return TicketCheckInResponse(
            success=True,
            message="Ticket successfully checked in",
            ticket_id=ticket.id,
            checked_in_at=ticket.validated_at,
            customer_name=customer_name,
            ticket_type=ticket_type.name if ticket_type else "Unknown",
            seat_number=ticket.seat_number
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error checking in ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-in error: {str(e)}"
        )


@router.post("/checkout", response_model=TicketCheckOutResponse)
def check_out_ticket(
    checkout_request: TicketCheckOutRequest,
    current_user: Users = Depends(require_role(["admin", "organizer"])),
    db: Session = Depends(get_db)
):
    """
    Check out a ticket (mark as exited)

    Only admin and event organizers can check out tickets

    Args:
        checkout_request: Ticket ID to check out
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Check-out confirmation
    """
    try:
        # Get ticket
        ticket = db.query(Tickets).filter(
            Tickets.id == checkout_request.ticket_id,
            Tickets.deleted_at.is_(None)
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Check if checked in
        if not ticket.checked_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket has not been checked in yet"
            )

        # Check if already checked out
        if ticket.checked_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket already checked out"
            )

        # Check authorization
        order = db.query(Orders).filter(Orders.id == ticket.order_id).first()
        if current_user.role != "admin":
            event = db.query(Events).filter(Events.id == order.event_id).first()
            if event and event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to check out tickets for this event"
                )

        # Update ticket
        ticket.checked_out = True
        now = datetime.now()

        db.commit()
        db.refresh(ticket)

        logger.info(f"Ticket {ticket.id} checked out by user {current_user.id}")

        return TicketCheckOutResponse(
            success=True,
            message="Ticket successfully checked out",
            ticket_id=ticket.id,
            checked_out_at=now
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error checking out ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-out error: {str(e)}"
        )


@router.get("/status/{ticket_id}", response_model=TicketStatusResponse)
def get_ticket_status(
    ticket_id: int,
    current_user: Users = Depends(require_role(["admin", "organizer"])),
    db: Session = Depends(get_db)
):
    """
    Get the current status of a ticket

    Only admin and event organizers can check ticket status

    Args:
        ticket_id: Ticket ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Ticket status details
    """
    try:
        # Get ticket with relationships
        ticket = db.query(Tickets).filter(
            Tickets.id == ticket_id,
            Tickets.deleted_at.is_(None)
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Get order
        order = db.query(Orders).filter(Orders.id == ticket.order_id).first()

        # Check authorization
        if current_user.role != "admin":
            event = db.query(Events).filter(Events.id == order.event_id).first()
            if event and event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this ticket"
                )

        # Get ticket type
        ticket_type = db.query(TicketTypes).filter(
            TicketTypes.id == ticket.ticket_type_id
        ).first()

        # Get customer
        user = db.query(Users).filter(Users.id == order.user_id).first()

        return TicketStatusResponse(
            ticket_id=ticket.id,
            order_id=ticket.order_id,
            event_id=order.event_id,
            ticket_type=ticket_type.name if ticket_type else "Unknown",
            seat_number=ticket.seat_number,
            checked_in=ticket.checked_in,
            checked_out=ticket.checked_out,
            validated_at=ticket.validated_at,
            validated_by=ticket.validated_by,
            customer_name=f"{user.firstname} {user.surname}" if user else "Unknown",
            customer_email=user.email if user else "Unknown"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status error: {str(e)}"
        )
