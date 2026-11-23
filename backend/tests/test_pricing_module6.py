"""
Automated Integration and Unit Tests for Module 6:
Tariffs and Dynamic Pricing Calculation Engine.

Tests run against an isolated in-memory SQLite database to ensure the live
PostgreSQL 18 database (ev_charging_network) and its 54 records remain 100% untouched.
"""

import pytest
from datetime import datetime, timezone, timedelta, time
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import ConnectorType, Vehicle
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
def test_station(db_session: Session, test_operator: User) -> Station:
    """Fixture providing a test station operated by test_operator."""
    station = Station(
        station_id=1,
        station_name="Tech Park Supercharger",
        address="100 Innovation Way",
        city="Pune",
        latitude=Decimal("18.52043"),
        longitude=Decimal("73.85674"),
        status="ACTIVE",
        operator_id=test_operator.user_id
    )
    db_session.add(station)
    db_session.commit()
    db_session.refresh(station)
    return station


@pytest.fixture
def other_station(db_session: Session, other_operator: User) -> Station:
    """Fixture providing a second station operated by other_operator."""
    station = Station(
        station_id=2,
        station_name="Metro Hub Charging Station",
        address="200 Central Ave",
        city="Mumbai",
        latitude=Decimal("19.0760"),
        longitude=Decimal("72.8777"),
        status="ACTIVE",
        operator_id=other_operator.user_id
    )
    db_session.add(station)
    db_session.commit()
    db_session.refresh(station)
    return station


# ============================================================================
# TASK 1: TARIFF MANAGEMENT TESTS
# ============================================================================

def test_tariff_creation_and_listing_admin_operator(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_admin: User,
    test_customer: User
):
    """Test tariff creation by operator (own station) and admin, and listing by customer."""
    now = datetime.now(timezone.utc)
    
    # 1. Operator creates station-wide tariff
    op_payload = {
        "station_id": test_station.station_id,
        "connector_type_id": None,
        "base_price_per_kwh": "12.50",
        "session_fee": "10.00",
        "tax_rate_percent": "5.00",
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_to": None
    }
    res = client.post("/api/v1/tariffs", json=op_payload, headers=get_auth_headers(test_operator))
    assert res.status_code == 201
    data = res.json()
    assert data["base_price_per_kwh"] == "12.50"
    assert data["station_name"] == "Tech Park Supercharger"
    assert data["connector_type_id"] is None

    # 2. Admin creates connector-specific tariff
    admin_payload = {
        "station_id": test_station.station_id,
        "connector_type_id": 1,
        "base_price_per_kwh": "15.00",
        "session_fee": "12.00",
        "tax_rate_percent": "5.00",
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_to": None
    }
    res2 = client.post("/api/v1/tariffs", json=admin_payload, headers=get_auth_headers(test_admin))
    assert res2.status_code == 201
    assert res2.json()["connector_type_id"] == 1

    # 3. Customer lists tariffs
    list_res = client.get(f"/api/v1/tariffs?station_id={test_station.station_id}", headers=get_auth_headers(test_customer))
    assert list_res.status_code == 200
    tariffs = list_res.json()
    assert len(tariffs) == 2


def test_customer_forbidden_from_creating_or_updating_tariff(
    client: TestClient,
    test_station: Station,
    test_customer: User
):
    """Ensure customers receive 403 Forbidden on tariff mutations."""
    now = datetime.now(timezone.utc)
    payload = {
        "station_id": test_station.station_id,
        "connector_type_id": None,
        "base_price_per_kwh": "10.00",
        "session_fee": "5.00",
        "tax_rate_percent": "5.00",
        "valid_from": now.isoformat()
    }
    res = client.post("/api/v1/tariffs", json=payload, headers=get_auth_headers(test_customer))
    assert res.status_code == 403


