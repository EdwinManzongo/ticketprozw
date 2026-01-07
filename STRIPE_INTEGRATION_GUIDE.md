# Stripe Payment Integration Guide

## Overview

Phase 3A has been successfully completed! The TicketProZW platform now has full Stripe payment processing capabilities with secure payment intents, webhook handling, and refund support.

## What Was Implemented

### 1. Database Model (`models/payments.py`)

Created the `PaymentTransaction` model to track all payment transactions:

**Fields:**
- `id` - Primary key
- `order_id` - Foreign key to orders table
- `stripe_payment_intent_id` - Unique Stripe payment intent ID
- `amount` - Payment amount (in dollars)
- `currency` - Three-letter currency code (default: USD)
- `status` - Payment status (e.g., "requires_payment_method", "succeeded", "failed")
- `payment_method` - Payment method used (populated by webhook)
- `stripe_customer_id` - Stripe customer ID (if applicable)
- `stripe_charge_id` - Stripe charge ID (populated by webhook)
- `error_message` - Error message if payment failed
- `created_at`, `updated_at`, `deleted_at` - Audit timestamps

**Relationship:**
- One-to-one relationship with `Orders` model

---

### 2. Schemas (`schemas/payments.py`)

Created Pydantic schemas for request/response validation:

**`PaymentIntentCreate`** - Request schema for creating payment intents
```python
{
    "order_id": 1,
    "amount": 99.99,
    "currency": "USD"
}
```

**`PaymentIntentResponse`** - Response after creating payment intent
```python
{
    "client_secret": "pi_xxx_secret_xxx",
    "payment_intent_id": "pi_xxx",
    "amount": 99.99,
    "currency": "USD",
    "status": "requires_payment_method"
}
```

**`PaymentTransactionResponse`** - Payment transaction details
```python
{
    "id": 1,
    "order_id": 1,
    "stripe_payment_intent_id": "pi_xxx",
    "amount": 99.99,
    "currency": "USD",
    "status": "succeeded",
    "payment_method": "card",
    "error_message": null,
    "created_at": "2026-01-08T01:00:00Z",
    "updated_at": "2026-01-08T01:05:00Z"
}
```

---

### 3. Service Layer

#### Abstract Base Class (`services/payment.py`)

Created `PaymentService` abstract base class to support multiple payment providers in the future:

**Methods:**
- `create_payment_intent()` - Create a payment intent
- `retrieve_payment_intent()` - Get payment intent details
- `confirm_payment()` - Confirm a payment intent
- `cancel_payment()` - Cancel a payment intent
- `create_refund()` - Create a refund
- `verify_webhook_signature()` - Verify webhook signatures

#### Stripe Implementation (`services/stripe_service.py`)

Implemented `StripePaymentService` with full Stripe API integration:

**Features:**
- Automatic dollar-to-cent conversion
- Metadata support for order tracking
- Automatic payment methods enabled
- Comprehensive error handling
- Webhook signature verification
- Singleton pattern for easy access

**Usage:**
```python
from services.stripe_service import stripe_service

# Create payment intent
result = stripe_service.create_payment_intent(
    amount=99.99,
    currency="USD",
    metadata={"order_id": "123", "user_id": "456"}
)

# Create refund
refund = stripe_service.create_refund(
    payment_intent_id="pi_xxx",
    amount=50.00  # Partial refund
)
```

---

### 4. API Endpoints (`routers/payments.py`)

Created payment processing endpoints with full authorization and error handling:

#### **POST /api/v1/payments/create-payment-intent**

Create a Stripe payment intent for an order.

**Authorization:** User must own the order or be an admin

**Request:**
```json
{
    "order_id": 1,
    "amount": 99.99,
    "currency": "USD"
}
```

**Response:** (201 Created)
```json
{
    "client_secret": "pi_xxx_secret_xxx",
    "payment_intent_id": "pi_xxx",
    "amount": 99.99,
    "currency": "USD",
    "status": "requires_payment_method"
}
```

