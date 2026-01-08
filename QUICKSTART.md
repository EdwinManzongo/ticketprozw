# 🚀 TicketProZW - Quick Start Guide

## Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your configuration
nano .env
```

**Important**: Generate a secure SECRET_KEY:
```bash
openssl rand -hex 32
```

### 3. Start the Server
```bash
uvicorn main:app --reload
```

Server runs at: **http://localhost:8000**

### 4. Access API Documentation
Open in your browser: **http://localhost:8000/api/docs**

---

## Quick Test

### Register a New User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "John",
    "surname": "Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "phone_number": "+263771234567",
    "street_address": "123 Main Street, Harare",
    "active": true
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe@example.com&password=SecurePass123!"
```

### Get Your Profile
```bash
# Save the access_token from login response
TOKEN="your_access_token_here"

curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Security Features ✅

1. **Strong Password Policy** - 8+ chars, uppercase, lowercase, digit
2. **JWT Authentication** - Secure token-based auth
3. **Rate Limiting** - Prevents brute force attacks
4. **Input Validation** - All fields validated
5. **No Password Exposure** - Never returned in responses
6. **Role-Based Access** - admin, organizer, user roles
7. **Global Error Handling** - Standardized responses

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Users (Protected)
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### Events
- `GET /api/v1/events` - List all events (with pagination)
- `GET /api/v1/events/{id}` - Get event details
- `POST /api/v1/events` - Create event (organizer/admin only)
- `PUT /api/v1/events/{id}` - Update event (organizer/admin only)
- `DELETE /api/v1/events/{id}` - Delete event (admin only)

### Orders
- `GET /api/v1/orders` - List user's orders
- `GET /api/v1/orders/{id}` - Get order details
- `POST /api/v1/orders` - Create new order
- `PUT /api/v1/orders/{id}` - Update order
- `DELETE /api/v1/orders/{id}` - Cancel order

### Tickets
- `GET /api/v1/tickets` - List user's tickets
- `GET /api/v1/tickets/{id}` - Get ticket details
- `POST /api/v1/tickets` - Create ticket
- `PUT /api/v1/tickets/{id}` - Update ticket

### Payments
- `POST /api/v1/payments/create-payment-intent` - Create Stripe payment
- `GET /api/v1/payments/transactions/{id}` - Get transaction details
- `POST /api/v1/payments/{payment_intent_id}/refund` - Process refund
- `POST /api/v1/payments/webhooks/stripe` - Stripe webhook handler

### Validation (Staff)
- `POST /api/v1/validation/validate` - Validate ticket QR code
- `POST /api/v1/validation/check-in/{ticket_id}` - Check-in ticket
- `POST /api/v1/validation/check-out/{ticket_id}` - Check-out ticket

### Admin (Admin Only)
- `GET /api/v1/admin/dashboard` - Comprehensive analytics dashboard
- `GET /api/v1/admin/analytics/sales` - Sales analytics
- `GET /api/v1/admin/analytics/events` - All events analytics
- `GET /api/v1/admin/analytics/events/{id}` - Single event analytics
- `POST /api/v1/admin/tickets/transfer` - Transfer ticket to another user

---

## Testing

### Manual Tests
See `manual_security_tests.md` for detailed test commands.

### Automated Tests
```bash
python test_security.py
```

---

## Documentation

- **Security Improvements**: See `SECURITY_IMPROVEMENTS.md`
- **Manual Tests**: See `manual_security_tests.md`
- **Implementation Plan**: See `.claude/plans/fluffy-wandering-nest.md`

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is already in use
lsof -ti:8000 | xargs kill -9

# Start server again
uvicorn main:app --reload
```

### Database errors
Make sure PostgreSQL is running and DATABASE_URL in `.env` is correct.

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## What's Been Implemented

### ✅ Phase 1: Security Foundation (Complete)
- Environment configuration with Pydantic Settings
- JWT authentication with access/refresh tokens
- Password security (hashing, validation)
- Input validation with Pydantic
- Global error handling
- Rate limiting with slowapi
- Database optimization (removed unnecessary indexes)
- Role-based access control (admin, organizer, user)

### ✅ Phase 2: Core Infrastructure (Complete)
- Alembic migrations system with autogenerate
- SQLAlchemy bidirectional relationships
- Audit fields (created_at, updated_at, deleted_at)
- Complete CRUD for all resources
- Pagination with PaginatedResponse[T]
- Soft delete pattern
- Authorization checks

### ✅ Phase 3: Features (Complete)
- Stripe payment processing
- Payment intents and webhooks
- SendGrid email notifications
- QR code generation and validation
- Ticket check-in/check-out system
- Inventory management with row-level locking
- Automatic ticket delivery on payment success

### ✅ Phase 4: Admin & Advanced Features (Complete)
- **Admin Dashboard** - Comprehensive analytics with sales, revenue, and user stats
- **Analytics Endpoints** - Sales, events, and payment method breakdowns
- **Refund System** - Full and partial refunds via Stripe
- **Ticket Transfers** - Transfer tickets between users with email notifications
- **Event Analytics** - Per-event revenue, capacity, and ticket sales tracking
- **Top Events** - Revenue-based event performance rankings

### 🔄 Phase 5: Testing (Pending)
- Comprehensive unit tests
- Integration tests
- 80%+ test coverage
- CI/CD improvements
- Load testing

---

## Support

For issues or questions, check the documentation files or review the implementation plan.