def test_operator_cannot_manage_other_operator_station_tariff(
    client: TestClient,
    other_station: Station,
    test_operator: User
):
    """Ensure operators cannot create tariffs for stations they do not operate."""
    now = datetime.now(timezone.utc)
    payload = {
        "station_id": other_station.station_id,
        "connector_type_id": None,
        "base_price_per_kwh": "11.00",
        "session_fee": "5.00",
        "tax_rate_percent": "5.00",
        "valid_from": now.isoformat()
    }
    res = client.post("/api/v1/tariffs", json=payload, headers=get_auth_headers(test_operator))
    assert res.status_code == 403
    assert "operate" in res.json()["detail"]


def test_tariff_temporal_overlap_rejection(
    client: TestClient,
    test_station: Station,
    test_operator: User
):
    """Ensure tariffs with overlapping validity periods for same station & connector are rejected with 409."""
    now = datetime.now(timezone.utc)
    t1 = {
        "station_id": test_station.station_id,
        "connector_type_id": 1,
        "base_price_per_kwh": "12.00",
        "session_fee": "10.00",
        "tax_rate_percent": "5.00",
        "valid_from": now.isoformat(),
        "valid_to": (now + timedelta(days=30)).isoformat()
    }
    res1 = client.post("/api/v1/tariffs", json=t1, headers=get_auth_headers(test_operator))
    assert res1.status_code == 201

    # Attempt to create overlapping tariff (starts 10 days later)
    t2 = {
        "station_id": test_station.station_id,
        "connector_type_id": 1,
        "base_price_per_kwh": "14.00",
        "session_fee": "10.00",
        "tax_rate_percent": "5.00",
        "valid_from": (now + timedelta(days=10)).isoformat(),
        "valid_to": (now + timedelta(days=40)).isoformat()
    }
    res2 = client.post("/api/v1/tariffs", json=t2, headers=get_auth_headers(test_operator))
    assert res2.status_code == 409
    assert "overlapping" in res2.json()["detail"].lower()


def test_tariff_invalid_constraints(
    client: TestClient,
    test_station: Station,
    test_operator: User
):
    """Verify validation: negative rates, valid_to before valid_from."""
    now = datetime.now(timezone.utc)
    # Negative base price
    res1 = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "-5.00",
        "session_fee": "0.00",
        "tax_rate_percent": "5.00",
        "valid_from": now.isoformat()
    }, headers=get_auth_headers(test_operator))
    assert res1.status_code == 422

    # valid_to <= valid_from
    res2 = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "session_fee": "0.00",
        "tax_rate_percent": "5.00",
        "valid_from": now.isoformat(),
        "valid_to": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))
    assert res2.status_code == 422


# ============================================================================
# TASK 2: PRICING RULES TESTS
# ============================================================================

def test_pricing_rule_creation_and_listing(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """Test creating PEAK_HOUR, OFF_PEAK, and HIGH_DEMAND rules."""
    now = datetime.now(timezone.utc)
    # Create tariff first
    t_res = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "session_fee": "5.00",
        "tax_rate_percent": "5.00",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))
    tariff_id = t_res.json()["tariff_id"]

    # 1. PEAK_HOUR rule
    peak_rule = {
        "tariff_id": tariff_id,
        "rule_type": "PEAK_HOUR",
        "start_time": "18:00:00",
        "end_time": "22:00:00",
        "price_multiplier": "1.250",
        "priority": 2
    }
    r1 = client.post("/api/v1/pricing-rules", json=peak_rule, headers=get_auth_headers(test_operator))
    assert r1.status_code == 201
    assert r1.json()["rule_type"] == "PEAK_HOUR"

    # 2. HIGH_DEMAND rule
    demand_rule = {
        "tariff_id": tariff_id,
        "rule_type": "HIGH_DEMAND",
        "demand_threshold_percent": "80.00",
        "price_multiplier": "1.300",
        "priority": 3
    }
    r2 = client.post("/api/v1/pricing-rules", json=demand_rule, headers=get_auth_headers(test_operator))
    assert r2.status_code == 201

    # 3. List rules
    list_res = client.get(f"/api/v1/pricing-rules?tariff_id={tariff_id}", headers=get_auth_headers(test_customer))
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2


