"""
Automated Integration and Unit Tests for Module 7:
Reservation Management and Slot Conflict Engine.

Tests run against an isolated PostgreSQL database.
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
    - Station with 2 chargers (Charger 1: CCS-2 50kW ONLINE, Charger 2: Type 2 22kW MAINTENANCE)
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
    # Charger 3: CCS-2, 120 kW, ONLINE (High power)
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

    # Link v1 to connector CCS-2 (ID 1)
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


def get_slot(days_ahead: int = 1, start_hour: int = 10, duration_hours: int = 1) -> Tuple[datetime, datetime]:
    """Helper to return an operating slot guaranteed to fall within station operating hours (06:00-23:00 UTC)."""
    now = datetime.now(timezone.utc)
    base_date = (now + timedelta(days=days_ahead)).date()
    start = datetime.combine(base_date, time(start_hour, 0), tzinfo=timezone.utc)
    end = start + timedelta(hours=duration_hours)
    return start, end


# ============================================================================
# TASK 1: AVAILABILITY API TESTS
# ============================================================================

def test_availability_compatible_chargers_returned(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Test availability search returns compatible online chargers with pricing quotes."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=10, duration_hours=1)

    res = client.get(
        "/api/v1/reservations/availability",
        params={
            "station_id": 1,
            "vehicle_id": 1,
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat()
        },
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 200
    data = res.json()
    assert data["station_id"] == 1
    assert data["vehicle_id"] == 1
    # Vehicle 1 has CCS-2 (ID 1). Chargers 1 and 3 are CCS-2. Charger 2 is Type 2.
    assert data["total_compatible_chargers"] == 2
    assert data["available_chargers_count"] == 2

    # Verify pricing quote estimate is attached
    ch_res = data["chargers"][0]
    assert ch_res["is_available"] is True
    assert ch_res["estimated_price"] is not None
    assert ch_res["estimated_price"]["total_amount"] is not None


def test_availability_filters_min_power_kw(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Test min_power_kw filter excludes lower powered chargers."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=11, duration_hours=1)

    res = client.get(
        "/api/v1/reservations/availability",
        params={
            "station_id": 1,
            "vehicle_id": 1,
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "min_power_kw": "60.00"  # Excludes PUN-01 (50 kW), keeps PUN-03 (120 kW)
        },
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_compatible_chargers"] == 1
    assert data["chargers"][0]["charger_code"] == "PUN-03"


def test_availability_shows_unavailable_for_reserved_slot(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    db_session: Session
):
    """Overlapping confirmed reservation marks specific charger unavailable while preserving operational status."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=14, duration_hours=1)

    # Seed overlapping reservation on charger 1
    resv = Reservation(
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        start_at=start_time,
        end_at=end_time,
        status="CONFIRMED"
    )
    db_session.add(resv)
    db_session.commit()

    res = client.get(
        "/api/v1/reservations/availability",
        params={
            "station_id": 1,
            "vehicle_id": 1,
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat()
        },
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 200
    data = res.json()
    # Charger 1 is occupied/unavailable, Charger 3 is available
    ch1 = next(c for c in data["chargers"] if c["charger_id"] == 1)
    assert ch1["is_available"] is False
    assert ch1["operational_status"] == "ONLINE"  # Operational status is distinct!
    assert "already been reserved" in ch1["unavailability_reason"].lower()

    ch3 = next(c for c in data["chargers"] if c["charger_id"] == 3)
    assert ch3["is_available"] is True


# ============================================================================
# TASK 2: RESERVATION CREATION & CONFLICT TESTS
# ============================================================================

def test_successful_reservation_creation(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Customer successfully reserves an online compatible charger bay."""
    start_time, end_time = get_slot(days_ahead=2, start_hour=10, duration_hours=1)

    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 201
    data = res.json()
    assert data["reservation_id"] is not None
    assert data["status"] == "CONFIRMED"
    assert data["user_id"] == test_customer.user_id
    assert data["customer"]["email"] == test_customer.email
    assert data["vehicle"]["registration_number"] == "MH12AB1234"
    assert data["charger"]["charger_code"] == "PUN-01"


def test_invalid_time_interval_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """end_at <= start_at is rejected with 422 Unprocessable Entity."""
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1, hours=10)
    end_time = start_time - timedelta(minutes=30)  # Before start

    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 422


def test_past_reservation_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Booking a slot in the past is rejected with 400 Bad Request."""
    past_start = datetime.now(timezone.utc) - timedelta(days=2)
    past_end = past_start + timedelta(hours=1)

    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": past_start.isoformat(),
        "end_at": past_end.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 400
    assert "past" in res.json()["detail"].lower()


def test_unauthorized_vehicle_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Customer A cannot book a slot using Customer B's vehicle (403 Forbidden)."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=10, duration_hours=1)

    # Customer 1 attempts to use vehicle 2 (owned by second_customer)
    payload = {
        "vehicle_id": 2,
        "charger_id": 1,
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 403
    assert "account" in res.json()["detail"].lower()


def test_incompatible_connector_rejected(
    client: TestClient,
    test_setup: dict,
    second_customer: User
):
    """Vehicle 2 (Type 2) attempting to book Charger 1 (CCS-2) is rejected with 422."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=10, duration_hours=1)

    payload = {
        "vehicle_id": 2,  # Has only Type 2
        "charger_id": 1,  # CCS-2 charger
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(second_customer))
    assert res.status_code == 422
    assert "incompatible connector" in res.json()["detail"].lower()


def test_charger_under_maintenance_rejected(
    client: TestClient,
    test_setup: dict,
    second_customer: User
):
    """Reserving a charger with operational_status='MAINTENANCE' is rejected with 400."""
    start_time, end_time = get_slot(days_ahead=1, start_hour=10, duration_hours=1)

    payload = {
        "vehicle_id": 2,
        "charger_id": 2,  # MAINTENANCE
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(second_customer))
    assert res.status_code == 400
    assert "maintenance" in res.json()["detail"].lower()


def test_outside_operating_hours_rejected(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Booking a slot when station is closed (station hours: 06:00 to 23:00) is rejected with 400."""
    now = datetime.now(timezone.utc)
    # 02:00 to 03:00 AM (station is closed)
    slot_start = datetime(now.year, now.month, now.day, 2, 0, tzinfo=timezone.utc) + timedelta(days=1)
    slot_end = slot_start + timedelta(hours=1)

    payload = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": slot_start.isoformat(),
        "end_at": slot_end.isoformat()
    }
    res = client.post("/api/v1/reservations", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 400
    assert "operating hours" in res.json()["detail"].lower()


# ============================================================================
# TASK 3: DOUBLE-BOOKING CONFLICT & ADJACENT BOOKING TESTS
# ============================================================================

def test_overlapping_reservation_rejected_with_409_conflict(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Overlapping reservation (10:00–11:00 vs 10:30–11:30) is rejected with HTTP 409 Conflict."""
    base_time, _ = get_slot(days_ahead=2, start_hour=10, duration_hours=1)

    # 1. First booking: 10:00 - 11:00
    b1 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": base_time.isoformat(),
        "end_at": (base_time + timedelta(hours=1)).isoformat()
    }
    res1 = client.post("/api/v1/reservations", json=b1, headers=get_auth_headers(test_customer))
    assert res1.status_code == 201

    # 2. Overlapping booking: 10:30 - 11:30
    b2 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": (base_time + timedelta(minutes=30)).isoformat(),
        "end_at": (base_time + timedelta(minutes=90)).isoformat()
    }
    res2 = client.post("/api/v1/reservations", json=b2, headers=get_auth_headers(test_customer))
    assert res2.status_code == 409
    assert "already been reserved" in res2.json()["detail"].lower()


def test_adjacent_reservations_accepted(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Adjacent bookings (10:00–11:00 and 11:00–12:00) on the same charger are both accepted."""
    base_time, _ = get_slot(days_ahead=3, start_hour=10, duration_hours=1)

    # Booking 1: 10:00 - 11:00
    b1 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": base_time.isoformat(),
        "end_at": (base_time + timedelta(hours=1)).isoformat()
    }
    res1 = client.post("/api/v1/reservations", json=b1, headers=get_auth_headers(test_customer))
    assert res1.status_code == 201

    # Booking 2: 11:00 - 12:00 (Starts exactly when previous ends)
    b2 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": (base_time + timedelta(hours=1)).isoformat(),
        "end_at": (base_time + timedelta(hours=2)).isoformat()
    }
    res2 = client.post("/api/v1/reservations", json=b2, headers=get_auth_headers(test_customer))
    assert res2.status_code == 201


def test_cancelled_reservation_releases_slot(
    client: TestClient,
    test_setup: dict,
    test_customer: User
):
    """Cancelling a reservation immediately releases the slot so a new booking can succeed."""
    slot_start, slot_end = get_slot(days_ahead=4, start_hour=12, duration_hours=1)

    # 1. Create booking
    b1 = {
        "vehicle_id": 1,
        "charger_id": 1,
        "start_at": slot_start.isoformat(),
        "end_at": slot_end.isoformat()
    }
    create_res = client.post("/api/v1/reservations", json=b1, headers=get_auth_headers(test_customer))
    assert create_res.status_code == 201
    res_id = create_res.json()["reservation_id"]

    # 2. Cancel booking
    cancel_res = client.patch(f"/api/v1/reservations/{res_id}/cancel", headers=get_auth_headers(test_customer))
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 3. New booking for the same slot now succeeds!
    new_res = client.post("/api/v1/reservations", json=b1, headers=get_auth_headers(test_customer))
    assert new_res.status_code == 201


def test_cannot_cancel_completed_reservation(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    db_session: Session
):
    """Cancelling a COMPLETED reservation is rejected with 400 Bad Request."""
    now = datetime.now(timezone.utc)
    resv = Reservation(
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        start_at=now - timedelta(days=1),
        end_at=now - timedelta(days=1, hours=-1),
        status="COMPLETED"
    )
    db_session.add(resv)
    db_session.commit()

    res = client.patch(f"/api/v1/reservations/{resv.reservation_id}/cancel", headers=get_auth_headers(test_customer))
    assert res.status_code == 400
    assert "completed" in res.json()["detail"].lower()


# ============================================================================
# TASK 4: RBAC & ISOLATION RETRIEVAL TESTS
# ============================================================================

def test_customer_reservation_isolation(
    client: TestClient,
    test_setup: dict,
    test_customer: User,
    second_customer: User,
    db_session: Session
):
    """Customer A only sees their own reservations; cannot view Customer B's reservations."""
    now = datetime.now(timezone.utc)
    r1 = Reservation(user_id=test_customer.user_id, vehicle_id=1, charger_id=1, start_at=now + timedelta(days=1), end_at=now + timedelta(days=1, hours=1), status="CONFIRMED")
    r2 = Reservation(user_id=second_customer.user_id, vehicle_id=2, charger_id=3, start_at=now + timedelta(days=2), end_at=now + timedelta(days=2, hours=1), status="CONFIRMED")
    db_session.add_all([r1, r2])
    db_session.commit()

    # Customer 1 lists reservations
    res = client.get("/api/v1/reservations", headers=get_auth_headers(test_customer))
    assert res.status_code == 200
    res_list = res.json()
    assert all(r["user_id"] == test_customer.user_id for r in res_list)

    # Customer 1 attempts to directly access Customer 2's reservation
    single_res = client.get(f"/api/v1/reservations/{r2.reservation_id}", headers=get_auth_headers(test_customer))
    assert single_res.status_code == 403


def test_operator_can_view_managed_station_reservations(
    client: TestClient,
    test_setup: dict,
    test_operator: User,
    test_customer: User,
    db_session: Session
):
    """Station operator can view reservations at stations they operate."""
    now = datetime.now(timezone.utc)
    r1 = Reservation(user_id=test_customer.user_id, vehicle_id=1, charger_id=1, start_at=now + timedelta(days=1), end_at=now + timedelta(days=1, hours=1), status="CONFIRMED")
    db_session.add(r1)
    db_session.commit()

    res = client.get("/api/v1/reservations", headers=get_auth_headers(test_operator))
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_admin_has_full_reservation_access(
    client: TestClient,
    test_setup: dict,
    test_admin: User,
    test_customer: User,
    second_customer: User,
    db_session: Session
):
    """Admin can list and cancel any reservation across the entire network."""
    now = datetime.now(timezone.utc)
    r1 = Reservation(user_id=test_customer.user_id, vehicle_id=1, charger_id=1, start_at=now + timedelta(days=5), end_at=now + timedelta(days=5, hours=1), status="CONFIRMED")
    db_session.add(r1)
    db_session.commit()

    # Admin lists
    res = client.get("/api/v1/reservations", headers=get_auth_headers(test_admin))
    assert res.status_code == 200

    # Admin cancels customer reservation
    cancel_res = client.patch(f"/api/v1/reservations/{r1.reservation_id}/cancel", headers=get_auth_headers(test_admin))
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

def test_two_simultaneous_bookings_return_one_conflict(test_setup, test_customer):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import func, select

    from backend.app.core.database import SessionLocal
    from backend.app.main import app

    start, end = get_slot()
    payload = {
        "vehicle_id": test_setup["vehicles"][0].vehicle_id,
        "charger_id": test_setup["chargers"][0].charger_id,
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
    }
    headers = get_auth_headers(test_customer)
    ready = Barrier(2)

    def book():
        with TestClient(app) as browser:
            ready.wait(timeout=10)
            return browser.post("/api/v1/reservations", json=payload, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(lambda _: book(), range(2))) == [201, 409]

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Reservation)) == 1


