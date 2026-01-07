"""
QR Code generation service for tickets
"""
import qrcode
import logging
import base64
import json
from io import BytesIO
from typing import Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class QRCodeService:
    """Service for generating and handling QR codes for tickets"""

    def __init__(self):
        """Initialize QR code service"""
        self.version = 1
        self.box_size = 10
        self.border = 4

    def generate_ticket_qr_code(
        self,
        ticket_id: int,
        order_id: int,
        event_id: int,
        user_id: int,
        ticket_type: str
    ) -> bytes:
        """
        Generate QR code for a ticket

        Args:
            ticket_id: Ticket ID
            order_id: Order ID
            event_id: Event ID
            user_id: User ID who owns the ticket
            ticket_type: Type/category of ticket

        Returns:
            QR code image as bytes (PNG format)
        """
        try:
            # Create QR code data payload
            qr_data = {
                "ticket_id": ticket_id,
                "order_id": order_id,
                "event_id": event_id,
                "user_id": user_id,
                "ticket_type": ticket_type,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            }

            # Convert to JSON string
            qr_payload = json.dumps(qr_data)

            # Generate QR code
            qr = qrcode.QRCode(
                version=self.version,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
                box_size=self.box_size,
                border=self.border,
            )
            qr.add_data(qr_payload)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_bytes = buffer.getvalue()

            logger.info(f"Generated QR code for ticket {ticket_id}")
            return qr_bytes

        except Exception as e:
            logger.error(f"Error generating QR code for ticket {ticket_id}: {str(e)}")
            raise Exception(f"Failed to generate QR code: {str(e)}")

    def generate_qr_code_base64(
        self,
        ticket_id: int,
        order_id: int,
        event_id: int,
        user_id: int,
        ticket_type: str
    ) -> str:
        """
        Generate QR code and return as base64 string

        Args:
            ticket_id: Ticket ID
            order_id: Order ID
            event_id: Event ID
            user_id: User ID
            ticket_type: Ticket type

        Returns:
            Base64 encoded QR code image
        """
        try:
            qr_bytes = self.generate_ticket_qr_code(
                ticket_id=ticket_id,
                order_id=order_id,
                event_id=event_id,
                user_id=user_id,
                ticket_type=ticket_type
            )

            # Encode to base64
            qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
            return qr_base64

        except Exception as e:
            logger.error(f"Error generating base64 QR code: {str(e)}")
            raise

    def decode_ticket_qr_code(self, qr_data_string: str) -> Dict[str, Any]:
        """
        Decode QR code data string

        Args:
            qr_data_string: JSON string from QR code

        Returns:
            Dictionary with ticket information
        """
        try:
            qr_data = json.loads(qr_data_string)

            # Validate required fields
            required_fields = ["ticket_id", "order_id", "event_id", "user_id"]
            for field in required_fields:
                if field not in qr_data:
                    raise ValueError(f"Missing required field: {field}")

            return qr_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid QR code data format: {str(e)}")
            raise ValueError("Invalid QR code format")
        except Exception as e:
            logger.error(f"Error decoding QR code: {str(e)}")
            raise

    def validate_qr_code_data(
        self,
        qr_data: Dict[str, Any],
        expected_event_id: int
    ) -> bool:
        """
        Validate QR code data against expected values

        Args:
            qr_data: Decoded QR code data
            expected_event_id: Expected event ID

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if event matches
            if qr_data.get("event_id") != expected_event_id:
                logger.warning(f"Event ID mismatch: {qr_data.get('event_id')} != {expected_event_id}")
                return False

            # Check if QR code version is supported
            version = qr_data.get("version", "1.0")
            if version not in ["1.0"]:
                logger.warning(f"Unsupported QR code version: {version}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating QR code data: {str(e)}")
            return False


# Create a singleton instance
qr_service = QRCodeService()