def test_pricing_rule_invalid_parameters(
    client: TestClient,
    test_station: Station,
    test_operator: User
):
    """Test validation errors: missing times for PEAK_HOUR, invalid multiplier."""
    now = datetime.now(timezone.utc)
    t_res = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "valid_from": now.isoformat()
    }, headers=get_auth_headers(test_operator))
    tariff_id = t_res.json()["tariff_id"]

    # PEAK_HOUR without times
    res1 = client.post("/api/v1/pricing-rules", json={
        "tariff_id": tariff_id,
        "rule_type": "PEAK_HOUR",
        "price_multiplier": "1.200"
    }, headers=get_auth_headers(test_operator))
    assert res1.status_code == 422

    # HIGH_DEMAND without threshold
    res2 = client.post("/api/v1/pricing-rules", json={
        "tariff_id": tariff_id,
        "rule_type": "HIGH_DEMAND",
        "price_multiplier": "1.200"
    }, headers=get_auth_headers(test_operator))
    assert res2.status_code == 422

    # Negative multiplier
    res3 = client.post("/api/v1/pricing-rules", json={
        "tariff_id": tariff_id,
        "rule_type": "HIGH_DEMAND",
        "demand_threshold_percent": "50.00",
        "price_multiplier": "-1.000"
    }, headers=get_auth_headers(test_operator))
    assert res3.status_code == 422


# ============================================================================
# TASK 3 & 4: DYNAMIC PRICING CALCULATION ENGINE & QUOTE TESTS
# ============================================================================

def test_quote_base_tariff_standard_rate(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """
    Test standard pricing quote without active dynamic rules.
    Base price = 10.00, energy = 20 kWh, fee = 5.00, tax = 5%.
    Energy charge: 20 * 10 = 200.00
    Subtotal: 200 + 5 = 205.00
    Tax: 205 * 0.05 = 10.25
    Total: 215.25
    """
    now = datetime.now(timezone.utc)
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "session_fee": "5.00",
        "tax_rate_percent": "5.00",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))

    quote_req = {
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "20.00",
        "start_at": now.isoformat()
    }
    res = client.post("/api/v1/pricing/quote", json=quote_req, headers=get_auth_headers(test_customer))
    assert res.status_code == 200
    q = res.json()
    assert q["multiplier"] == "1.000"
    assert q["effective_rate_per_kwh"] == "10.00"
    assert q["energy_charge"] == "200.00"
    assert q["session_fee"] == "5.00"
    assert q["subtotal"] == "205.00"
    assert q["tax_amount"] == "10.25"
    assert q["total_amount"] == "215.25"
    assert q["applied_rule"] is None


def test_quote_connector_specific_tariff_precedence(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """Connector-specific tariff (15.00) takes precedence over station-wide tariff (10.00)."""
    now = datetime.now(timezone.utc)
    # Station-wide
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "connector_type_id": None,
        "base_price_per_kwh": "10.00",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))
    
    # Specific for connector 1 (CCS-2)
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "connector_type_id": 1,
        "base_price_per_kwh": "15.00",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))

    # Request with connector 1
    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "connector_type_id": 1,
        "estimated_energy_kwh": "10.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))
    assert res.status_code == 200
    assert res.json()["base_price_per_kwh"] == "15.00"


def test_quote_station_wide_fallback(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """When requested connector has no specific tariff, fall back to station-wide tariff."""
    now = datetime.now(timezone.utc)
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "connector_type_id": None,
        "base_price_per_kwh": "11.50",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "connector_type_id": 3,  # CHAdeMO (no specific tariff)
        "estimated_energy_kwh": "10.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))
    assert res.status_code == 200
    assert res.json()["base_price_per_kwh"] == "11.50"


def test_quote_peak_hour_rule_activation(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """PEAK_HOUR multiplier (1.200) applied during peak hours (18:00 - 22:00)."""
    now = datetime.now(timezone.utc)
    t_res = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "valid_from": (now - timedelta(days=7)).isoformat()
    }, headers=get_auth_headers(test_operator))
    t_id = t_res.json()["tariff_id"]

    client.post("/api/v1/pricing-rules", json={
        "tariff_id": t_id,
        "rule_type": "PEAK_HOUR",
        "start_time": "18:00:00",
        "end_time": "22:00:00",
        "price_multiplier": "1.200",
        "priority": 1
    }, headers=get_auth_headers(test_operator))

    # Test peak hour: 19:30
    peak_time = now.replace(hour=19, minute=30, second=0, microsecond=0)
    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": peak_time.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["multiplier"] == "1.200"
    assert q["effective_rate_per_kwh"] == "12.00"
    assert q["energy_charge"] == "120.00"
    assert q["applied_rule"]["rule_type"] == "PEAK_HOUR"


