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

### Events, Orders, Tickets
*(Coming in Phase 2)*

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
- Environment configuration
- JWT authentication
- Password security
- Input validation
- Error handling
- Rate limiting
- Database optimization

### 🔄 Phase 2: Core Infrastructure (Pending)
- Alembic migrations
- SQLAlchemy relationships
- Audit fields
- Complete CRUD
- Pagination

### 🔄 Phase 3: Features (Pending)
- Payment processing
- Email notifications
- QR codes
- Event search
- Inventory management

### 🔄 Phase 4: Admin (Pending)
- Dashboard
- Analytics
- Refunds
- Transfers

### 🔄 Phase 5: Testing (Pending)
- Comprehensive tests
- 80%+ coverage
- CI/CD improvements

---

## Support

For issues or questions, check the documentation files or review the implementation plan.
