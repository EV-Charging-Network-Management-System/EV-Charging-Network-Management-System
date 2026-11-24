"""
Automated Integration and Unit Tests for Module 8:
Charging Session Management and Energy Metering.

Tests execute against an isolated in-memory test database to ensure the live
PostgreSQL 18 database (ev_charging_network) and its 54 records remain 100% untouched.
"""

import pytest
from datetime import datetime, timezone, timedelta, time
from decimal import Decimal
from typing import Tuple, List, Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import ConnectorType, Vehicle, VehicleConnectorType
from backend.app.models.tariff import Tariff, PricingRule
from backend.app.models.session import ChargingSession
from backend.app.models.reservation import Reservation


@pytest.fixture(autouse=True)
def seed_connectors(db_session: Session):
    """Seed standard connector types into test database."""
    connectors = [
        ConnectorType(connector_type_id=1, type_name="CCS-2", description="Combined Charging System 2 (DC Fast)"),
        ConnectorType(connector_type_id=2, type_name="Type 2", description="Mennekes AC connector"),
        ConnectorType(connector_type_id=3, type_name="CHAdeMO", description="Japanese DC fast charging standard"),
        ConnectorType(connector_type_id=4, type_name="GB/T", description="Chinese standard DC charging"),
    ]
    db_session.add_all(connectors)
    db_session.commit()