def test_quote_off_peak_rule_activation(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """OFF_PEAK discount multiplier (0.850) applied during night hours (00:00 - 06:00)."""
    now = datetime.now(timezone.utc)
    t_res = client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "valid_from": (now - timedelta(days=7)).isoformat()
    }, headers=get_auth_headers(test_operator))
    t_id = t_res.json()["tariff_id"]

    client.post("/api/v1/pricing-rules", json={
        "tariff_id": t_id,
        "rule_type": "OFF_PEAK",
        "start_time": "00:00:00",
        "end_time": "06:00:00",
        "price_multiplier": "0.850",
        "priority": 1
    }, headers=get_auth_headers(test_operator))

    # Test off-peak hour: 03:00
    off_peak_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": off_peak_time.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["multiplier"] == "0.850"
    assert q["effective_rate_per_kwh"] == "8.50"
    assert q["energy_charge"] == "85.00"
    assert q["applied_rule"]["rule_type"] == "OFF_PEAK"


def test_quote_high_demand_rule_activation(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User,
    db_session: Session
):
    """HIGH_DEMAND multiplier (1.400) applied when station demand meets/exceeds threshold."""
    now = datetime.now(timezone.utc)
    # Add charger online
    c1 = Charger(
        charger_id=10,
        station_id=test_station.station_id,
        charger_code="CH-01",
        connector_type_id=1,
        power_kw=Decimal("50.00"),
        operational_status="ONLINE"
    )
    # Vehicle
    veh = Vehicle(
        vehicle_id=1,
        owner_user_id=test_customer.user_id,
        registration_number="MH12AB1234",
        make="Tata",
        model="Nexon EV",
        battery_capacity_kwh=Decimal("40.50")
    )
    # Tariff
    tariff = Tariff(
        tariff_id=1,
        station_id=test_station.station_id,
        base_price_per_kwh=Decimal("10.00"),
        valid_from=now - timedelta(days=1)
    )
    rule = PricingRule(
        rule_id=1,
        tariff_id=1,
        rule_type="HIGH_DEMAND",
        demand_threshold_percent=Decimal("75.00"),
        price_multiplier=Decimal("1.400"),
        priority=1,
        is_active=True
    )
    # Active session on c1
    sess = ChargingSession(
        session_id=10,
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=10,
        tariff_id=1,
        started_at=now - timedelta(minutes=20),
        meter_start_kwh=Decimal("100.000"),
        status="ACTIVE"
    )
    db_session.add_all([c1, veh, tariff, rule, sess])
    db_session.commit()

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["station_demand_percent"] == "100.00"
    assert q["multiplier"] == "1.400"
    assert q["effective_rate_per_kwh"] == "14.00"
    assert q["applied_rule"]["rule_type"] == "HIGH_DEMAND"


