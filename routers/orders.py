"""
Orders router - Complete CRUD operations for orders
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from models.orders import Orders
from models.events import Events
from models.users import Users
from schemas.orders import OrderCreate, OrderUpdate, OrderResponse
from schemas.common import PaginatedResponse, MessageResponse
from core.auth import get_current_user
from core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from core.pagination import paginate


router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"]
)

logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    from_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter orders until this date"),
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List orders with optional filtering and pagination.

    Requires authentication.
    Users can only see their own orders unless they are admin.
    """
    # Base query - filter by user unless admin
    if current_user.role == "admin":
        query = db.query(Orders).filter(Orders.deleted_at == None)
    else:
        query = db.query(Orders).filter(
            and_(Orders.user_id == current_user.id, Orders.deleted_at == None)
        )

    # Apply filters
    if event_id:
        query = query.filter(Orders.event_id == event_id)

    if payment_status:
        query = query.filter(Orders.payment_status == payment_status)

    if from_date:
        query = query.filter(Orders.order_date >= from_date)

    if to_date:
        query = query.filter(Orders.order_date <= to_date)

    # Order by date (most recent first)
    query = query.order_by(Orders.order_date.desc())

    # Paginate
    return paginate(query, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single order by ID.

    Requires authentication.
    Users can only view their own orders unless they are admin.
    """
    order = db.query(Orders).filter(
        and_(Orders.id == order_id, Orders.deleted_at == None)
    ).first()

    if not order:
        raise NotFoundException(detail="Order not found")

    # Authorization check
    if order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to view this order")

    return order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order.

    Requires authentication.
    User ID will be taken from auth token.
    """
    # Verify event exists
    event = db.query(Events).filter(
        and_(Events.id == order_data.event_id, Events.deleted_at == None)
    ).first()

    if not event:
        raise NotFoundException(detail="Event not found")

    # Check for duplicate orders (same user, event, and date)
    existing_order = db.query(Orders).filter(
        and_(
            Orders.user_id == current_user.id,
            Orders.event_id == order_data.event_id,
            Orders.order_date == order_data.order_date,
            Orders.deleted_at == None
        )
    ).first()

    if existing_order:
        raise BadRequestException(
            detail="Order already exists for this event and time"
        )

    try:
        # Create order
        db_order = Orders(
            user_id=current_user.id,
            event_id=order_data.event_id,
            order_date=order_data.order_date or datetime.now(timezone.utc),
            total_price=order_data.total_price,
            payment_method=order_data.payment_method.value,
            payment_status=order_data.payment_status.value
        )

        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        logger.info(f"Order created: {db_order.id} for user {current_user.id}")
        return db_order

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating order: {str(e)}")
        raise BadRequestException(detail=f"Failed to create order: {str(e)}")


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing order.

    Requires authentication.
    Users can only update their own orders unless they are admin.
    Only certain fields can be updated (not user_id, event_id, or order_date).
    """
    # Get order
    order = db.query(Orders).filter(
        and_(Orders.id == order_id, Orders.deleted_at == None)
    ).first()

    if not order:
        raise NotFoundException(detail="Order not found")

    # Authorization check
    if order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to update this order")

    # Don't allow updates to completed/cancelled orders
    if order.payment_status in ["completed", "cancelled", "refunded"]:
        raise BadRequestException(
            detail=f"Cannot update order with status: {order.payment_status}"
        )

    try:
        # Update fields (only if provided)
        update_data = order_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            # Convert enum to value if needed
            if hasattr(value, 'value'):
                value = value.value
            setattr(order, field, value)

        db.commit()
        db.refresh(order)

        logger.info(f"Order updated: {order.id} by user {current_user.id}")
        return order

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating order: {str(e)}")
        raise BadRequestException(detail=f"Failed to update order: {str(e)}")


@router.delete("/{order_id}", response_model=MessageResponse)
def cancel_order(
    order_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an order (soft delete).

    Requires authentication.
    Users can only cancel their own orders unless they are admin.

    Note: This is a soft delete - the order is marked as deleted but not removed from the database.
    """
    # Get order
    order = db.query(Orders).filter(
        and_(Orders.id == order_id, Orders.deleted_at == None)
    ).first()

    if not order:
        raise NotFoundException(detail="Order not found")

    # Authorization check
    if order.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenException(detail="Not authorized to cancel this order")

    # Check if order can be cancelled
    if order.payment_status == "completed":
        raise BadRequestException(
            detail="Cannot cancel completed order. Please request a refund instead."
        )

    try:
        # Soft delete
        order.deleted_at = datetime.now(timezone.utc)
        order.payment_status = "cancelled"
        db.commit()

        logger.info(f"Order cancelled: {order.id} by user {current_user.id}")
        return {"message": "Order cancelled successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling order: {str(e)}")
        raise BadRequestException(detail=f"Failed to cancel order: {str(e)}")