def get_auth_headers(user: User) -> dict:
    """Generate JWT Authorization Bearer header for a given user."""
    token = create_access_token(
        subject=user.user_id,
        email=user.email,
        role=user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_customer(db_session: Session) -> User:
    """Fixture providing a second customer for ownership isolation tests."""
    user = User(
        user_id=10,
        full_name="Pooja Customer",
        email="pooja.customer@test.com",
        phone="9876543299",
        password_hash=get_password_hash("ValidCustomer123!"),
        role="CUSTOMER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_setup(db_session: Session, test_customer: User, second_customer: User, test_operator: User):
    """
    Standard test fixture setup:
    - Station with 2 chargers (Charger 1: CCS-2 50kW ONLINE, Charger 2: Type 2 22kW MAINTENANCE, Charger 3: CCS-2 120kW ONLINE)
    - Vehicle 1 for test_customer with CCS-2 connector
    - Vehicle 2 for second_customer with Type 2 connector
    - Tariff for Station
    """
    station = Station(
        station_id=1,
        station_name="Pune Central Supercharger",
        address="100 Shivaji Nagar",
        city="Pune",
        latitude=Decimal("18.5314"),
        longitude=Decimal("73.8446"),
        opening_time=time(6, 0),
        closing_time=time(23, 0),
        status="ACTIVE",
        operator_id=test_operator.user_id
    )
    db_session.add(station)

    # Charger 1: CCS-2, 50 kW, ONLINE
    ch1 = Charger(
        charger_id=1,
        station_id=1,
        connector_type_id=1,
        charger_code="PUN-01",
        power_kw=Decimal("50.00"),
        operational_status="ONLINE"
    )
    # Charger 2: Type 2, 22 kW, MAINTENANCE
    ch2 = Charger(
        charger_id=2,
        station_id=1,
        connector_type_id=2,
        charger_code="PUN-02",
        power_kw=Decimal("22.00"),
        operational_status="MAINTENANCE"
    )
    # Charger 3: CCS-2, 120 kW, ONLINE
    ch3 = Charger(
        charger_id=3,
        station_id=1,
        connector_type_id=1,
        charger_code="PUN-03",
        power_kw=Decimal("120.00"),
        operational_status="ONLINE"
    )
    db_session.add_all([ch1, ch2, ch3])

    # Customer 1 Vehicle (Nexon EV with CCS-2)
    v1 = Vehicle(
        vehicle_id=1,
        owner_user_id=test_customer.user_id,
        registration_number="MH12AB1234",
        make="Tata",
        model="Nexon EV",
        battery_capacity_kwh=Decimal("40.50")
    )
    db_session.add(v1)

    vct1 = VehicleConnectorType(vehicle_id=1, connector_type_id=1)
    db_session.add(vct1)

    # Customer 2 Vehicle (Tiago EV with Type 2 only)
    v2 = Vehicle(
        vehicle_id=2,
        owner_user_id=second_customer.user_id,
        registration_number="MH12XY9876",
        make="Tata",
        model="Tiago EV",
        battery_capacity_kwh=Decimal("24.00")
    )
    db_session.add(v2)
    vct2 = VehicleConnectorType(vehicle_id=2, connector_type_id=2)
    db_session.add(vct2)

    # Tariff
    now = datetime.now(timezone.utc)
    tariff = Tariff(
        tariff_id=1,
        station_id=1,
        connector_type_id=None,
        base_price_per_kwh=Decimal("12.00"),
        session_fee=Decimal("10.00"),
        tax_rate_percent=Decimal("5.00"),
        valid_from=now - timedelta(days=10)
    )
    db_session.add(tariff)
    db_session.commit()

    return {
        "station": station,
        "chargers": [ch1, ch2, ch3],
        "vehicles": [v1, v2],
        "tariff": tariff
    }


# ============================================================================
# TASK 1: START CHARGING SESSION TESTS
# ============================================================================

def test_start_reserved_charging_session(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    db_session: Session
):
    """Customer successfully starts a session linked to their confirmed reservation."""
    now = datetime.now(timezone.utc)
    resv = Reservation(
        reservation_id=101,
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        start_at=now - timedelta(minutes=5),
        end_at=now + timedelta(minutes=55),
        status="CONFIRMED"
    )
    db_session.add(resv)
    db_session.commit()

    payload = {
        "reservation_id": 101,
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.500"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 201
    data = res.json()
    assert data["session_id"] is not None
    assert data["status"] == "ACTIVE"
    assert data["reservation_id"] == 101
    assert data["user_id"] == test_customer.user_id
    assert float(data["meter_start_kwh"]) == 100.5
    assert data["ended_at"] is None
    assert data["meter_end_kwh"] is None
    assert data["vehicle"]["registration_number"] == "MH12AB1234"
    assert data["charger"]["charger_code"] == "PUN-01"


def test_start_walk_in_charging_session(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Customer successfully starts a walk-in session without prior reservation."""
    payload = {
        "reservation_id": None,
        "vehicle_id": 1,
        "charger_id": 3,  # Charger 3 (CCS-2, ONLINE)
        "meter_start_kwh": "250.000"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "ACTIVE"
    assert data["reservation_id"] is None
    assert float(data["meter_start_kwh"]) == 250.0
    assert data["charger"]["charger_code"] == "PUN-03"


def test_start_session_invalid_reservation_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    db_session: Session
):
    """Starting a session with an already COMPLETED or non-existent reservation is rejected."""
    # 1. Non-existent reservation
    res1 = client.post("/api/v1/sessions/start", json={
        "reservation_id": 9999,
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }, headers=get_auth_headers(test_customer))
    assert res1.status_code == 404

    # 2. Already completed reservation
    now = datetime.now(timezone.utc)
    resv = Reservation(
        reservation_id=102,
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        start_at=now - timedelta(hours=2),
        end_at=now - timedelta(hours=1),
        status="COMPLETED"
    )
    db_session.add(resv)
    db_session.commit()

    res2 = client.post("/api/v1/sessions/start", json={
        "reservation_id": 102,
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }, headers=get_auth_headers(test_customer))
    assert res2.status_code == 400
    assert "completed" in res2.json()["detail"].lower()


def test_start_session_unauthorized_vehicle_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Customer A cannot start a session using Customer B's vehicle (403 Forbidden)."""
    payload = {
        "vehicle_id": 2,  # Owned by second_customer
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 403
    assert "account" in res.json()["detail"].lower()


def test_start_session_incompatible_connector_rejected(
    client: TestClient,
    test_setup: dict,
    second_customer: User
):
    """Vehicle 2 (Type 2) attempting to charge at Charger 1 (CCS-2) is rejected with 422."""
    payload = {
        "vehicle_id": 2,  # Type 2 only
        "charger_id": 1,  # CCS-2 charger
        "meter_start_kwh": "50.0"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(second_customer))
    assert res.status_code == 422
    assert "incompatible connector" in res.json()["detail"].lower()


def test_start_session_charger_under_maintenance_rejected(
    client: TestClient,
    test_setup: dict,
    second_customer: User
):
    """Starting a session on a charger with operational_status='MAINTENANCE' is rejected with 400."""
    payload = {
        "vehicle_id": 2,
        "charger_id": 2,  # Charger 2 is MAINTENANCE
        "meter_start_kwh": "50.0"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(second_customer))
    assert res.status_code == 400
    assert "maintenance" in res.json()["detail"].lower()


def test_start_session_duplicate_active_session_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Cannot start two concurrent ACTIVE sessions on the same charger (409 Conflict)."""
    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }
    # 1. First session starts
    res1 = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res1.status_code == 201

    # 2. Second session attempt on same charger
    res2 = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res2.status_code == 409
    assert "already has an active charging session" in res2.json()["detail"].lower()


def test_start_session_invalid_starting_meter_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Negative meter reading is rejected."""
    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "-10.0"
    }
    res = client.post("/api/v1/sessions/start", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code in (400, 422)


# ============================================================================
# TASK 2: COMPLETE & INTERRUPT CHARGING SESSION TESTS
# ============================================================================

def test_successful_session_completion(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    db_session: Session
):
    """Customer completes an active session and energy consumption is accurately computed."""
    # 1. Start session with linked reservation
    now = datetime.now(timezone.utc)
    resv = Reservation(
        reservation_id=201,
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=3,
        start_at=now - timedelta(minutes=10),
        end_at=now + timedelta(minutes=50),
        status="CONFIRMED"
    )
    db_session.add(resv)
    db_session.commit()

    start_res = client.post("/api/v1/sessions/start", json={
        "reservation_id": 201,
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "100.000"
    }, headers=get_auth_headers(test_customer))
    assert start_res.status_code == 201
    session_id = start_res.json()["session_id"]

    # 2. Complete session with meter_end = 125.500 kWh (25.500 kWh consumed)
    complete_res = client.post(f"/api/v1/sessions/{session_id}/complete", json={
        "meter_end_kwh": "125.500"
    }, headers=get_auth_headers(test_customer))
    assert complete_res.status_code == 200
    data = complete_res.json()
    assert data["status"] == "COMPLETED"
    assert data["ended_at"] is not None
    assert float(data["meter_end_kwh"]) == 125.5
    assert float(data["energy_consumed_kwh"]) == 25.5
    assert data["estimated_cost"] is not None

    # Verify associated reservation was updated to COMPLETED
    db_session.expire_all()
    updated_resv = db_session.get(Reservation, 201)
    assert updated_resv.status == "COMPLETED"


def test_complete_session_ending_meter_lower_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Ending meter reading lower than starting meter reading is rejected with 400."""
    start_res = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "100.000"
    }, headers=get_auth_headers(test_customer))
    session_id = start_res.json()["session_id"]

    res = client.post(f"/api/v1/sessions/{session_id}/complete", json={
        "meter_end_kwh": "95.000"  # Lower than 100.0
    }, headers=get_auth_headers(test_customer))
    assert res.status_code == 400
    assert "cannot be less than starting reading" in res.json()["detail"].lower()


def test_duplicate_session_completion_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Completing an already COMPLETED session is rejected with 400."""
    start_res = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "100.000"
    }, headers=get_auth_headers(test_customer))
    session_id = start_res.json()["session_id"]

    # 1. First completion succeeds
    res1 = client.post(f"/api/v1/sessions/{session_id}/complete", json={
        "meter_end_kwh": "110.000"
    }, headers=get_auth_headers(test_customer))
    assert res1.status_code == 200

    # 2. Second completion fails
    res2 = client.post(f"/api/v1/sessions/{session_id}/complete", json={
        "meter_end_kwh": "115.000"
    }, headers=get_auth_headers(test_customer))
    assert res2.status_code == 400
    assert "already completed" in res2.json()["detail"].lower()


def test_session_interruption(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Interrupting an active session transitions to INTERRUPTED with final reading recorded."""
    start_res = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "200.000"
    }, headers=get_auth_headers(test_customer))
    session_id = start_res.json()["session_id"]

    interrupt_res = client.post(f"/api/v1/sessions/{session_id}/interrupt", json={
        "meter_end_kwh": "212.500",
        "reason": "Emergency stop button pressed"
    }, headers=get_auth_headers(test_customer))
    assert interrupt_res.status_code == 200
    data = interrupt_res.json()
    assert data["status"] == "INTERRUPTED"
    assert float(data["meter_end_kwh"]) == 212.5
    assert float(data["energy_consumed_kwh"]) == 12.5


# ============================================================================
# TASK 3: RBAC & DATA ISOLATION TESTS
# ============================================================================

def test_customer_session_isolation(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    second_customer: User
):
    """Customer A cannot view Customer B's active or historic sessions."""
    # Customer 1 starts a session
    s1 = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }, headers=get_auth_headers(test_customer)).json()

    # Customer 2 lists active sessions (should NOT contain s1)
    res = client.get("/api/v1/sessions/active", headers=get_auth_headers(second_customer))
    assert res.status_code == 200
    assert all(s["session_id"] != s1["session_id"] for s in res.json())

    # Customer 2 attempts direct access to Customer 1's session (403 Forbidden)
    res_direct = client.get(f"/api/v1/sessions/{s1['session_id']}", headers=get_auth_headers(second_customer))
    assert res_direct.status_code == 403


def test_operator_authorization(
    client: TestClient,
    test_setup: dict,
    test_operator: User,
    test_customer: User
):
    """Operator can view active sessions and complete sessions at their managed stations."""
    s1 = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }, headers=get_auth_headers(test_customer)).json()

    # Operator views active sessions at their station
    res = client.get("/api/v1/sessions/active", headers=get_auth_headers(test_operator))
    assert res.status_code == 200
    assert any(s["session_id"] == s1["session_id"] for s in res.json())

    # Operator completes session (e.g. station attendant override)
    comp_res = client.post(f"/api/v1/sessions/{s1['session_id']}/complete", json={
        "meter_end_kwh": "115.0"
    }, headers=get_auth_headers(test_operator))
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"


