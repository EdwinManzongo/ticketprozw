"""
Events router - Complete CRUD operations for events
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from dependencies import get_db
from models.events import Events
from models.users import Users
from schemas.events import EventCreate, EventUpdate, EventResponse
from schemas.common import PaginatedResponse, MessageResponse
from core.auth import get_current_user, require_role
from core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from core.pagination import paginate


router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"]
)


@router.get("", response_model=PaginatedResponse[EventResponse])
def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in event name, description, or location"),
    location: Optional[str] = Query(None, description="Filter by location"),
    organizer_id: Optional[int] = Query(None, description="Filter by organizer ID"),
    from_date: Optional[datetime] = Query(None, description="Filter events from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter events until this date"),
    db: Session = Depends(get_db)
):
    """
    List all events with optional filtering and pagination.

    Public endpoint - no authentication required.
    Only returns non-deleted events.
    """
    query = db.query(Events).filter(Events.deleted_at == None).options(
        joinedload(Events.ticket_types),
        joinedload(Events.organizer)
    )

    # Apply filters
    if search:
        search_filter = or_(
            Events.event_name.ilike(f"%{search}%"),
            Events.description.ilike(f"%{search}%"),
            Events.location.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if location:
        query = query.filter(Events.location.ilike(f"%{location}%"))

    if organizer_id:
        query = query.filter(Events.organizer_id == organizer_id)

    if from_date:
        query = query.filter(Events.date >= from_date)

    if to_date:
        query = query.filter(Events.date <= to_date)

    # Order by date (upcoming events first)
    query = query.order_by(Events.date.asc())

    # Paginate
    return paginate(query, skip, limit)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get a single event by ID.

    Public endpoint - no authentication required.
    """
    event = db.query(Events).filter(
        and_(Events.id == event_id, Events.deleted_at == None)
    ).options(
        joinedload(Events.ticket_types),
        joinedload(Events.organizer)
    ).first()

    if not event:
        raise NotFoundException(detail="Event not found")

    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new event.

    Requires authentication.
    Only organizers and admins can create events.
    """
    # Check if user has organizer or admin role
    if current_user.role not in ["organizer", "admin"]:
        raise ForbiddenException(
            detail="Only organizers and admins can create events"
        )

    # Check if event with same name already exists
    existing_event = db.query(Events).filter(
        and_(
            Events.event_name == event_data.event_name,
            Events.deleted_at == None
        )
    ).first()

    if existing_event:
        raise BadRequestException(
            detail="Event with this name already exists"
        )

    try:
        # Create new event
        db_event = Events(
            event_name=event_data.event_name,
            description=event_data.description,
            organizer_id=current_user.id,  # Set current user as organizer
            location=event_data.location,
            date=event_data.date,
            image=event_data.image
        )

        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        # Refresh relationships
        db.refresh(db_event, attribute_names=['ticket_types', 'organizer'])

        return db_event

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to create event: {str(e)}")


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing event.

    Requires authentication.
    Only the event organizer or admin can update the event.
    """
    # Get event
    event = db.query(Events).filter(
        and_(Events.id == event_id, Events.deleted_at == None)
    ).first()

    if not event:
        raise NotFoundException(detail="Event not found")

    # Check authorization
    if current_user.role != "admin" and event.organizer_id != current_user.id:
        raise ForbiddenException(
            detail="You can only update your own events"
        )

    try:
        # Update fields (only if provided)
        update_data = event_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(event, field, value)

        db.commit()
        db.refresh(event)

        # Refresh relationships
        db.refresh(event, attribute_names=['ticket_types', 'organizer'])

        return event

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to update event: {str(e)}")


@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete an event.

    Requires authentication.
    Only the event organizer or admin can delete the event.

    Note: This is a soft delete - the event is marked as deleted but not removed from the database.
    """
    # Get event
    event = db.query(Events).filter(
        and_(Events.id == event_id, Events.deleted_at == None)
    ).first()

    if not event:
        raise NotFoundException(detail="Event not found")

    # Check authorization
    if current_user.role != "admin" and event.organizer_id != current_user.id:
        raise ForbiddenException(
            detail="You can only delete your own events"
        )

    try:
        # Soft delete
        event.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Event deleted successfully"}

    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=f"Failed to delete event: {str(e)}")
