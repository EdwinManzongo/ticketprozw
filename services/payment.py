"""
Payment service abstraction

This module provides an abstract base class for payment processing.
Different payment providers (Stripe, PayPal, etc.) can implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentService(ABC):
    """Abstract base class for payment services"""

    @abstractmethod
    def create_payment_intent(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a payment intent

        Args:
            amount: Amount to charge (in smallest currency unit, e.g., cents)
            currency: Three-letter currency code (e.g., 'USD')
            metadata: Additional metadata to attach to the payment

        Returns:
            Dictionary containing payment intent details
        """
        pass

    @abstractmethod
    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent by ID

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing payment intent details
        """
        pass

    @abstractmethod
    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing updated payment intent details
        """
        pass

    @abstractmethod
    def cancel_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Cancel a payment intent

        Args:
            payment_intent_id: The payment intent ID

        Returns:
            Dictionary containing cancelled payment intent details
        """
        pass

    @abstractmethod
    def create_refund(
        self,
        payment_intent_id: str,
        amount: float = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment

        Args:
            payment_intent_id: The payment intent ID to refund
            amount: Amount to refund (None for full refund)

        Returns:
            Dictionary containing refund details
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature to ensure it came from the payment provider

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            secret: Webhook secret key

        Returns:
            True if signature is valid, False otherwise
        """
        pass
