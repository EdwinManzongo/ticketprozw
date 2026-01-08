"""
Admin dashboard and analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from dependencies import get_db
from models.users import Users
from models.events import Events
from models.orders import Orders
from models.tickets import Tickets, TicketTypes
from models.payments import PaymentTransaction
from schemas.admin import (
    DashboardResponse,
    SalesStatsResponse,
    EventStatsResponse,
    TopEventResponse,
    RevenueByEventResponse,
    UserActivityResponse,
    PaymentMethodStatsResponse,
    TicketTransferRequest,
    TicketTransferResponse
)
from schemas.common import MessageResponse
from core.auth import get_current_user, require_role
from core.exceptions import TicketProException
from services.email_service import email_service


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    days: Optional[int] = 30,
    current_user: Users = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive admin dashboard with analytics

    - **days**: Number of days to include in statistics (default: 30)

    Only accessible by admin users
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days) if days else None

        # Build base query filters
        order_filters = [Orders.deleted_at.is_(None)]
        if start_date:
            order_filters.append(Orders.created_at >= start_date)

        # Sales Statistics
        sales_query = db.query(
            func.count(Orders.id).label('total_orders'),
            func.coalesce(func.sum(Orders.total_price), 0).label('total_sales')
        ).filter(*order_filters)

        sales_result = sales_query.first()
        total_orders = sales_result.total_orders or 0
        total_sales = float(sales_result.total_sales or 0)

        # Ticket count
        ticket_filters = [Tickets.deleted_at.is_(None)]
        if start_date:
            ticket_filters.append(Tickets.created_at >= start_date)

        total_tickets_sold = db.query(func.count(Tickets.id)).filter(*ticket_filters).scalar() or 0

        average_order_value = total_sales / total_orders if total_orders > 0 else 0

        sales_stats = SalesStatsResponse(
            total_sales=total_sales,
            total_orders=total_orders,
            total_tickets_sold=total_tickets_sold,
            average_order_value=average_order_value,
            period_start=start_date,
            period_end=end_date
        )

        # User Activity Statistics
        total_users = db.query(func.count(Users.id)).filter(Users.deleted_at.is_(None)).scalar() or 0
        active_users = db.query(func.count(Users.id)).filter(
            Users.deleted_at.is_(None),
            Users.active == True
        ).scalar() or 0

        month_ago = datetime.now() - timedelta(days=30)
        new_users_this_month = db.query(func.count(Users.id)).filter(
            Users.deleted_at.is_(None),
            Users.created_at >= month_ago
        ).scalar() or 0

        users_with_orders = db.query(func.count(func.distinct(Orders.user_id))).filter(
            Orders.deleted_at.is_(None)
        ).scalar() or 0

        user_activity = UserActivityResponse(
            total_users=total_users,
            active_users=active_users,
            new_users_this_month=new_users_this_month,
            users_with_orders=users_with_orders
        )

        # Top Events by Revenue
        top_events_query = db.query(
            Events.id,
            Events.event_name,
            func.coalesce(func.sum(Orders.total_price), 0).label('total_revenue'),
            func.count(Tickets.id).label('total_tickets_sold')
        ).join(
            Orders, Orders.event_id == Events.id
        ).outerjoin(
            Tickets, Tickets.order_id == Orders.id
        ).filter(
            Events.deleted_at.is_(None),
            Orders.deleted_at.is_(None)
        ).group_by(
            Events.id, Events.event_name
        ).order_by(
            func.sum(Orders.total_price).desc()
        ).limit(5)

        top_events = []
        for event in top_events_query.all():
            top_events.append(TopEventResponse(
                event_id=event.id,
                event_name=event.event_name,
                total_revenue=float(event.total_revenue or 0),
                total_tickets_sold=event.total_tickets_sold or 0
            ))

        # Revenue by Event (percentage breakdown)
        revenue_by_event = []
        if total_sales > 0:
            for event in top_events_query.all():
                event_revenue = float(event.total_revenue or 0)
                percentage = (event_revenue / total_sales * 100) if total_sales > 0 else 0
                revenue_by_event.append(RevenueByEventResponse(
                    event_id=event.id,
                    event_name=event.event_name,
                    revenue=event_revenue,
                    percentage=percentage
                ))

        # Payment Method Statistics
        payment_methods_query = db.query(
            PaymentTransaction.payment_method,
            func.count(PaymentTransaction.id).label('count'),
            func.coalesce(func.sum(PaymentTransaction.amount), 0).label('total_amount')
        ).filter(
            PaymentTransaction.deleted_at.is_(None),
            PaymentTransaction.status == 'succeeded'
        ).group_by(
            PaymentTransaction.payment_method
        )

        total_payment_count = db.query(func.count(PaymentTransaction.id)).filter(
            PaymentTransaction.deleted_at.is_(None),
            PaymentTransaction.status == 'succeeded'
        ).scalar() or 1  # Avoid division by zero

        payment_methods = []
        for pm in payment_methods_query.all():
            payment_methods.append(PaymentMethodStatsResponse(
                payment_method=pm.payment_method or 'Unknown',
                count=pm.count or 0,
                total_amount=float(pm.total_amount or 0),
                percentage=(pm.count / total_payment_count * 100) if total_payment_count > 0 else 0
            ))

        return DashboardResponse(
            sales_stats=sales_stats,
            user_activity=user_activity,
            top_events=top_events,
            revenue_by_event=revenue_by_event,
            payment_methods=payment_methods,
            total_revenue=total_sales,
            total_orders=total_orders,
            total_tickets_sold=total_tickets_sold
        )

    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


@router.get("/analytics/sales", response_model=SalesStatsResponse)
def get_sales_analytics(
    days: Optional[int] = 30,
    current_user: Users = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Get detailed sales analytics

    - **days**: Number of days to include (default: 30, None for all time)
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days) if days else None

        filters = [Orders.deleted_at.is_(None), Orders.payment_status == 'completed']
        if start_date:
            filters.append(Orders.created_at >= start_date)

        sales_data = db.query(
            func.count(Orders.id).label('total_orders'),
            func.coalesce(func.sum(Orders.total_price), 0).label('total_sales')
        ).filter(*filters).first()

        ticket_filters = [Tickets.deleted_at.is_(None)]
        if start_date:
            ticket_filters.append(Tickets.created_at >= start_date)

        total_tickets = db.query(func.count(Tickets.id)).filter(*ticket_filters).scalar() or 0

        total_orders = sales_data.total_orders or 0
        total_sales = float(sales_data.total_sales or 0)

        return SalesStatsResponse(
            total_sales=total_sales,
            total_orders=total_orders,
            total_tickets_sold=total_tickets,
            average_order_value=total_sales / total_orders if total_orders > 0 else 0,
            period_start=start_date,
            period_end=end_date
        )

    except Exception as e:
        logger.error(f"Error getting sales analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sales analytics: {str(e)}"
        )


@router.get("/analytics/events", response_model=List[EventStatsResponse])
def get_event_analytics(
    current_user: Users = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Get analytics for all events

    Returns detailed statistics for each event including revenue, tickets sold, and capacity
    """
    try:
        events = db.query(Events).filter(Events.deleted_at.is_(None)).all()

        event_stats = []
        for event in events:
            # Get total revenue for this event
            total_revenue = db.query(
                func.coalesce(func.sum(Orders.total_price), 0)
            ).filter(
                Orders.event_id == event.id,
                Orders.deleted_at.is_(None),
                Orders.payment_status == 'completed'
            ).scalar() or 0

            # Get total orders
            total_orders = db.query(func.count(Orders.id)).filter(
                Orders.event_id == event.id,
                Orders.deleted_at.is_(None)
            ).scalar() or 0

            # Get total tickets sold
            tickets_sold = db.query(
                func.coalesce(func.sum(TicketTypes.sold_quantity), 0)
            ).filter(
                TicketTypes.event_id == event.id,
                TicketTypes.deleted_at.is_(None)
            ).scalar() or 0

            # Get available tickets
            available_tickets = db.query(
                func.coalesce(func.sum(TicketTypes.available_quantity), 0)
            ).filter(
                TicketTypes.event_id == event.id,
                TicketTypes.deleted_at.is_(None)
            ).scalar() or 0

            # Calculate total capacity
            total_capacity = db.query(
                func.coalesce(func.sum(TicketTypes.quantity), 0)
            ).filter(
                TicketTypes.event_id == event.id,
                TicketTypes.deleted_at.is_(None)
            ).scalar() or 0

            capacity_percentage = (tickets_sold / total_capacity * 100) if total_capacity > 0 else 0

            event_stats.append(EventStatsResponse(
                event_id=event.id,
                event_name=event.event_name,
                total_revenue=float(total_revenue),
                total_orders=total_orders,
                total_tickets_sold=int(tickets_sold),
                available_tickets=int(available_tickets),
                capacity_percentage=capacity_percentage
            ))

        return event_stats

    except Exception as e:
        logger.error(f"Error getting event analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event analytics: {str(e)}"
        )


