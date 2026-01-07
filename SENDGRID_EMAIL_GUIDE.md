# SendGrid Email Integration Guide

## Overview

Phase 3B is complete! The TicketProZW platform now has comprehensive email notification capabilities using SendGrid, with beautiful HTML templates for all customer communications.

## What Was Implemented

### 1. Email Service (`services/email_service.py`)

Created a complete email service with SendGrid integration:

**Features:**
- SendGrid API client initialization
- Jinja2 template rendering
- Attachment support (for QR codes, receipts, etc.)
- Comprehensive error handling and logging
- Singleton pattern for easy access

**Core Methods:**

#### `send_email()`
Low-level method for sending emails with full customization:
```python
email_service.send_email(
    to_email="customer@example.com",
    subject="Your Subject",
    html_content="<h1>HTML Content</h1>",
    from_email="custom@sender.com",  # Optional
    attachments=[{  # Optional
        'content': base64_encoded_content,
        'filename': 'ticket.pdf',
        'type': 'application/pdf'
    }]
)
```

#### `send_order_confirmation()`
Send order confirmation email after order is placed:
```python
email_service.send_order_confirmation(
    to_email=customer_email,
    order_data={
        "order_id": 123,
        "customer_name": "John Doe",
        "event_name": "Summer Music Festival",
        "event_date": "2026-07-15 18:00",
        "event_location": "Harare Gardens",
        "tickets": [
            {"type": "VIP", "quantity": 2, "price": 50.00},
            {"type": "General", "quantity": 3, "price": 25.00}
        ],
        "total_amount": 175.00,
        "order_date": "2026-01-08 10:30"
    }
)
```

#### `send_ticket_delivery()`
Send e-ticket with QR code attachment:
```python
email_service.send_ticket_delivery(
    to_email=customer_email,
    ticket_data={
        "ticket_id": 456,
        "customer_name": "John Doe",
        "event_name": "Summer Music Festival",
        "event_date": "2026-07-15 18:00",
        "event_location": "Harare Gardens",
        "ticket_type": "VIP",
        "seat_number": "A12",  # Optional
        "order_id": 123
    },
    qr_code_attachment={
        'content': qr_code_base64,
        'filename': 'ticket_qr.png',
        'type': 'image/png'
    }
)
```

#### `send_event_reminder()`
Send event reminder 24-48 hours before event:
```python
email_service.send_event_reminder(
    to_email=customer_email,
    reminder_data={
        "customer_name": "John Doe",
        "event_name": "Summer Music Festival",
        "event_date": "2026-07-15 18:00",
        "event_location": "Harare Gardens",
        "ticket_count": 5,
        "order_id": 123
    }
)
```

#### `send_payment_confirmation()`
Send payment confirmation after successful payment:
```python
email_service.send_payment_confirmation(
    to_email=customer_email,
    payment_data={
        "customer_name": "John Doe",
        "order_id": 123,
        "amount": 175.00,
        "currency": "USD",
        "payment_method": "card",
        "transaction_id": "pi_xxx",
        "event_name": "Summer Music Festival"
    }
)
```

---

### 2. Email Templates

Created professional, responsive HTML email templates using Jinja2:

#### **Base Template** (`templates/emails/base.html`)
- Responsive design (mobile-friendly)
- Consistent branding with TicketProZW colors
- Professional header and footer
- Clean, modern styling

**Design Features:**
- Gradient header (purple theme)
- Info boxes with clean borders
- Responsive layout (adapts to mobile)
- Professional typography
- Highlight colors for important information

#### **Order Confirmation** (`templates/emails/order_confirmation.html`)
Sent immediately after order is created.

**Includes:**
- Order number and date
- Event details (name, date, location)
- Ticket breakdown with quantities and prices
- Total amount
- What happens next instructions

#### **Ticket Delivery** (`templates/emails/ticket_delivery.html`)
Sent after payment confirmation with e-ticket and QR code.

**Includes:**
- Ticket ID and order number
- Ticket type and seat (if applicable)
- Event details
- QR code attachment
- Entry instructions
- Event day tips
- Security warning about not sharing QR code

#### **Event Reminder** (`templates/emails/event_reminder.html`)
Sent 24-48 hours before event.

**Includes:**
- Event details
- Booking information
- Preparation checklist
- What to bring
- Venue information
- Cancellation/transfer information

#### **Payment Confirmation** (`templates/emails/payment_confirmation.html`)
Sent immediately after successful payment.

**Includes:**
- Transaction ID and payment method
- Amount paid
- Event information
- What happens next
- Receipt information

---

### 3. Webhook Integration

Integrated email notifications into Stripe payment webhook (`routers/payments.py`):

**When Payment Succeeds:**
1. Update payment transaction status
2. Update order status to "completed"
3. Fetch order and event details
4. **Send payment confirmation email**
5. Log email delivery