**Features:**
- Verifies order ownership
- Prevents duplicate payments for completed orders
- Creates/updates payment transaction record
- Includes metadata for tracking

---

#### **GET /api/v1/payments/transactions/{transaction_id}**

Get payment transaction details.

**Authorization:** User must own the order or be an admin

**Response:** (200 OK)
```json
{
    "id": 1,
    "order_id": 1,
    "stripe_payment_intent_id": "pi_xxx",
    "amount": 99.99,
    "currency": "USD",
    "status": "succeeded",
    "payment_method": "card",
    "error_message": null,
    "created_at": "2026-01-08T01:00:00Z",
    "updated_at": "2026-01-08T01:05:00Z"
}
```

---

#### **POST /api/v1/payments/{payment_intent_id}/refund**

Create a refund for a payment.

**Authorization:** Admin or order owner

**Query Parameters:**
- `amount` (optional) - Amount to refund (defaults to full refund)

**Response:** (200 OK)
```json
{
    "message": "Refund processed successfully. Refund ID: re_xxx"
}
```

**Features:**
- Supports partial refunds
- Updates payment transaction status to "refunded"
- Updates order payment status to "refunded"
- Full audit trail

---

#### **POST /api/v1/payments/webhooks/stripe**

Handle Stripe webhook events.

**Authorization:** Webhook signature verification

**Supported Events:**
- `payment_intent.succeeded` - Payment completed successfully
- `payment_intent.payment_failed` - Payment failed
- `payment_intent.canceled` - Payment canceled

**Features:**
- Automatic signature verification
- Updates payment transaction status
- Updates order payment status
- Populates payment method and Stripe IDs
- Comprehensive logging

**Webhook Event Flow:**

1. **Payment Succeeds:**
   - Updates transaction status to "succeeded"
   - Updates order status to "completed"
   - Populates payment_method, stripe_customer_id, stripe_charge_id

2. **Payment Fails:**
   - Updates transaction status to "failed"
   - Updates order status to "failed"
   - Stores error message

3. **Payment Canceled:**
   - Updates transaction status to "canceled"
   - Updates order status to "canceled"

---

### 5. Database Migration

**Migration:** `9ca2ef198515_add_payment_transactions_table.py`

**Changes:**
- Created `payment_transactions` table
- Added foreign key to `orders` table
- Created indexes on:
  - `id` (primary key)
  - `order_id` (foreign key)
  - `status` (for filtering)
  - `stripe_payment_intent_id` (unique, for lookups)
- Added audit timestamps (created_at, updated_at, deleted_at)

**Applied:** ✅ Yes (alembic upgrade head)

---

### 6. Configuration Updates

**Updated Files:**
- `.env.example` - Added Stripe configuration placeholders
- `core/config.py` - Already had Stripe settings (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET)
- `main.py` - Registered payments router
- `alembic/env.py` - Added PaymentTransaction model import

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install stripe==8.1.0
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

**Get your Stripe keys:**
1. Sign up at https://stripe.com
2. Go to Dashboard → Developers → API keys
3. Copy your test mode secret key (starts with `sk_test_`)
4. For webhook secret, create a webhook endpoint (see below)

### 3. Set Up Stripe Webhook

**Option A: Local Development (using Stripe CLI)**

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to http://localhost:8000/api/v1/payments/webhooks/stripe

# Copy the webhook signing secret (starts with whsec_) to your .env file
```

**Option B: Production (Stripe Dashboard)**

1. Go to Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Enter your webhook URL: `https://yourdomain.com/api/v1/payments/webhooks/stripe`
4. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
5. Copy the webhook signing secret to your `.env` file

### 4. Run Database Migration

```bash
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn main:app --reload
```

---

## Usage Examples

### Example 1: Create Payment Intent