def test_quote_high_demand_threshold_not_met(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User,
    db_session: Session
):
    """When demand is below threshold, multiplier remains standard 1.000."""
    now = datetime.now(timezone.utc)
    # 2 online chargers, 0 occupied -> demand = 0.00%
    c1 = Charger(charger_id=21, station_id=test_station.station_id, charger_code="CH-21", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    c2 = Charger(charger_id=22, station_id=test_station.station_id, charger_code="CH-22", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    tariff = Tariff(tariff_id=2, station_id=test_station.station_id, base_price_per_kwh=Decimal("10.00"), valid_from=now - timedelta(days=1))
    rule = PricingRule(rule_id=2, tariff_id=2, rule_type="HIGH_DEMAND", demand_threshold_percent=Decimal("50.00"), price_multiplier=Decimal("1.500"), priority=1, is_active=True)
    db_session.add_all([c1, c2, tariff, rule])
    db_session.commit()

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["station_demand_percent"] == "0.00"
    assert q["multiplier"] == "1.000"
    assert q["applied_rule"] is None


def test_quote_rule_priority_resolution(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User,
    db_session: Session
):
    """When multiple rules qualify (e.g. PEAK_HOUR priority 1 vs HIGH_DEMAND priority 2), higher priority wins."""
    target_time = datetime(2026, 11, 16, 19, 0, tzinfo=timezone.utc)
    # 1 charger occupied -> 100% demand
    c1 = Charger(charger_id=31, station_id=test_station.station_id, charger_code="CH-31", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    veh = Vehicle(vehicle_id=3, owner_user_id=test_customer.user_id, registration_number="MH12CD5678", make="Tata", model="Nexon EV", battery_capacity_kwh=Decimal("40.50"))
    tariff = Tariff(tariff_id=3, station_id=test_station.station_id, base_price_per_kwh=Decimal("10.00"), valid_from=target_time - timedelta(days=1))
    sess = ChargingSession(session_id=31, user_id=test_customer.user_id, vehicle_id=3, charger_id=31, tariff_id=3, started_at=target_time - timedelta(minutes=10), meter_start_kwh=Decimal("10.0"), status="ACTIVE")
    
    # Priority 1: PEAK_HOUR (1.200)
    rule_peak = PricingRule(rule_id=31, tariff_id=3, rule_type="PEAK_HOUR", start_time=time(18, 0), end_time=time(21, 0), price_multiplier=Decimal("1.200"), priority=1, is_active=True)
    # Priority 2: HIGH_DEMAND (1.500) -> Should win!
    rule_demand = PricingRule(rule_id=32, tariff_id=3, rule_type="HIGH_DEMAND", demand_threshold_percent=Decimal("80.00"), price_multiplier=Decimal("1.500"), priority=2, is_active=True)

    db_session.add_all([c1, veh, tariff, rule_peak, rule_demand, sess])
    db_session.commit()

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": target_time.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["multiplier"] == "1.500"
    assert q["applied_rule"]["rule_type"] == "HIGH_DEMAND"
    assert q["applied_rule"]["priority"] == 2


def test_quote_rule_collision_detection(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User,
    db_session: Session
):
    """When multiple conflicting rules share equal highest priority with different multipliers, reject with 409 Conflict."""
    target_time = datetime(2026, 11, 16, 19, 0, tzinfo=timezone.utc)
    c1 = Charger(charger_id=41, station_id=test_station.station_id, charger_code="CH-41", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    veh = Vehicle(vehicle_id=4, owner_user_id=test_customer.user_id, registration_number="MH12EF9012", make="MG", model="ZS EV", battery_capacity_kwh=Decimal("50.30"))
    tariff = Tariff(tariff_id=4, station_id=test_station.station_id, base_price_per_kwh=Decimal("10.00"), valid_from=target_time - timedelta(days=1))
    sess = ChargingSession(session_id=41, user_id=test_customer.user_id, vehicle_id=4, charger_id=41, tariff_id=4, started_at=target_time - timedelta(minutes=10), meter_start_kwh=Decimal("10.0"), status="ACTIVE")
    
    # Both priority = 2, but multipliers differ (1.200 vs 1.350)
    rule1 = PricingRule(rule_id=41, tariff_id=4, rule_type="PEAK_HOUR", start_time=time(18, 0), end_time=time(21, 0), price_multiplier=Decimal("1.200"), priority=2, is_active=True)
    rule2 = PricingRule(rule_id=42, tariff_id=4, rule_type="HIGH_DEMAND", demand_threshold_percent=Decimal("50.00"), price_multiplier=Decimal("1.350"), priority=2, is_active=True)

    db_session.add_all([c1, veh, tariff, rule1, rule2, sess])
    db_session.commit()

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "10.00",
        "start_at": target_time.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 409
    assert "collision" in res.json()["detail"].lower()


def test_quote_expired_or_future_tariff_rejection(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """When no active tariff exists for station at requested time, reject with 404."""
    now = datetime.now(timezone.utc)
    # Create tariff valid only in past
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "10.00",
        "valid_from": (now - timedelta(days=10)).isoformat(),
        "valid_to": (now - timedelta(days=5)).isoformat()
    }, headers=get_auth_headers(test_operator))

    # Request quote for now
    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "15.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 404
    assert "no active tariff found" in res.json()["detail"].lower()


def test_quote_with_zero_kwh(
    client: TestClient,
    test_station: Station,
    test_operator: User,
    test_customer: User
):
    """Quote with 0 kWh calculation: energy charge is 0, only session fee and tax applied."""
    now = datetime.now(timezone.utc)
    client.post("/api/v1/tariffs", json={
        "station_id": test_station.station_id,
        "base_price_per_kwh": "12.00",
        "session_fee": "20.00",
        "tax_rate_percent": "10.00",
        "valid_from": (now - timedelta(days=1)).isoformat()
    }, headers=get_auth_headers(test_operator))

    res = client.post("/api/v1/pricing/quote", json={
        "station_id": test_station.station_id,
        "estimated_energy_kwh": "0.00",
        "start_at": now.isoformat()
    }, headers=get_auth_headers(test_customer))

    assert res.status_code == 200
    q = res.json()
    assert q["energy_charge"] == "0.00"
    assert q["session_fee"] == "20.00"
    assert q["subtotal"] == "20.00"
    assert q["tax_amount"] == "2.00"
    assert q["total_amount"] == "22.00"


def test_station_demand_calculation_and_double_counting_avoidance(
    client: TestClient,
    test_station: Station,
    test_customer: User,
    db_session: Session
):
    """
    Test demand calculation:
    - 2 chargers online, 1 out of service.
    - Charger 1 has BOTH an active session AND a confirmed reservation.
    - Charger 2 is available.
    - Demand must be 50.00% (1 occupied / 2 online), verifying double counting avoidance.
    """
    now = datetime.now(timezone.utc)
    start_win = now
    end_win = now + timedelta(hours=1)

    c1 = Charger(charger_id=51, station_id=test_station.station_id, charger_code="CH-51", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    c2 = Charger(charger_id=52, station_id=test_station.station_id, charger_code="CH-52", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="ONLINE")
    c3 = Charger(charger_id=53, station_id=test_station.station_id, charger_code="CH-53", connector_type_id=1, power_kw=Decimal("50.00"), operational_status="OUT_OF_SERVICE")
    
    veh = Vehicle(vehicle_id=5, owner_user_id=test_customer.user_id, registration_number="MH12GH3456", make="Hyundai", model="Kona", battery_capacity_kwh=Decimal("39.20"))
    
    tariff = Tariff(tariff_id=5, station_id=test_station.station_id, base_price_per_kwh=Decimal("10.00"), valid_from=now - timedelta(days=1))

    # Active session on c1
    sess = ChargingSession(session_id=51, user_id=test_customer.user_id, vehicle_id=5, charger_id=51, tariff_id=5, started_at=now - timedelta(minutes=15), meter_start_kwh=Decimal("10.0"), status="ACTIVE")
    
    # Confirmed reservation on SAME charger c1 overlapping window
    resv = Reservation(reservation_id=51, user_id=test_customer.user_id, vehicle_id=5, charger_id=51, start_at=start_win, end_at=end_win, status="CONFIRMED")

    db_session.add_all([c1, c2, c3, veh, tariff, sess, resv])
    db_session.commit()

    res = client.get(
        "/api/v1/pricing/demand",
        params={
            "station_id": test_station.station_id,
            "start_at": start_win.isoformat(),
            "end_at": end_win.isoformat()
        },
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 200
    d = res.json()
    assert d["total_online_chargers"] == 2
    assert d["occupied_chargers"] == 1
    assert d["demand_percent"] == "50.00"