@router.get("/analytics/events/{event_id}", response_model=EventStatsResponse)
def get_single_event_analytics(
    event_id: int,
    current_user: Users = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for a specific event

    - **event_id**: Event ID to get analytics for
    """
    try:
        event = db.query(Events).filter(
            Events.id == event_id,
            Events.deleted_at.is_(None)
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Get statistics
        total_revenue = db.query(
            func.coalesce(func.sum(Orders.total_price), 0)
        ).filter(
            Orders.event_id == event_id,
            Orders.deleted_at.is_(None),
            Orders.payment_status == 'completed'
        ).scalar() or 0

        total_orders = db.query(func.count(Orders.id)).filter(
            Orders.event_id == event_id,
            Orders.deleted_at.is_(None)
        ).scalar() or 0

        tickets_sold = db.query(
            func.coalesce(func.sum(TicketTypes.sold_quantity), 0)
        ).filter(
            TicketTypes.event_id == event_id,
            TicketTypes.deleted_at.is_(None)
        ).scalar() or 0

        available_tickets = db.query(
            func.coalesce(func.sum(TicketTypes.available_quantity), 0)
        ).filter(
            TicketTypes.event_id == event_id,
            TicketTypes.deleted_at.is_(None)
        ).scalar() or 0

        total_capacity = db.query(
            func.coalesce(func.sum(TicketTypes.quantity), 0)
        ).filter(
            TicketTypes.event_id == event_id,
            TicketTypes.deleted_at.is_(None)
        ).scalar() or 0

        capacity_percentage = (tickets_sold / total_capacity * 100) if total_capacity > 0 else 0

        return EventStatsResponse(
            event_id=event.id,
            event_name=event.event_name,
            total_revenue=float(total_revenue),
            total_orders=total_orders,
            total_tickets_sold=int(tickets_sold),
            available_tickets=int(available_tickets),
            capacity_percentage=capacity_percentage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event analytics: {str(e)}"
        )


@router.post("/tickets/transfer", response_model=TicketTransferResponse)
def transfer_ticket(
    transfer_data: TicketTransferRequest,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfer a ticket to another user

    - **ticket_id**: Ticket to transfer
    - **new_owner_email**: Email of the new owner
    - **message**: Optional message to include in transfer notification
    """
    try:
        # Get the ticket
        ticket = db.query(Tickets).filter(
            Tickets.id == transfer_data.ticket_id,
            Tickets.deleted_at.is_(None)
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Get the order to verify ownership
        order = db.query(Orders).filter(Orders.id == ticket.order_id).first()

        # Check if current user owns the ticket or is admin
        if order.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to transfer this ticket"
            )

        # Find new owner by email
        new_owner = db.query(Users).filter(
            Users.email == transfer_data.new_owner_email,
            Users.deleted_at.is_(None)
        ).first()

        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {transfer_data.new_owner_email} not found"
            )

        # Can't transfer to yourself
        if new_owner.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer ticket to yourself"
            )

        # Check if ticket has been validated/used
        if ticket.checked_in or ticket.validated_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer a ticket that has already been validated or checked in"
            )

        old_owner_id = order.user_id

        # Create new order for the new owner
        new_order = Orders(
            user_id=new_owner.id,
            event_id=order.event_id,
            order_date=datetime.now(),
            total_price=0,  # Transfer is free
            payment_method="transfer",
            payment_status="completed"
        )
        db.add(new_order)
        db.flush()

        # Update ticket to belong to new order
        ticket.order_id = new_order.id
        db.commit()
        db.refresh(ticket)

        # Send email notifications
        try:
            # Get event details
            event = db.query(Events).filter(Events.id == order.event_id).first()
            ticket_type = db.query(TicketTypes).filter(TicketTypes.id == ticket.ticket_type_id).first()

            # Notify new owner
            new_owner_data = {
                "customer_name": f"{new_owner.firstname} {new_owner.surname}",
                "from_name": f"{current_user.firstname} {current_user.surname}",
                "event_name": event.event_name if event else "Unknown Event",
                "ticket_type": ticket_type.name if ticket_type else "Unknown",
                "ticket_id": ticket.id,
                "message": transfer_data.message or "No message provided"
            }

            # For now, use payment confirmation template (you can create a specific transfer template later)
            email_service.send_payment_confirmation(
                to_email=new_owner.email,
                payment_data={
                    "customer_name": new_owner_data["customer_name"],
                    "order_id": new_order.id,
                    "amount": 0,
                    "currency": "USD",
                    "payment_method": "transfer",
                    "transaction_id": f"TRANSFER_{ticket.id}",
                    "event_name": new_owner_data["event_name"]
                }
            )

            logger.info(f"Transferred ticket {ticket.id} from user {old_owner_id} to user {new_owner.id}")

        except Exception as email_error:
            logger.error(f"Failed to send transfer notification email: {str(email_error)}")

        return TicketTransferResponse(
            ticket_id=ticket.id,
            old_owner_id=old_owner_id,
            new_owner_id=new_owner.id,
            transferred_at=datetime.now(),
            message=f"Ticket successfully transferred to {new_owner.email}"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error transferring ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer ticket: {str(e)}"
        )