```python
import requests

# 1. Create an order first (not shown)
order_id = 1

# 2. Create payment intent
response = requests.post(
    "http://localhost:8000/api/v1/payments/create-payment-intent",
    json={
        "order_id": order_id,
        "amount": 99.99,
        "currency": "USD"
    },
    headers={
        "Authorization": f"Bearer {access_token}"
    }
)

payment_intent = response.json()
client_secret = payment_intent["client_secret"]

# 3. Use client_secret in your frontend to complete payment
# (using Stripe.js or Stripe Elements)
```

### Example 2: Frontend Payment Form (React + Stripe.js)

```javascript
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement } from '@stripe/react-stripe-js';

const stripePromise = loadStripe('pk_test_your_publishable_key');

function CheckoutForm({ clientSecret }) {
  const stripe = await stripePromise;

  const { error } = await stripe.confirmPayment({
    clientSecret,
    confirmParams: {
      return_url: 'https://yourdomain.com/order-confirmation',
    },
  });

  if (error) {
    console.error(error.message);
  }
}
```

### Example 3: Process Refund

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/payments/pi_xxx/refund",
    params={"amount": 50.00},  # Partial refund
    headers={
        "Authorization": f"Bearer {admin_token}"
    }
)

print(response.json()["message"])
# Output: "Refund processed successfully. Refund ID: re_xxx"
```

---

## Security Features

1. **Webhook Signature Verification**
   - All webhook requests are verified using Stripe signature
   - Invalid signatures are rejected with 400 Bad Request

2. **Authorization Checks**
   - Users can only create payments for their own orders
   - Only admins or order owners can request refunds
   - Only admins or order owners can view transaction details

3. **Idempotency**
   - Prevents duplicate payments for already-completed orders
   - Safe to retry failed payment intent creations

4. **Error Handling**
   - All Stripe API errors are caught and logged
   - User-friendly error messages returned
   - Database rollback on failures

---

## Testing

### Test with Stripe Test Cards

Use these test card numbers in your Stripe test environment:

**Success:**
- `4242 4242 4242 4242` - Visa (succeeds)

**Failures:**
- `4000 0000 0000 0002` - Card declined
- `4000 0000 0000 9995` - Insufficient funds

**Any future expiry date, any 3-digit CVC**

### Test Webhook Events

Using Stripe CLI:

```bash
# Trigger a successful payment event
stripe trigger payment_intent.succeeded

# Trigger a failed payment event
stripe trigger payment_intent.payment_failed
```

---

## Files Created/Modified

### Created:
- ✅ `models/payments.py` - PaymentTransaction model
- ✅ `schemas/payments.py` - Payment schemas
- ✅ `services/payment.py` - Abstract payment service
- ✅ `services/stripe_service.py` - Stripe implementation
- ✅ `routers/payments.py` - Payment endpoints
- ✅ `alembic/versions/9ca2ef198515_add_payment_transactions_table.py` - Migration
- ✅ `STRIPE_INTEGRATION_GUIDE.md` - This document

### Modified:
- ✅ `models/orders.py` - Added payment_transaction relationship
- ✅ `main.py` - Registered payments router
- ✅ `alembic/env.py` - Added PaymentTransaction import
- ✅ `.env.example` - Added Stripe configuration
- ✅ `requirements.txt` - Added stripe==8.1.0

---

## API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## Next Steps (Phase 3B-3E)

Phase 3A is complete! Remaining Phase 3 tasks:

- **3B:** SendGrid email notifications (order confirmation, ticket delivery)
- **3C:** QR code generation and ticket validation
- **3D:** Enhanced event search and filtering
- **3E:** Inventory management with concurrency control

---

## Support

For Stripe-related questions:
- Stripe Documentation: https://stripe.com/docs
- Stripe API Reference: https://stripe.com/docs/api

For implementation questions:
- Check the code comments in the implementation files
- Review the comprehensive examples in this guide