def test_admin_access(
    client: TestClient,
    test_setup: dict,
    test_admin: User,
    test_customer: User
):
    """Admin has full access to inspect history and manage any session across the network."""
    s1 = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "100.0"
    }, headers=get_auth_headers(test_customer)).json()

    # Admin fetches history
    res = client.get("/api/v1/sessions/history", headers=get_auth_headers(test_admin))
    assert res.status_code == 200
    assert any(s["session_id"] == s1["session_id"] for s in res.json())

    # Admin interrupts session
    res_int = client.post(f"/api/v1/sessions/{s1['session_id']}/interrupt", json={
        "meter_end_kwh": "105.0",
        "reason": "Admin safety inspection"
    }, headers=get_auth_headers(test_admin))
    assert res_int.status_code == 200
    assert res_int.json()["status"] == "INTERRUPTED"


def test_tariff_snapshot_preservation(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Session preserves tariff metadata and correctly evaluates dynamic cost breakdown."""
    start_res = client.post("/api/v1/sessions/start", json={
        "vehicle_id": 1,
        "charger_id": 3,
        "meter_start_kwh": "100.000"
    }, headers=get_auth_headers(test_customer))
    assert start_res.status_code == 201
    s_data = start_res.json()
    assert s_data["tariff"] is not None
    assert float(s_data["tariff"]["base_price_per_kwh"]) == 12.0
    assert float(s_data["tariff"]["session_fee"]) == 10.0
    assert float(s_data["tariff"]["tax_rate_percent"]) == 5.0


def test_concurrent_session_start_attempts(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    second_customer: User
):
    """When two requests attempt to start an active session on the same bay, second is rejected."""
    payload1 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }
    # Request 1 succeeds
    r1 = client.post("/api/v1/sessions/start", json=payload1, headers=get_auth_headers(test_customer))
    assert r1.status_code == 201

    # Request 2 (even for another vehicle/user) on the same charger is rejected with 409
    payload2 = {
        "vehicle_id": 2,
        "charger_id": 1,
        "meter_start_kwh": "100.0"
    }
    r2 = client.post("/api/v1/sessions/start", json=payload2, headers=get_auth_headers(second_customer))
    assert r2.status_code == 409
    assert "already has an active charging session" in r2.json()["detail"].lower()


def test_session_mutations_can_be_replayed(client, test_setup, test_customer):
    key = {**get_auth_headers(test_customer), "Idempotency-Key": "retry-request-1"}
    payload = {"vehicle_id": 1, "charger_id": 3, "meter_start_kwh": "25"}
    first = client.post("/api/v1/sessions/start", json=payload, headers=key)
    assert first.status_code == 201, first.text
    assert client.post("/api/v1/sessions/start", json=payload, headers=key).json() == first.json()
    assert client.post("/api/v1/sessions/start", json={**payload, "meter_start_kwh": "30"}, headers=key).status_code == 409

    path = f"/api/v1/sessions/{first.json()['session_id']}/complete"
    first_completion = client.post(path, json={"meter_end_kwh": "33"}, headers=key)
    replay = client.post(path, json={"meter_end_kwh": "33"}, headers=key)
    assert first_completion.status_code == replay.status_code == 200
    assert first_completion.json() == replay.json()

def test_invoice_uses_rate_accepted_at_session_start(client, db_session, test_setup, test_customer):
    headers = get_auth_headers(test_customer)
    start = client.post("/api/v1/sessions/start", headers=headers, json={
        "vehicle_id": 1, "charger_id": 3, "meter_start_kwh": "10",
    })
    assert start.status_code == 201, start.text
    session_id = start.json()["session_id"]
    tariff = test_setup["tariff"]
    tariff.base_price_per_kwh = Decimal("99.00")
    tariff.session_fee = Decimal("500.00")
    tariff.tax_rate_percent = Decimal("15.00")
    db_session.commit()

    complete = client.post(f"/api/v1/sessions/{session_id}/complete", headers=headers, json={"meter_end_kwh": "20"})
    assert Decimal(complete.json()["tariff"]["effective_rate_per_kwh"]) == Decimal("12.00")
    invoice = client.post(f"/api/v1/invoices/generate/{session_id}", headers=headers)
    assert invoice.status_code == 201, invoice.text
    assert Decimal(invoice.json()["price_per_kwh"]) == Decimal("12.00")
    assert Decimal(invoice.json()["session_fee"]) == Decimal("10.00")
    assert Decimal(invoice.json()["tax_rate_percent"]) == Decimal("5.00")


def test_worker_expires_stale_bookings_flags_chargers_and_invoices_once(
    db_session, test_setup, test_customer,
):
    from sqlalchemy import select

    from backend.app.models.billing import Invoice
    from backend.app.models.workflow import ChargerHeartbeat
    from backend.app.worker import run_cycle

    now = datetime.now(timezone.utc)
    charger = test_setup["chargers"][0]
    vehicle = test_setup["vehicles"][0]
    reservation = Reservation(
        user_id=test_customer.user_id, vehicle_id=vehicle.vehicle_id,
        charger_id=charger.charger_id, start_at=now-timedelta(hours=2),
        end_at=now-timedelta(hours=1), status="CONFIRMED",
    )
    session = ChargingSession(
        user_id=test_customer.user_id, vehicle_id=vehicle.vehicle_id,
        charger_id=charger.charger_id, tariff_id=test_setup["tariff"].tariff_id,
        started_at=now-timedelta(hours=2), ended_at=now-timedelta(hours=1),
        status="COMPLETED", meter_start_kwh=Decimal("0"), meter_end_kwh=Decimal("10"),
    )
    db_session.add_all([
        reservation, session,
        ChargerHeartbeat(charger_id=charger.charger_id, last_seen_at=now-timedelta(minutes=10)),
    ])
    db_session.commit()
    run_cycle(now)
    run_cycle(now)
    db_session.refresh(reservation)
    db_session.refresh(charger)
    assert reservation.status == "NO_SHOW"
    assert charger.operational_status == "OUT_OF_SERVICE"
    assert len(db_session.scalars(select(Invoice).where(Invoice.session_id == session.session_id)).all()) == 1


def test_network_kpis_only_include_managed_stations(client, test_setup, test_customer, test_operator, other_operator):
    path = "/api/v1/admin/network-kpis"
    assert client.get(path, headers=get_auth_headers(test_customer)).status_code == 403
    response = client.get(path, headers=get_auth_headers(test_operator))
    assert response.status_code == 200, response.text
    assert len(response.json()["chargers"]) == 3
    assert len(response.json()["hours"]) == 24
    assert client.get(path, headers=get_auth_headers(other_operator)).json()["chargers"] == []

def test_station_list_applies_filters_before_pagination(client, test_setup, test_customer):
    headers = get_auth_headers(test_customer)
    listing = client.get("/api/v1/chargers", headers=headers, params={"operational_status": "ONLINE"})
    assert listing.status_code == 200
    first_page = client.get("/api/v1/chargers", headers=headers, params={
        "operational_status": "ONLINE", "limit": 1, "skip": 1,
    })
    assert first_page.status_code == 200, first_page.text
    assert first_page.json() == listing.json()[1:2]
    assert client.get("/api/v1/chargers", headers=headers, params={"limit": 0}).status_code == 422


def test_charger_status_updates_trigger_live_notification(db_session, test_setup):
    from contextlib import closing

    from backend.app.api.session_stream import stream_updates

    with closing(stream_updates("ev_chargers", 2)) as stream:
        assert next(stream).startswith("event: changed")
        test_setup["chargers"][0].operational_status = "OUT_OF_SERVICE"
        db_session.commit()
        assert next(stream).startswith("event: changed")

def test_site_power_cap_shares_remaining_budget_and_checks_station_owner(
    client, db_session, test_setup, test_customer, test_operator, other_operator,
):
    from backend.app.api.v1.endpoints.power import allocate_watts

    assert allocate_watts({1: 22000, 2: 60000, 3: 90000}, 100000) == {1: 22000, 2: 39000, 3: 39000}
    assert allocate_watts({1: 30000, 2: 30000}, 10001) == {1: 5001, 2: 5000}
    headers = get_auth_headers(test_operator)
    url = "/api/v1/stations/1/power-cap"
    assert client.put(url, headers=get_auth_headers(other_operator), json={"site_power_cap_kw": "50"}).status_code == 403
    assert client.put(url, headers=get_auth_headers(test_customer), json={"site_power_cap_kw": "50"}).status_code == 403
    for charger in (test_setup["chargers"][0], test_setup["chargers"][2]):
        db_session.add(ChargingSession(
            user_id=test_customer.user_id, vehicle_id=1, charger_id=charger.charger_id,
            tariff_id=test_setup["tariff"].tariff_id, meter_start_kwh=Decimal("0"), status="ACTIVE",
            started_at=datetime.now(timezone.utc),
        ))
    db_session.commit()

    response = client.put(url, headers=headers, json={"site_power_cap_kw": "50"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(data["total_allocated_kw"]) == Decimal("50")
    assert [Decimal(row["allocated_kw"]) for row in data["sessions"]] == [Decimal(25), Decimal(25)]
