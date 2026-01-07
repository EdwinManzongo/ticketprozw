"""
Payment processing endpoints for handling Stripe payments
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models.users import Users
from models.orders import Orders
from models.payments import PaymentTransaction
from schemas.payments import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentTransactionResponse
)
from schemas.common import MessageResponse
from services.stripe_service import stripe_service
from services.email_service import email_service
from services.qr_service import qr_service
from core.auth import get_current_user
from core.config import settings


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
logger = logging.getLogger(__name__)


@router.post("/create-payment-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe payment intent for an order

    - **order_id**: Order ID to create payment for
    - **amount**: Payment amount in dollars
    - **currency**: Three-letter currency code (default: USD)
    """
    try:
        # Verify order exists and belongs to current user
        order = db.query(Orders).filter(
            Orders.id == payment_data.order_id,
            Orders.deleted_at.is_(None)
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Only order owner or admin can create payment
        if order.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create payment for this order"
            )

        # Check if payment already exists for this order
        existing_payment = db.query(PaymentTransaction).filter(
            PaymentTransaction.order_id == payment_data.order_id,
            PaymentTransaction.deleted_at.is_(None)
        ).first()

        if existing_payment and existing_payment.status == "succeeded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already completed for this order"
            )

        # Create payment intent via Stripe
        metadata = {
            "order_id": str(payment_data.order_id),
            "user_id": str(current_user.id),
            "user_email": current_user.email
        }

        payment_intent = stripe_service.create_payment_intent(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata=metadata
        )

        # Create or update payment transaction record
        if existing_payment:
            existing_payment.stripe_payment_intent_id = payment_intent["payment_intent_id"]
            existing_payment.amount = payment_data.amount
            existing_payment.currency = payment_data.currency
            existing_payment.status = payment_intent["status"]
            db.commit()
            db.refresh(existing_payment)
        else:
            payment_transaction = PaymentTransaction(
                order_id=payment_data.order_id,
                stripe_payment_intent_id=payment_intent["payment_intent_id"],
                amount=payment_data.amount,
                currency=payment_data.currency,
                status=payment_intent["status"]
            )
            db.add(payment_transaction)
            db.commit()
            db.refresh(payment_transaction)

        logger.info(f"Created payment intent for order {payment_data.order_id}: {payment_intent['payment_intent_id']}")

        return PaymentIntentResponse(**payment_intent)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )


