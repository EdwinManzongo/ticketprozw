"""
Email service implementation using SendGrid
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """Email service using SendGrid"""

    def __init__(self):
        """Initialize SendGrid client and Jinja2 environment"""
        if not settings.SENDGRID_API_KEY:
            logger.warning("SENDGRID_API_KEY not configured - emails will not be sent")
            self.client = None
        else:
            self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)

        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render email template with context

        Args:
            template_name: Name of the template file
            context: Template context variables

        Returns:
            Rendered HTML string
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email using SendGrid

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            from_email: Sender email (defaults to SENDGRID_FROM_EMAIL)
            attachments: List of attachment dicts with 'content', 'filename', 'type'

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.client:
            logger.warning(f"SendGrid not configured - skipping email to {to_email}")
            return False

        try:
            # Use default from_email if not provided
            from_email = from_email or settings.SENDGRID_FROM_EMAIL
            if not from_email:
                raise ValueError("SENDGRID_FROM_EMAIL not configured")

            # Create message
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            # Add attachments if provided
            if attachments:
                for attach in attachments:
                    attachment = Attachment(
                        FileContent(attach.get('content')),
                        FileName(attach.get('filename')),
                        FileType(attach.get('type', 'application/pdf')),
                        Disposition('attachment')
                    )
                    message.add_attachment(attachment)

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    def send_order_confirmation(
        self,
        to_email: str,
        order_data: Dict[str, Any]
    ) -> bool:
        """
        Send order confirmation email

        Args:
            to_email: Customer email address
            order_data: Dictionary containing order details:
                - order_id: Order ID
                - customer_name: Customer full name
                - event_name: Event name
                - event_date: Event date
                - event_location: Event location
                - tickets: List of ticket details
                - total_amount: Total order amount
                - order_date: Date order was placed

        Returns:
            True if email was sent successfully
        """
        try:
            # Render template
            html_content = self._render_template('order_confirmation.html', order_data)

            # Send email
            subject = f"Order Confirmation - {order_data.get('event_name')} (Order #{order_data.get('order_id')})"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Error sending order confirmation email: {str(e)}")
            return False

    def send_ticket_delivery(
        self,
        to_email: str,
        ticket_data: Dict[str, Any],
        qr_code_attachment: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send ticket delivery email with QR code

        Args:
            to_email: Customer email address
            ticket_data: Dictionary containing ticket details:
                - ticket_id: Ticket ID
                - customer_name: Customer full name
                - event_name: Event name
                - event_date: Event date and time
                - event_location: Event location
                - ticket_type: Ticket type/category
                - seat_number: Seat number (if applicable)
                - order_id: Order ID
            qr_code_attachment: Optional QR code attachment dict

        Returns:
            True if email was sent successfully
        """
        try:
            # Render template
            html_content = self._render_template('ticket_delivery.html', ticket_data)

            # Send email with QR code attachment
            subject = f"Your Ticket - {ticket_data.get('event_name')}"
            attachments = [qr_code_attachment] if qr_code_attachment else None

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                attachments=attachments
            )

        except Exception as e:
            logger.error(f"Error sending ticket delivery email: {str(e)}")
            return False

    def send_event_reminder(
        self,
        to_email: str,
        reminder_data: Dict[str, Any]
    ) -> bool:
        """
        Send event reminder email

        Args:
            to_email: Customer email address
            reminder_data: Dictionary containing:
                - customer_name: Customer full name
                - event_name: Event name
                - event_date: Event date and time
                - event_location: Event location
                - ticket_count: Number of tickets
                - order_id: Order ID

        Returns:
            True if email was sent successfully
        """
        try:
            # Render template
            html_content = self._render_template('event_reminder.html', reminder_data)

            # Send email
            subject = f"Reminder: {reminder_data.get('event_name')} - Coming Soon!"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Error sending event reminder email: {str(e)}")
            return False

    def send_payment_confirmation(
        self,
        to_email: str,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Send payment confirmation email

        Args:
            to_email: Customer email address
            payment_data: Dictionary containing:
                - customer_name: Customer full name
                - order_id: Order ID
                - amount: Payment amount
                - currency: Currency code
                - payment_method: Payment method used
                - transaction_id: Transaction ID
                - event_name: Event name

        Returns:
            True if email was sent successfully
        """
        try:
            # Render template
            html_content = self._render_template('payment_confirmation.html', payment_data)

            # Send email
            subject = f"Payment Confirmed - Order #{payment_data.get('order_id')}"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Error sending payment confirmation email: {str(e)}")
            return False


# Create a singleton instance
email_service = EmailService()
