"""
Automated Integration and Unit Tests for Module 4: Vehicle and Connector Management.
Tests run against an isolated in-memory SQLite database to ensure the live PostgreSQL 18
database and its 54 records remain 100% untouched.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle, ConnectorType, VehicleConnectorType


@pytest.fixture(autouse=True)
def seed_connector_types(db_session: Session):
    """Seed standard connector types into test database."""
    connectors = [
        ConnectorType(connector_type_id=1, type_name="CCS-2", description="Combined Charging System 2 (DC Fast)"),
        ConnectorType(connector_type_id=2, type_name="Type 2", description="Mennekes AC connector (Single/Three-phase)"),
        ConnectorType(connector_type_id=3, type_name="CHAdeMO", description="Japanese DC fast charging standard"),
        ConnectorType(connector_type_id=4, type_name="GB/T", description="Chinese national standard DC charging"),
    ]
    db_session.add_all(connectors)
    db_session.commit()


@pytest.fixture
def other_customer(db_session: Session) -> User:
    """Fixture providing a second customer to test ownership and isolation."""
    user = User(
        full_name="Second Customer",
        email="second.customer@test.com",
        phone="9876543299",
        password_hash=get_password_hash("Password123!"),
        role="CUSTOMER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_headers(user: User) -> dict:
    """Generate JWT Authorization Bearer header for a given user."""
    token = create_access_token(
        subject=user.user_id,
        email=user.email,
        role=user.role
    )
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# CONNECTOR STANDARDS TESTS
# ======================================================================

def test_list_connector_types(client: TestClient, test_customer: User):
    """Test retrieving available connector standards."""
    headers = get_auth_headers(test_customer)
    response = client.get("/api/v1/connectors", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    type_names = [c["type_name"] for c in data]
    assert "CCS-2" in type_names
    assert "Type 2" in type_names


def test_list_connectors_unauthenticated(client: TestClient):
    """Test connector listing requires authentication."""
    response = client.get("/api/v1/connectors")
    assert response.status_code == 401


# ======================================================================
# VEHICLE REGISTRATION TESTS
# ======================================================================

def test_register_vehicle_success(client: TestClient, test_customer: User):
    """Test successful vehicle registration bound to the authenticated customer."""
    headers = get_auth_headers(test_customer)
    payload = {
        "registration_number": "KA01EV1234",
        "make": "Tata",
        "model": "Nexon EV",
        "battery_capacity_kwh": 40.5,
        "connector_type_ids": [1, 2]
    }
    response = client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["registration_number"] == "KA01EV1234"
    assert data["make"] == "Tata"
    assert data["model"] == "Nexon EV"
    assert float(data["battery_capacity_kwh"]) == 40.5
    assert data["owner_user_id"] == test_customer.user_id
    assert len(data["connector_types"]) == 2
    assigned_ids = {c["connector_type_id"] for c in data["connector_types"]}
    assert assigned_ids == {1, 2}


def test_register_vehicle_duplicate_registration_rejected(client: TestClient, test_customer: User):
    """Test that duplicate vehicle registration numbers are rejected with 409 Conflict."""
    headers = get_auth_headers(test_customer)
    payload = {
        "registration_number": "MH12EV9999",
        "make": "MG",
        "model": "ZS EV",
        "battery_capacity_kwh": 50.3
    }
    # First registration succeeds
    res1 = client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second registration with identical number fails
    res2 = client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


def test_register_vehicle_invalid_battery_capacity_rejected(client: TestClient, test_customer: User):
    """Test that zero or negative battery capacity is rejected."""
    headers = get_auth_headers(test_customer)
    payload_zero = {
        "registration_number": "DL01EV0001",
        "make": "Hyundai",
        "model": "Ioniq 5",
        "battery_capacity_kwh": 0
    }
    res = client.post("/api/v1/vehicles", json=payload_zero, headers=headers)
    assert res.status_code == 422

    payload_negative = {
        "registration_number": "DL01EV0002",
        "make": "Hyundai",
        "model": "Ioniq 5",
        "battery_capacity_kwh": -10.5
    }
    res = client.post("/api/v1/vehicles", json=payload_negative, headers=headers)
    assert res.status_code == 422


def test_register_vehicle_nonexistent_connector_rejected(client: TestClient, test_customer: User):
    """Test that registering a vehicle with non-existent connector type IDs fails."""
    headers = get_auth_headers(test_customer)
    payload = {
        "registration_number": "GA01EV5555",
        "make": "BYD",
        "model": "Atto 3",
        "battery_capacity_kwh": 60.48,
        "connector_type_ids": [999, 1000]
    }
    response = client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert response.status_code == 400
    assert "do not exist" in response.json()["detail"]


# ======================================================================
# VEHICLE LISTING & ISOLATION TESTS
# ======================================================================

def test_list_vehicles_customer_isolation(
    client: TestClient,
    test_customer: User,
    other_customer: User
):
    """Test that customers can only view their own vehicles, maintaining strict isolation."""
    headers_cust1 = get_auth_headers(test_customer)
    headers_cust2 = get_auth_headers(other_customer)

    # Customer 1 registers a vehicle
    client.post("/api/v1/vehicles", json={
        "registration_number": "CUST1VEH",
        "make": "Mahindra",
        "model": "XUV400",
        "battery_capacity_kwh": 39.4
    }, headers=headers_cust1)

    # Customer 2 registers a vehicle
    client.post("/api/v1/vehicles", json={
        "registration_number": "CUST2VEH",
        "make": "Kia",
        "model": "EV6",
        "battery_capacity_kwh": 77.4
    }, headers=headers_cust2)

    # Cust 1 listing only includes Cust 1's vehicle
    res1 = client.get("/api/v1/vehicles", headers=headers_cust1)
    assert res1.status_code == 200
    regs1 = [v["registration_number"] for v in res1.json()]
    assert "CUST1VEH" in regs1
    assert "CUST2VEH" not in regs1

    # Cust 2 listing only includes Cust 2's vehicle
    res2 = client.get("/api/v1/vehicles", headers=headers_cust2)
    assert res2.status_code == 200
    regs2 = [v["registration_number"] for v in res2.json()]
    assert "CUST2VEH" in regs2
    assert "CUST1VEH" not in regs2


def test_list_vehicles_admin_access(
    client: TestClient,
    test_admin: User,
    test_customer: User,
    other_customer: User
):
    """Test that Admin can view all vehicles or filter by owner."""
    headers_cust1 = get_auth_headers(test_customer)
    headers_admin = get_auth_headers(test_admin)

    client.post("/api/v1/vehicles", json={
        "registration_number": "ADMINSEES",
        "make": "Audi",
        "model": "e-tron",
        "battery_capacity_kwh": 95.0
    }, headers=headers_cust1)

    # Admin lists all vehicles
    res_admin = client.get("/api/v1/vehicles", headers=headers_admin)
    assert res_admin.status_code == 200
    regs = [v["registration_number"] for v in res_admin.json()]
    assert "ADMINSEES" in regs

    # Admin filters by owner_user_id
    res_filter = client.get(f"/api/v1/vehicles?owner_user_id={test_customer.user_id}", headers=headers_admin)
    assert res_filter.status_code == 200
    assert all(v["owner_user_id"] == test_customer.user_id for v in res_filter.json())


# ======================================================================
# VEHICLE RETRIEVAL & OWNERSHIP ACCESS CONTROL
# ======================================================================

def test_get_vehicle_details_owner_success(client: TestClient, test_customer: User):
    """Test owner successfully retrieves their own vehicle details."""
    headers = get_auth_headers(test_customer)
    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "GETOWN1",
        "make": "BMW",
        "model": "i4",
        "battery_capacity_kwh": 83.9,
        "connector_type_ids": [1]
    }, headers=headers)
    vehicle_id = create_res.json()["vehicle_id"]

    res = client.get(f"/api/v1/vehicles/{vehicle_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["registration_number"] == "GETOWN1"
    assert res.json()["make"] == "BMW"


def test_get_vehicle_details_unauthorized_forbidden(
    client: TestClient,
    test_customer: User,
    other_customer: User
):
    """Test that accessing another customer's vehicle returns 403 Forbidden."""
    headers_cust1 = get_auth_headers(test_customer)
    headers_cust2 = get_auth_headers(other_customer)

    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "PRIVATEVEH",
        "make": "Porsche",
        "model": "Taycan",
        "battery_capacity_kwh": 93.4
    }, headers=headers_cust1)
    vehicle_id = create_res.json()["vehicle_id"]

    # Customer 2 attempts to inspect Customer 1's vehicle
    res = client.get(f"/api/v1/vehicles/{vehicle_id}", headers=headers_cust2)
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]


def test_get_vehicle_details_not_found(client: TestClient, test_customer: User):
    """Test retrieving non-existent vehicle returns 404."""
    headers = get_auth_headers(test_customer)
    res = client.get("/api/v1/vehicles/99999", headers=headers)
    assert res.status_code == 404


# ======================================================================
# VEHICLE UPDATE TESTS
# ======================================================================

def test_update_vehicle_success(client: TestClient, test_customer: User):
    """Test updating vehicle make, model, and battery capacity."""
    headers = get_auth_headers(test_customer)
    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "UPDATE01",
        "make": "Tata",
        "model": "Tigor EV",
        "battery_capacity_kwh": 26.0
    }, headers=headers)
    vehicle_id = create_res.json()["vehicle_id"]

    update_payload = {
        "model": "Tigor EV Long Range",
        "battery_capacity_kwh": 31.5
    }
    res = client.patch(f"/api/v1/vehicles/{vehicle_id}", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "Tigor EV Long Range"
    assert float(data["battery_capacity_kwh"]) == 31.5
    assert data["make"] == "Tata"  # Unchanged


def test_update_vehicle_duplicate_registration_rejected(client: TestClient, test_customer: User):
    """Test updating registration number to an existing one returns 409 Conflict."""
    headers = get_auth_headers(test_customer)
    # Register vehicle 1
    client.post("/api/v1/vehicles", json={
        "registration_number": "EXISTS01",
        "make": "Tata",
        "model": "Punch EV",
        "battery_capacity_kwh": 35.0
    }, headers=headers)

    # Register vehicle 2
    res2 = client.post("/api/v1/vehicles", json={
        "registration_number": "CHANGE01",
        "make": "Tata",
        "model": "Curvv EV",
        "battery_capacity_kwh": 45.0
    }, headers=headers)
    veh2_id = res2.json()["vehicle_id"]

    # Try changing veh2 reg to EXISTS01
    update_res = client.patch(
        f"/api/v1/vehicles/{veh2_id}",
        json={"registration_number": "EXISTS01"},
        headers=headers
    )
    assert update_res.status_code == 409
    assert "already in use" in update_res.json()["detail"]


def test_update_vehicle_unauthorized_forbidden(
    client: TestClient,
    test_customer: User,
    other_customer: User
):
    """Test updating another customer's vehicle is rejected with 403 Forbidden."""
    headers_cust1 = get_auth_headers(test_customer)
    headers_cust2 = get_auth_headers(other_customer)

    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "LOCK01",
        "make": "Volvo",
        "model": "XC40 Recharge",
        "battery_capacity_kwh": 78.0
    }, headers=headers_cust1)
    vehicle_id = create_res.json()["vehicle_id"]

    # Customer 2 attempts update
    res = client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"model": "Hacked Model"},
        headers=headers_cust2
    )
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]