@router.get("/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
def get_payment_transaction(
    transaction_id: int,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment transaction details

    - **transaction_id**: Payment transaction ID
    """
    try:
        transaction = db.query(PaymentTransaction).filter(
            PaymentTransaction.id == transaction_id,
            PaymentTransaction.deleted_at.is_(None)
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment transaction not found"
            )

        # Check authorization
        order = db.query(Orders).filter(Orders.id == transaction.order_id).first()
        if order.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this payment transaction"
            )

        return PaymentTransactionResponse.model_validate(transaction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving payment transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment transaction: {str(e)}"
        )


@router.post("/{payment_intent_id}/refund", response_model=MessageResponse)
def create_refund(
    payment_intent_id: str,
    amount: Optional[float] = None,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a refund for a payment

    - **payment_intent_id**: Stripe payment intent ID
    - **amount**: Amount to refund in dollars (optional, defaults to full refund)
    """
    try:
        # Find payment transaction
        transaction = db.query(PaymentTransaction).filter(
            PaymentTransaction.stripe_payment_intent_id == payment_intent_id,
            PaymentTransaction.deleted_at.is_(None)
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment transaction not found"
            )

        # Check authorization (only admin or order owner can refund)
        order = db.query(Orders).filter(Orders.id == transaction.order_id).first()
        if current_user.role != "admin" and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to refund this payment"
            )

        # Create refund via Stripe
        refund = stripe_service.create_refund(
            payment_intent_id=payment_intent_id,
            amount=amount
        )

        # Update transaction status
        transaction.status = "refunded"
        db.commit()

        # Update order payment status
        order.payment_status = "refunded"
        db.commit()

        logger.info(f"Created refund {refund['id']} for payment {payment_intent_id}")

        return MessageResponse(
            message=f"Refund processed successfully. Refund ID: {refund['id']}"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating refund: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create refund: {str(e)}"
        )


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events

    This endpoint receives webhook events from Stripe to update payment statuses
    """
    try:
        # Get raw body
        payload = await request.body()

        # Verify webhook signature
        if not settings.STRIPE_WEBHOOK_SECRET:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured, skipping signature verification")
        else:
            is_valid = stripe_service.verify_webhook_signature(
                payload=payload,
                signature=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook signature"
                )

        # Parse event
        import json
        event = json.loads(payload)
        event_type = event.get("type")

        logger.info(f"Received Stripe webhook: {event_type}")

        # Handle different event types
        if event_type == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            payment_intent_id = payment_intent["id"]

            # Update payment transaction status
            transaction = db.query(PaymentTransaction).filter(
                PaymentTransaction.stripe_payment_intent_id == payment_intent_id
            ).first()

            if transaction:
                transaction.status = "succeeded"
                transaction.payment_method = payment_intent.get("payment_method")
                transaction.stripe_customer_id = payment_intent.get("customer")
                transaction.stripe_charge_id = payment_intent.get("latest_charge")

                # Update order payment status
                order = db.query(Orders).filter(Orders.id == transaction.order_id).first()
                if order:
                    order.payment_status = "completed"

                db.commit()
                logger.info(f"Updated payment status to succeeded for {payment_intent_id}")

                # Send payment confirmation email
                if order and order.user:
                    try:
                        from models.events import Events
                        event = db.query(Events).filter(Events.id == order.event_id).first()

                        payment_data = {
                            "customer_name": f"{order.user.firstname} {order.user.surname}",
                            "order_id": order.id,
                            "amount": transaction.amount,
                            "currency": transaction.currency,
                            "payment_method": transaction.payment_method or "card",
                            "transaction_id": payment_intent_id,
                            "event_name": event.event_name if event else "Unknown Event"
                        }

                        email_service.send_payment_confirmation(
                            to_email=order.user.email,
                            payment_data=payment_data
                        )
                        logger.info(f"Sent payment confirmation email to {order.user.email}")
                    except Exception as email_error:
                        logger.error(f"Failed to send payment confirmation email: {str(email_error)}")

                # Generate QR codes and send ticket delivery emails
                if order and order.user:
                    try:
                        from models.tickets import Tickets, TicketTypes
                        import json
                        import base64

                        # Get all tickets for this order
                        tickets = db.query(Tickets).filter(
                            Tickets.order_id == order.id,
                            Tickets.deleted_at.is_(None)
                        ).all()

                        event = db.query(Events).filter(Events.id == order.event_id).first()

                        for ticket in tickets:
                            # Generate QR code data
                            ticket_type = db.query(TicketTypes).filter(
                                TicketTypes.id == ticket.ticket_type_id
                            ).first()

                            # Create QR code payload
                            qr_data = {
                                "ticket_id": ticket.id,
                                "order_id": order.id,
                                "event_id": order.event_id,
                                "user_id": order.user_id,
                                "ticket_type": ticket_type.name if ticket_type else "Unknown"
                            }

                            # Generate QR code
                            qr_code_base64 = qr_service.generate_qr_code_base64(
                                ticket_id=ticket.id,
                                order_id=order.id,
                                event_id=order.event_id,
                                user_id=order.user_id,
                                ticket_type=ticket_type.name if ticket_type else "Unknown"
                            )

                            # Update ticket with QR code data
                            ticket.qr_code = f"TICKET_{ticket.id}_{order.id}"
                            ticket.qr_code_data = json.dumps(qr_data)
                            db.commit()

                            # Send ticket delivery email with QR code
                            ticket_data = {
                                "ticket_id": ticket.id,
                                "customer_name": f"{order.user.firstname} {order.user.surname}",
                                "event_name": event.event_name if event else "Unknown Event",
                                "event_date": event.event_date.strftime("%B %d, %Y at %I:%M %p") if event else "TBD",
                                "event_location": event.location if event else "TBD",
                                "ticket_type": ticket_type.name if ticket_type else "Unknown",
                                "seat_number": ticket.seat_number,
                                "order_id": order.id
                            }

                            qr_attachment = {
                                'content': qr_code_base64,
                                'filename': f'ticket_{ticket.id}_qr.png',
                                'type': 'image/png'
                            }

                            email_service.send_ticket_delivery(
                                to_email=order.user.email,
                                ticket_data=ticket_data,
                                qr_code_attachment=qr_attachment
                            )

                            logger.info(f"Sent ticket delivery email for ticket {ticket.id} to {order.user.email}")

                    except Exception as ticket_error:
                        logger.error(f"Failed to generate QR codes or send ticket emails: {str(ticket_error)}")

        elif event_type == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            payment_intent_id = payment_intent["id"]
            error_message = payment_intent.get("last_payment_error", {}).get("message", "Payment failed")

            # Update payment transaction status
            transaction = db.query(PaymentTransaction).filter(
                PaymentTransaction.stripe_payment_intent_id == payment_intent_id
            ).first()

            if transaction:
                transaction.status = "failed"
                transaction.error_message = error_message

                # Update order payment status
                order = db.query(Orders).filter(Orders.id == transaction.order_id).first()
                if order:
                    order.payment_status = "failed"

                db.commit()
                logger.warning(f"Payment failed for {payment_intent_id}: {error_message}")

        elif event_type == "payment_intent.canceled":
            payment_intent = event["data"]["object"]
            payment_intent_id = payment_intent["id"]

            # Update payment transaction status
            transaction = db.query(PaymentTransaction).filter(
                PaymentTransaction.stripe_payment_intent_id == payment_intent_id
            ).first()

            if transaction:
                transaction.status = "canceled"

                # Update order payment status
                order = db.query(Orders).filter(Orders.id == transaction.order_id).first()
                if order:
                    order.payment_status = "canceled"

                db.commit()
                logger.info(f"Payment canceled for {payment_intent_id}")

        return {"status": "success"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )
