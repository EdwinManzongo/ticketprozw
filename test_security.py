#!/usr/bin/env python3
"""Security testing script for TicketProZW API."""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_test(name, passed, details=""):
    """Print test result with formatting."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"    {details}")
    print()

def test_password_validation():
    """Test password strength requirements."""
    print("=" * 60)
    print("TEST 1: Password Validation")
    print("=" * 60)

    # Test weak password (too short)
    weak_password_data = {
        "firstname": "Test",
        "surname": "User",
        "email": "weak@test.com",
        "password": "short",  # Too short
        "phone_number": "1234567890",
        "street_address": "123 Test St",
        "active": True
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=weak_password_data)
    print_test(
        "Weak password rejected (too short)",
        response.status_code == 422,
        f"Expected 422, got {response.status_code}"
    )

    # Test password without uppercase
    no_upper_data = weak_password_data.copy()
    no_upper_data["email"] = "noupper@test.com"
    no_upper_data["password"] = "lowercase123"

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=no_upper_data)
    print_test(
        "Password without uppercase rejected",
        response.status_code == 422 and "uppercase" in response.text.lower(),
        f"Response: {response.status_code}"
    )

    # Test password without digit
    no_digit_data = weak_password_data.copy()
    no_digit_data["email"] = "nodigit@test.com"
    no_digit_data["password"] = "NoDigitsHere"

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=no_digit_data)
    print_test(
        "Password without digit rejected",
        response.status_code == 422 and "digit" in response.text.lower(),
        f"Response: {response.status_code}"
    )

    # Test common password
    common_pwd_data = weak_password_data.copy()
    common_pwd_data["email"] = "common@test.com"
    common_pwd_data["password"] = "Password123"

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=common_pwd_data)
    print_test(
        "Common password rejected",
        response.status_code == 422 and "common" in response.text.lower(),
        f"Response: {response.status_code}"
    )

def test_successful_registration():
    """Test successful user registration."""
    print("=" * 60)
    print("TEST 2: Successful Registration")
    print("=" * 60)

    # Create valid user
    valid_user = {
        "firstname": "Security",
        "surname": "Test",
        "email": f"security.test.{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "phone_number": "1234567890",
        "street_address": "123 Security St",
        "active": True
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=valid_user)
    print_test(
        "User registration successful",
        response.status_code == 201,
        f"Status: {response.status_code}"
    )

    if response.status_code == 201:
        data = response.json()
        has_access = "access_token" in data
        has_refresh = "refresh_token" in data
        has_type = data.get("token_type") == "bearer"

        print_test(
            "JWT tokens returned",
            has_access and has_refresh and has_type,
            f"Access token: {has_access}, Refresh token: {has_refresh}, Type: {has_type}"
        )

        return data["access_token"], valid_user["email"]

    return None, None

def test_login_and_user_enumeration(email):
    """Test login functionality and user enumeration prevention."""
    print("=" * 60)
    print("TEST 3: Login & User Enumeration Prevention")
    print("=" * 60)

    # Test login with wrong password
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": email, "password": "WrongPassword123!"}
    )
    wrong_pwd_msg = response.json().get("detail", "")

    # Test login with non-existent user
    response2 = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "nonexistent@test.com", "password": "WrongPassword123!"}
    )
    no_user_msg = response2.json().get("detail", "")

    print_test(
        "User enumeration prevented (same error message)",
        wrong_pwd_msg == no_user_msg and "Incorrect email or password" in wrong_pwd_msg,
        f"Both return: '{wrong_pwd_msg}'"
    )

    # Test successful login
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": email, "password": "SecurePass123!"}
    )

    print_test(
        "Successful login",
        response.status_code == 200,
        f"Status: {response.status_code}"
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_password_not_exposed(token):
    """Test that password is never exposed in API responses."""
    print("=" * 60)
    print("TEST 4: Password Exposure Prevention")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    # Test /me endpoint
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)

    if response.status_code == 200:
        data = response.json()
        has_password = "password" in data

        print_test(
            "Password NOT in /me response",
            not has_password,
            f"Response keys: {list(data.keys())}"
        )

def test_authentication_required():
    """Test that endpoints require authentication."""
    print("=" * 60)
    print("TEST 5: Authentication Required")
    print("=" * 60)

    # Try to access user endpoint without token
    response = requests.get(f"{BASE_URL}/api/v1/users/1")

    print_test(
        "Endpoint blocked without authentication",
        response.status_code == 401,
        f"Expected 401, got {response.status_code}"
    )

    # Try with invalid token
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = requests.get(f"{BASE_URL}/api/v1/users/1", headers=headers)

    print_test(
        "Invalid token rejected",
        response.status_code == 401,
        f"Expected 401, got {response.status_code}"
    )

def test_rate_limiting():
    """Test rate limiting on authentication endpoints."""
    print("=" * 60)
    print("TEST 6: Rate Limiting")
    print("=" * 60)

    print("Testing login rate limit (10 requests/minute)...")

    # Make 11 rapid login attempts
    responses = []
    for i in range(11):
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "ratelimit@test.com", "password": "Test123!"}
        )
        responses.append(response.status_code)

    rate_limited = 429 in responses

    print_test(
        "Rate limiting active",
        rate_limited,
        f"Got 429 (rate limited) after rapid requests: {rate_limited}"
    )

def test_input_validation():
    """Test input validation on various fields."""
    print("=" * 60)
    print("TEST 7: Input Validation")
    print("=" * 60)

    # Test invalid email
    invalid_email = {
        "firstname": "Test",
        "surname": "User",
        "email": "not-an-email",
        "password": "ValidPass123!",
        "phone_number": "1234567890",
        "street_address": "123 Test St"
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=invalid_email)
    print_test(
        "Invalid email rejected",
        response.status_code == 422,
        f"Status: {response.status_code}"
    )

    # Test short phone number
    short_phone = invalid_email.copy()
    short_phone["email"] = "valid@test.com"
    short_phone["phone_number"] = "123"

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=short_phone)
    print_test(
        "Invalid phone number rejected",
        response.status_code == 422,
        f"Status: {response.status_code}"
    )

def test_error_handling():
    """Test global error handling."""
    print("=" * 60)
    print("TEST 8: Error Handling")
    print("=" * 60)

    # Test 404 for non-existent resource
    response = requests.get(f"{BASE_URL}/api/v1/events/99999")

    if response.status_code in [401, 403]:
        print_test(
            "Authentication required (expected)",
            True,
            "Endpoint is protected - this is correct"
        )
    else:
        has_error_field = "error" in response.json() or "detail" in response.json()

        print_test(
            "Standardized error response",
            has_error_field,
            f"Response: {response.json()}"
        )

def main():
    """Run all security tests."""
    print("\n")
    print("🔒" * 30)
    print("TICKETPROZW - SECURITY TEST SUITE")
    print("🔒" * 30)
    print("\n")

    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        print("✅ Server is running\n")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Server is not running!")
        print("Please start the server with: uvicorn main:app --reload")
        return

    # Run tests
    test_password_validation()
    token, email = test_successful_registration()

    if token and email:
        login_token = test_login_and_user_enumeration(email)
        if login_token:
            test_password_not_exposed(login_token)

    test_authentication_required()
    test_rate_limiting()
    test_input_validation()
    test_error_handling()

    print("=" * 60)
    print("✅ SECURITY TEST SUITE COMPLETE")
    print("=" * 60)
    print("\nAll critical security features have been tested.")
    print("Review the results above to ensure all tests passed.")

if __name__ == "__main__":
    main()