def test_postgres_rejects_overlapping_bookings_outside_api(db_session, test_setup, test_customer):
    from sqlalchemy.exc import IntegrityError

    start, end = get_slot()
    vehicle_id = test_setup["vehicles"][0].vehicle_id
    charger_id = test_setup["chargers"][0].charger_id

    def reservation(start_at, end_at):
        return Reservation(user_id=test_customer.user_id, vehicle_id=vehicle_id,
                           charger_id=charger_id, start_at=start_at, end_at=end_at,
                           status="CONFIRMED")

    db_session.add(reservation(start, end))
    db_session.commit()
    db_session.add(reservation(start + timedelta(minutes=10), end + timedelta(minutes=10)))
    with pytest.raises(IntegrityError) as failure:
        db_session.commit()
    assert failure.value.orig.sqlstate == "23P01"
    db_session.rollback()
    db_session.add(reservation(end, end + timedelta(hours=1)))
    db_session.commit()


def test_ocpp_charger_reports_session_and_meter_data(db_session, test_setup, test_customer, monkeypatch):
    import base64
    from contextlib import closing

    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from backend.app.api.session_stream import session_updates
    from backend.app.core.charger_config import ChargerDevice
    from backend.app.core.config import settings
    from backend.app.core.database import SessionLocal
    from backend.app.main import app
    from backend.app.models.meter_reading import MeterReading

    charger = test_setup["chargers"][0]
    now = datetime.now(timezone.utc)
    reservation = Reservation(
        user_id=test_customer.user_id, vehicle_id=test_setup["vehicles"][0].vehicle_id,
        charger_id=charger.charger_id, status="CONFIRMED",
        start_at=now - timedelta(minutes=1), end_at=now + timedelta(hours=1),
    )
    db_session.add(reservation)
    db_session.commit()
    password = "test-device-only-credential-12345"
    monkeypatch.setattr(settings, "OCPP_DEVICES", {
        charger.charger_id: ChargerDevice(password=password, driver_tags={"driver-a": test_customer.user_id}),
    })
    auth = base64.b64encode(f"{charger.charger_id}:{password}".encode()).decode()
    path = f"/ocpp/{charger.charger_id}"
    with TestClient(app) as browser:
        with browser.websocket_connect(path, subprotocols=["ocpp1.6"], headers={"Authorization": f"Basic {auth}"}) as socket:
            def call(action, payload):
                socket.send_json([2, action, action, payload])
                return socket.receive_json()

            assert call("BootNotification", {"chargePointVendor": "Test", "chargePointModel": "Test"})[2]["status"] == "Accepted"
            assert call("StatusNotification", {"connectorId": 1, "status": "Available", "errorCode": "NoError"}) == [3, "StatusNotification", {}]
            request = {
                "connectorId": 1, "reservationId": reservation.reservation_id,
                "idTag": "driver-a", "meterStart": 10000, "timestamp": now.isoformat(),
            }
            assert call("StartTransaction", {**request, "idTag": "other"})[2]["transactionId"] == 0
            reply = call("StartTransaction", request)
            assert reply[0] == 3, reply
            session_id = reply[2]["transactionId"]
            assert call("StartTransaction", request)[2]["transactionId"] == session_id
            reading = {
                "connectorId": 1, "transactionId": session_id,
                "meterValue": [{"timestamp": datetime.now(timezone.utc).isoformat(), "sampledValue": [
                    {"value": "13000", "unit": "Wh"},
                    {"value": "11000", "unit": "W", "measurand": "Power.Active.Import"},
                ]}],
            }
            assert call("MeterValues", {**reading, "transactionId": session_id + 1})[2] == "SecurityError"
            with closing(session_updates(session_id, 2)) as stream:
                assert next(stream).startswith("event: changed")
                assert call("MeterValues", reading)[0] == 3
                assert next(stream).startswith("event: changed")
            assert call("MeterValues", reading)[0] == 3
            stop = {"transactionId": session_id, "meterStop": 14000, "timestamp": datetime.now(timezone.utc).isoformat()}
            assert call("StopTransaction", {**stop, "meterStop": 12500})[2] == "PropertyConstraintViolation"
            assert call("StopTransaction", stop)[0] == 3

        readings = browser.get(f"/api/v1/sessions/{session_id}/meter-readings", headers=get_auth_headers(test_customer))
        assert readings.status_code == 200
        assert readings.json()[0]["energy_kwh"] == "13.000"

    with SessionLocal() as db:
        sample = db.scalars(select(MeterReading)).one()
        assert sample.energy_kwh == Decimal("13.000")
        assert sample.power_kw == Decimal("11.000")
        assert db.get(ChargingSession, session_id).status == "COMPLETED"