**Error Handling:**
- Email failures are logged but don't block payment processing
- Graceful degradation if SendGrid is not configured

---

### 4. Configuration Updates

**Environment Variables** (`.env.example`):
```bash
# SendGrid Email Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@ticketpro.zw
```

**Config Class** (`core/config.py`):
- Already had `SENDGRID_API_KEY` (optional)
- Already had `SENDGRID_FROM_EMAIL` (optional)

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install sendgrid==6.11.0 jinja2==3.1.3
```

### 2. Create SendGrid Account

1. Sign up at https://sendgrid.com
2. Verify your email and account
3. Complete sender authentication (verify your domain or single sender)

### 3. Create API Key

1. Go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Name it (e.g., "TicketProZW Production")
4. Select **Full Access** or at minimum **Mail Send** permissions
5. Click **Create & View**
6. **Copy the API key immediately** (you can't view it again)

### 4. Verify Sender Email

**Option A: Single Sender Verification** (Easier for development)
1. Go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in your details (use noreply@ticketpro.zw or your domain)
4. Verify the email sent to that address

**Option B: Domain Authentication** (Recommended for production)
1. Go to **Settings** → **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Follow the DNS configuration steps
4. Wait for DNS propagation (can take 24-48 hours)

### 5. Configure Environment

Add to your `.env` file:

```bash
SENDGRID_API_KEY=SG.your_actual_api_key_here
SENDGRID_FROM_EMAIL=noreply@ticketpro.zw
```

**Important:**
- Use the verified email address from Step 4
- Never commit your API key to version control

### 6. Test Email Service

Create a test script or use the Python shell:

```python
from services.email_service import email_service

# Test basic email
result = email_service.send_email(
    to_email="your-test-email@example.com",
    subject="Test Email from TicketProZW",
    html_content="<h1>Hello!</h1><p>This is a test email.</p>"
)

print(f"Email sent: {result}")
```

---

## Usage Examples

### Example 1: Send Order Confirmation

```python
from services.email_service import email_service
from datetime import datetime

order_data = {
    "order_id": 123,
    "customer_name": "Sarah Johnson",
    "event_name": "Zimbabwe Music Awards 2026",
    "event_date": "December 15, 2026 at 7:00 PM",
    "event_location": "Harare International Convention Centre",
    "tickets": [
        {"type": "VIP", "quantity": 2, "price": 75.00},
        {"type": "Standard", "quantity": 4, "price": 35.00}
    ],
    "total_amount": 290.00,
    "order_date": "January 8, 2026 at 2:30 PM"
}

email_service.send_order_confirmation(
    to_email="sarah@example.com",
    order_data=order_data
)
```

### Example 2: Send Ticket with QR Code

```python
import base64
from services.email_service import email_service

# Generate QR code (from Phase 3C)
qr_code_bytes = generate_qr_code(ticket_id)  # Your QR generation function
qr_code_base64 = base64.b64encode(qr_code_bytes).decode('utf-8')

ticket_data = {
    "ticket_id": 456,
    "customer_name": "Sarah Johnson",
    "event_name": "Zimbabwe Music Awards 2026",
    "event_date": "December 15, 2026 at 7:00 PM",
    "event_location": "Harare International Convention Centre",
    "ticket_type": "VIP",
    "seat_number": "Row A, Seat 12",
    "order_id": 123
}

qr_attachment = {
    'content': qr_code_base64,
    'filename': 'ticket_456_qr.png',
    'type': 'image/png'
}

email_service.send_ticket_delivery(
    to_email="sarah@example.com",
    ticket_data=ticket_data,
    qr_code_attachment=qr_attachment
)
```

### Example 3: Automated Event Reminders

```python
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.orders import Orders
from models.events import Events

def send_event_reminders(db: Session):
    """Send reminders for events happening in 24 hours"""
    tomorrow = datetime.now() + timedelta(days=1)

    # Find events happening tomorrow
    upcoming_events = db.query(Events).filter(
        Events.event_date >= tomorrow,
        Events.event_date < tomorrow + timedelta(days=1)
    ).all()

    for event in upcoming_events:
        # Get all orders for this event
        orders = db.query(Orders).filter(
            Orders.event_id == event.id,
            Orders.payment_status == "completed"
        ).all()

        for order in orders:
            reminder_data = {
                "customer_name": f"{order.user.firstname} {order.user.surname}",
                "event_name": event.event_name,
                "event_date": event.event_date.strftime("%B %d, %Y at %I:%M %p"),
                "event_location": event.location,
                "ticket_count": len(order.tickets),
                "order_id": order.id
            }

            email_service.send_event_reminder(
                to_email=order.user.email,
                reminder_data=reminder_data
            )