# ======================================================================
# VEHICLE CONNECTOR MAPPING & TRANSACTION TESTS
# ======================================================================

def test_get_and_update_vehicle_connectors(client: TestClient, test_customer: User):
    """Test getting and updating vehicle connector mappings."""
    headers = get_auth_headers(test_customer)
    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "CONNMAP01",
        "make": "Mercedes",
        "model": "EQS",
        "battery_capacity_kwh": 107.8,
        "connector_type_ids": [1]
    }, headers=headers)
    vehicle_id = create_res.json()["vehicle_id"]

    # GET initial connectors
    get_res = client.get(f"/api/v1/vehicles/{vehicle_id}/connectors", headers=headers)
    assert get_res.status_code == 200
    connectors = get_res.json()
    assert len(connectors) == 1
    assert connectors[0]["connector_type_id"] == 1

    # PUT replace with connectors [1, 2, 3]
    put_res = client.put(
        f"/api/v1/vehicles/{vehicle_id}/connectors",
        json={"connector_type_ids": [1, 2, 3]},
        headers=headers
    )
    assert put_res.status_code == 200
    updated_connectors = put_res.json()
    assert len(updated_connectors) == 3
    updated_ids = {c["connector_type_id"] for c in updated_connectors}
    assert updated_ids == {1, 2, 3}


def test_update_vehicle_connectors_deduplication(client: TestClient, test_customer: User):
    """Test duplicate connector type IDs in payload are automatically deduplicated."""
    headers = get_auth_headers(test_customer)
    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "DEDUP01",
        "make": "Tesla",
        "model": "Model 3",
        "battery_capacity_kwh": 75.0
    }, headers=headers)
    vehicle_id = create_res.json()["vehicle_id"]

    # Supply duplicate IDs [1, 1, 2, 2]
    put_res = client.put(
        f"/api/v1/vehicles/{vehicle_id}/connectors",
        json={"connector_type_ids": [1, 1, 2, 2]},
        headers=headers
    )
    assert put_res.status_code == 200
    updated_ids = [c["connector_type_id"] for c in put_res.json()]
    assert len(updated_ids) == 2
    assert set(updated_ids) == {1, 2}


def test_update_vehicle_connectors_nonexistent_rejected(client: TestClient, test_customer: User):
    """Test submitting invalid connector type IDs fails with 400 Bad Request."""
    headers = get_auth_headers(test_customer)
    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "BADCONN01",
        "make": "Audi",
        "model": "Q8 e-tron",
        "battery_capacity_kwh": 114.0
    }, headers=headers)
    vehicle_id = create_res.json()["vehicle_id"]

    put_res = client.put(
        f"/api/v1/vehicles/{vehicle_id}/connectors",
        json={"connector_type_ids": [1, 9999]},
        headers=headers
    )
    assert put_res.status_code == 400
    assert "do not exist" in put_res.json()["detail"]


def test_update_vehicle_connectors_unauthorized_forbidden(
    client: TestClient,
    test_customer: User,
    other_customer: User
):
    """Test customer cannot update connector mappings on another customer's vehicle."""
    headers_cust1 = get_auth_headers(test_customer)
    headers_cust2 = get_auth_headers(other_customer)

    create_res = client.post("/api/v1/vehicles", json={
        "registration_number": "UNAUTHCONN",
        "make": "Jaguar",
        "model": "I-Pace",
        "battery_capacity_kwh": 90.0
    }, headers=headers_cust1)
    vehicle_id = create_res.json()["vehicle_id"]

    # Customer 2 attempts to change connectors
    res = client.put(
        f"/api/v1/vehicles/{vehicle_id}/connectors",
        json={"connector_type_ids": [2]},
        headers=headers_cust2
    )
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]
