"""
Stripe payment service implementation
"""
import stripe
import logging
from typing import Dict, Any, Optional
from core.config import settings
from services.payment import PaymentService


logger = logging.getLogger(__name__)


class StripePaymentService(PaymentService):
    """Stripe implementation of PaymentService"""

    def __init__(self):
        """Initialize Stripe with API key"""
        if not settings.STRIPE_SECRET_KEY:
            logger.warning("STRIPE_SECRET_KEY not configured")
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(
        self,
        amount: float,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent

        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Three-letter currency code
            metadata: Additional metadata

        Returns:
            Dictionary with client_secret, payment_intent_id, etc.
        """
        try:
            # Convert dollars to cents
            amount_cents = int(amount * 100)

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )

            logger.info(f"Created payment intent: {payment_intent.id}")

            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")

    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent from Stripe

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing payment intent details
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": payment_intent.id,
                "amount": payment_intent.amount / 100,  # Convert cents to dollars
                "currency": payment_intent.currency.upper(),
                "status": payment_intent.status,
                "payment_method": payment_intent.payment_method,
                "customer": payment_intent.customer,
                "metadata": payment_intent.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment intent: {str(e)}")
            raise Exception(f"Payment retrieval error: {str(e)}")

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing updated payment intent details
        """
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency.upper()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            raise Exception(f"Payment confirmation error: {str(e)}")

    def cancel_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Cancel a payment intent

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing cancelled payment intent details
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)

            logger.info(f"Cancelled payment intent: {payment_intent.id}")

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency.upper()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling payment: {str(e)}")
            raise Exception(f"Payment cancellation error: {str(e)}")

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment

        Args:
            payment_intent_id: The payment intent ID to refund
            amount: Amount to refund in dollars (None for full refund)

        Returns:
            Dictionary containing refund details
        """
        try:
            refund_data = {"payment_intent": payment_intent_id}

            if amount is not None:
                # Convert dollars to cents
                refund_data["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Created refund: {refund.id} for payment intent: {payment_intent_id}")

            return {
                "id": refund.id,
                "payment_intent_id": payment_intent_id,
                "amount": refund.amount / 100,
                "currency": refund.currency.upper(),
                "status": refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {str(e)}")
            raise Exception(f"Refund error: {str(e)}")

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify Stripe webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature from Stripe-Signature header
            secret: Webhook signing secret

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            stripe.Webhook.construct_event(
                payload, signature, secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False


# Create a singleton instance
stripe_service = StripePaymentService()