# Schedule this to run daily with a cron job or task scheduler
```

---

## Template Customization

All email templates support Jinja2 syntax for dynamic content.

### Adding Custom Variables

Edit the templates in `templates/emails/`:

```html
{% extends "base.html" %}

{% block content %}
<h2>Hello {{ customer_name }}!</h2>

<p>Your custom message here with {{ dynamic_variable }}.</p>

{% if some_condition %}
    <p>This shows conditionally</p>
{% endif %}

{% for item in items %}
    <div>{{ item.name }}: ${{ item.price }}</div>
{% endfor %}
{% endblock %}
```

### Styling Guide

The base template includes these CSS classes:
- `.highlight` - Purple highlight color
- `.info-box` - Styled information container
- `.info-row` - Key-value pair row
- `.button` - Call-to-action button
- `.total` - Large, bold total amount

---

## Best Practices

### 1. Email Deliverability

**Do:**
- Use verified sender emails
- Authenticate your domain (SPF, DKIM, DMARC)
- Keep email content relevant and valuable
- Include unsubscribe links (for marketing emails)
- Monitor bounce rates and spam complaints

**Don't:**
- Use free email providers (gmail.com, yahoo.com) as sender
- Send from unverified emails
- Include too many links or images
- Use spam trigger words excessively

### 2. Testing

**Always test emails before production:**

```python
# In development, use your own email
if settings.ENVIRONMENT == "development":
    to_email = "developer@yourdomain.com"

result = email_service.send_order_confirmation(to_email, order_data)
assert result == True, "Email failed to send"
```

**Test on multiple email clients:**
- Gmail (web and mobile)
- Outlook
- Apple Mail
- Mobile devices (iOS, Android)

### 3. Error Handling

Email failures should **never** block critical operations:

```python
try:
    email_service.send_payment_confirmation(email, data)
except Exception as e:
    logger.error(f"Email failed but payment succeeded: {e}")
    # Payment is still successful, just log the error
```

### 4. Performance

For bulk emails (event reminders, newsletters):
- Use background tasks (Celery)
- Batch process emails
- Implement rate limiting
- Consider SendGrid's batch sending API

---

## Monitoring & Debugging

### SendGrid Dashboard

Monitor email activity at https://app.sendgrid.com:
- **Activity Feed** - See all sent emails in real-time
- **Statistics** - Track deliveries, opens, clicks, bounces
- **Suppressions** - Manage bounces and unsubscribes

### Application Logs

All email operations are logged:

```python
# Success
logger.info(f"Email sent successfully to {to_email}: {subject}")

# Failure
logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
logger.error(f"Error sending email: {str(e)}")
```

### Common Issues

**"SendGrid not configured"**
- Check `SENDGRID_API_KEY` in `.env`
- Verify API key is valid
- Ensure `.env` file is loaded

**"Invalid sender email"**
- Verify sender email in SendGrid dashboard
- Use exact email from verification

**"Mail Send permissions required"**
- Recreate API key with proper permissions

---

## Files Created/Modified

### Created:
- ✅ `services/email_service.py` - Email service with SendGrid
- ✅ `templates/emails/base.html` - Base email template
- ✅ `templates/emails/order_confirmation.html` - Order confirmation template
- ✅ `templates/emails/ticket_delivery.html` - Ticket delivery template
- ✅ `templates/emails/event_reminder.html` - Event reminder template
- ✅ `templates/emails/payment_confirmation.html` - Payment confirmation template
- ✅ `SENDGRID_EMAIL_GUIDE.md` - This document

### Modified:
- ✅ `requirements.txt` - Added sendgrid==6.11.0, jinja2==3.1.3
- ✅ `.env.example` - Added SendGrid configuration
- ✅ `routers/payments.py` - Integrated email in webhook

---

## Cost Considerations

**SendGrid Free Tier:**
- 100 emails/day forever free
- Suitable for development and small-scale testing

**SendGrid Essentials ($19.95/month):**
- 50,000 emails/month
- Email support
- Recommended for production

**SendGrid Pro ($89.95/month):**
- 100,000 emails/month
- Dedicated IP
- Advanced features

**Recommendation:** Start with free tier for development, upgrade to Essentials for production.

---

## Next Steps (Phase 3C-3E)

Phase 3B is complete! Remaining Phase 3 tasks:

- **3C:** QR code generation and ticket validation (IN PROGRESS)
- **3D:** Enhanced event search and filtering
- **3E:** Inventory management with concurrency control

---

## Support

**SendGrid Documentation:**
- API Reference: https://docs.sendgrid.com/api-reference
- Email Design Guide: https://docs.sendgrid.com/ui/sending-email/editor
- Troubleshooting: https://docs.sendgrid.com/ui/account-and-settings/troubleshooting

**Implementation Questions:**
- Review code comments in `services/email_service.py`
- Check template examples in `templates/emails/`
- Consult this comprehensive guide
