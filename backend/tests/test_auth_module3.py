"""
Module 3 Automated Test Suite: Authentication, Security & User Management.
Operates on an isolated test database to protect the live 54 production records.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from backend.app.models.user import User


# ==============================================================================
# 1. Password Hashing & Security Tests (Argon2 via pwdlib)
# ==============================================================================

def test_password_hashing_uses_argon2():
    """Verify that password hashing uses Argon2 and generates valid hashes."""
    raw_pwd = "SecureP@ssword2026!"
    hashed = get_password_hash(raw_pwd)

    # Argon2 hashes always begin with $argon2
    assert hashed.startswith("$argon2"), f"Expected Argon2 hash prefix, got: {hashed[:15]}"
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_password_hash_never_stores_plaintext():
    """Verify that plaintext passwords are never stored."""
    raw_pwd = "PlaintextP@ss123"
    hashed = get_password_hash(raw_pwd)
    assert raw_pwd not in hashed


# ==============================================================================
# 2. Registration API Tests
# ==============================================================================

def test_customer_registration_success(client: TestClient, db_session: Session):
    """Verify customer registration defaults to CUSTOMER and returns safe response."""
    payload = {
        "full_name": "New Registered Customer",
        "email": "new.customer@example.com",
        "phone": "9123456789",
        "password": "StrongPassword123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "new.customer@example.com"
    assert data["full_name"] == "New Registered Customer"
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True
    assert "user_id" in data

    # STRICT SECURITY: password and password_hash must NEVER appear in response
    assert "password" not in data
    assert "password_hash" not in data

    # Verify database record has Argon2 hash
    user_in_db = db_session.query(User).filter(User.email == "new.customer@example.com").first()
    assert user_in_db is not None
    assert user_in_db.password_hash.startswith("$argon2")


def test_duplicate_email_rejection(client: TestClient, test_customer: User):
    """Verify registration fails with 400 when an email already exists."""
    payload = {
        "full_name": "Imposter Customer",
        "email": test_customer.email,  # Same email as existing fixture
        "phone": "9998887776",
        "password": "AnotherPassword123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_registration_weak_password_rejection(client: TestClient):
    """Verify weak password is rejected with 422."""
    payload = {
        "full_name": "Weak Pwd User",
        "email": "weak@example.com",
        "password": "short"  # Less than 8 chars
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 3. Login & Authentication Tests
# ==============================================================================

def test_successful_login(client: TestClient, test_customer: User):
    """Verify valid credentials return JWT token and safe user details."""
    payload = {
        "email": test_customer.email,
        "password": "ValidCustomer123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["email"] == test_customer.email
    assert data["user"]["role"] == "CUSTOMER"

    # Verify password hash is NOT exposed
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]

    # Decode and verify token
    token = data["access_token"]
    payload = decode_access_token(token)
    assert payload["sub"] == str(test_customer.user_id)
    assert payload["email"] == test_customer.email
    assert payload["role"] == "CUSTOMER"


def test_incorrect_password_rejection(client: TestClient, test_customer: User):
    """Verify login with incorrect password returns 401."""
    payload = {
        "email": test_customer.email,
        "password": "WrongPassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_inactive_account_rejection(client: TestClient, test_inactive_user: User):
    """Verify login for deactivated account is rejected with 403."""
    payload = {
        "email": test_inactive_user.email,
        "password": "InactiveUser123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


# ==============================================================================
# 4. JWT Token Validation & Expiry Tests
# ==============================================================================

def test_jwt_expired_token_rejection(client: TestClient, test_customer: User):
    """Verify expired JWT tokens are rejected with 401."""
    # Create token that expired 10 minutes ago
    expired_token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role,
        expires_delta=timedelta(minutes=-10)
    )

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_auth_me_endpoint(client: TestClient, test_customer: User):
    """Verify GET /api/v1/auth/me returns current user profile."""
    token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_customer.user_id
    assert data["email"] == test_customer.email
    assert "password_hash" not in data


def test_logout_endpoint(client: TestClient, test_customer: User):
    """Verify POST /api/v1/auth/logout succeeds."""
    token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()


# ==============================================================================
# 5. Role-Based Authorization & User Management Tests
# ==============================================================================

def test_customer_can_update_own_profile(client: TestClient, test_customer: User):
    """Verify customers can update their own name and phone."""
    token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"full_name": "Rishi Updated Customer", "phone": "9999999999"}

    response = client.patch("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Rishi Updated Customer"
    assert data["phone"] == "9999999999"


def test_customer_cannot_elevate_role(client: TestClient, test_customer: User):
    """Verify customer cannot change their role through /users/me."""
    token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"role": "ADMIN", "full_name": "Hacker"}

    response = client.patch("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    # Role must still be CUSTOMER
    assert response.json()["role"] == "CUSTOMER"


def test_customer_forbidden_from_admin_user_list(client: TestClient, test_customer: User):
    """Verify customer receives 403 Forbidden when calling GET /api/v1/users."""
    token = create_access_token(
        subject=test_customer.user_id,
        email=test_customer.email,
        role=test_customer.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]


def test_admin_can_list_all_users(client: TestClient, test_admin: User, test_customer: User):
    """Verify admin can list all registered users."""
    token = create_access_token(
        subject=test_admin.user_id,
        email=test_admin.email,
        role=test_admin.role
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 2
    # Verify no password_hash exposed in list
    for u in users:
        assert "password_hash" not in u


def test_admin_can_deactivate_and_activate_user(client: TestClient, test_admin: User, test_customer: User):
    """Verify admin can toggle user active status."""
    token = create_access_token(
        subject=test_admin.user_id,
        email=test_admin.email,
        role=test_admin.role
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Deactivate customer
    resp_deact = client.patch(
        f"/api/v1/users/{test_customer.user_id}/status",
        json={"is_active": False},
        headers=headers
    )
    assert resp_deact.status_code == 200
    assert resp_deact.json()["is_active"] is False

    # Reactivate customer
    resp_act = client.patch(
        f"/api/v1/users/{test_customer.user_id}/status",
        json={"is_active": True},
        headers=headers
    )
    assert resp_act.status_code == 200
    assert resp_act.json()["is_active"] is True


def test_admin_cannot_deactivate_self(client: TestClient, test_admin: User):
    """Verify admin cannot deactivate their own active account."""
    token = create_access_token(
        subject=test_admin.user_id,
        email=test_admin.email,
        role=test_admin.role
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch(
        f"/api/v1/users/{test_admin.user_id}/status",
        json={"is_active": False},
        headers=headers
    )
    assert response.status_code == 400
    assert "cannot deactivate their own" in response.json()["detail"]



def test_browser_cookie_logout_revokes_the_same_bearer_token(client, test_customer):
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-EV-Browser": "1"},
        json={"email": test_customer.email, "password": "ValidCustomer123!"},
    )
    assert response.status_code == 200
    assert response.json()["expires_in"] == 900
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Secure" in response.headers["set-cookie"]
    bearer = {"Authorization": "Bearer " + response.json()["access_token"]}
    client.cookies.set("ev_access", response.json()["access_token"], path="/api/v1")
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 403
    assert client.post("/api/v1/auth/logout", headers={"X-EV-Browser": "1"}).status_code == 200
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401

def test_admin_status_changes_are_audited(client, test_admin, test_customer):
    admin = create_access_token(test_admin.user_id, test_admin.email, test_admin.role)
    customer = create_access_token(test_customer.user_id, test_customer.email, test_customer.role)
    headers = {"Authorization": f"Bearer {admin}"}
    audit = "/api/v1/admin/audit-events"
    assert client.get(audit, headers={"Authorization": f"Bearer {customer}"}).status_code == 403
    response = client.patch(
        f"/api/v1/users/{test_customer.user_id}/status", json={"is_active": False}, headers=headers,
    )
    assert response.status_code == 200
    events = client.get(audit, headers=headers).json()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "user.status_changed"
    assert event["actor_id"] == test_admin.user_id
    assert event["resource_id"] == test_customer.user_id
    assert event["details"] == {"before": True, "after": False}
    assert client.get(audit, params={"before": event["event_id"]}, headers=headers).json() == []


def test_login_is_throttled_after_consecutive_attempts(client, monkeypatch):
    from backend.app.services import login_limits

    monkeypatch.setattr(login_limits, "time", lambda: 310.0)
    bad = {"email": "unregistered@example.com", "password": "incorrect"}
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json=bad).status_code == 401
    denied = client.post("/api/v1/auth/login", json=bad)
    assert denied.status_code == 429
    assert denied.headers["retry-after"] == "290"
    assert client.post("/api/v1/auth/login", json={**bad, "email": "another@example.com"}).status_code == 401
    monkeypatch.setattr(login_limits, "time", lambda: 600.0)
    assert client.post("/api/v1/auth/login", json=bad).status_code == 401
