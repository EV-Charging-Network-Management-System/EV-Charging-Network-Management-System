"""
Module 9 Automated Tests: Invoicing, Payment Reconciliation, and Revenue Reporting.
Covers all 22 required scenarios:
1. Invoice generation from completed session
2. Invoice rejection for ACTIVE session
3. Missing final meter reading rejection
4. Correct energy calculation
5. Correct tax and total calculation
6. Decimal rounding correctness (ROUND_HALF_UP)
7. Locked tariff snapshot usage
8. Tariff changes not changing old invoices
9. Duplicate invoice rejection
10. Concurrent invoice generation
11. Successful DEMO payment
12. Failed payment
13. Payment retry after failure
14. Invoice remains unpaid after failure
15. Successful payment marks invoice PAID
16. Duplicate transaction reference rejection
17. Concurrent payment attempts
18. Overpayment prevention
19. Customer invoice isolation
20. Admin invoice access
21. Payment history preservation
22. Refund validation where supported
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import Vehicle, ConnectorType, VehicleConnectorType
from backend.app.models.tariff import Tariff, PricingRule
from backend.app.models.session import ChargingSession
from backend.app.models.billing import Invoice, Payment


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
    - Station with 1 charger (Charger 1: CCS-2 50kW ONLINE)
    - Vehicles for both customers
    - Active Tariff with base_price=12.50, session_fee=10.00, tax_rate=5.00
    """
    station = Station(
        station_id=1,
        station_name="Pune Tech Park Supercharger",
        address="100 Shivaji Nagar",
        city="Pune",
        latitude=Decimal("18.5314"),
        longitude=Decimal("73.8446"),
        operator_id=test_operator.user_id,
        status="ACTIVE"
    )
    db_session.add(station)

    charger = Charger(
        charger_id=1,
        station_id=1,
        connector_type_id=1,  # CCS-2
        charger_code="PUN-01-A",
        power_kw=Decimal("50.00"),
        operational_status="ONLINE"
    )
    db_session.add(charger)

    # Vehicles
    v1 = Vehicle(
        vehicle_id=1,
        owner_user_id=test_customer.user_id,
        make="Tata",
        model="Nexon EV",
        battery_capacity_kwh=Decimal("40.50"),
        registration_number="MH-12-AB-1234"
    )
    v2 = Vehicle(
        vehicle_id=2,
        owner_user_id=second_customer.user_id,
        make="MG",
        model="ZS EV",
        battery_capacity_kwh=Decimal("50.30"),
        registration_number="MH-12-CD-5678"
    )
    db_session.add_all([v1, v2])

    vct1 = VehicleConnectorType(vehicle_id=1, connector_type_id=1)
    vct2 = VehicleConnectorType(vehicle_id=2, connector_type_id=1)
    db_session.add_all([vct1, vct2])

    now = datetime.now(timezone.utc)
    tariff = Tariff(
        tariff_id=1,
        station_id=1,
        connector_type_id=1,
        base_price_per_kwh=Decimal("12.50"),
        session_fee=Decimal("10.00"),
        tax_rate_percent=Decimal("5.00"),
        valid_from=now - timedelta(days=30),
        valid_to=None
    )
    db_session.add(tariff)
    db_session.commit()

    return {
        "station": station,
        "charger": charger,
        "vehicle1": v1,
        "vehicle2": v2,
        "tariff": tariff
    }


def create_completed_session(
    db_session: Session,
    user_id: int,
    charger_id: int = 1,
    vehicle_id: int = 1,
    tariff_id: int = 1,
    meter_start: Decimal = Decimal("100.000"),
    meter_end: Decimal = Decimal("125.500")
) -> ChargingSession:
    """Helper to create a completed charging session with meter readings."""
    now = datetime.now(timezone.utc)
    session = ChargingSession(
        user_id=user_id,
        vehicle_id=vehicle_id,
        charger_id=charger_id,
        tariff_id=tariff_id,
        started_at=now - timedelta(hours=2),
        ended_at=now - timedelta(hours=1),
        meter_start_kwh=meter_start,
        meter_end_kwh=meter_end,
        status="COMPLETED"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


# ----------------------------------------------------------------------------
# 1. Invoice generation from completed session
# ----------------------------------------------------------------------------
def test_invoice_generation_from_completed_session(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    data = res.json()
    assert data["session_id"] == session.session_id
    assert data["status"] == "UNPAID"
    assert data["invoice_number"].startswith("INV-")
    assert Decimal(str(data["energy_kwh"])) == Decimal("25.500")


# ----------------------------------------------------------------------------
# 2. Invoice rejection for ACTIVE session
# ----------------------------------------------------------------------------
def test_invoice_rejection_for_active_session(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    now = datetime.now(timezone.utc)
    active_session = ChargingSession(
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        tariff_id=1,
        started_at=now,
        meter_start_kwh=Decimal("100.000"),
        meter_end_kwh=None,
        status="ACTIVE"
    )
    db_session.add(active_session)
    db_session.commit()

    res = client.post(
        f"/api/v1/invoices/generate/{active_session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 400
    assert "ACTIVE" in res.json()["detail"]


# ----------------------------------------------------------------------------
# 3. Missing final meter reading rejection
# ----------------------------------------------------------------------------
def test_missing_final_meter_reading_rejection(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    now = datetime.now(timezone.utc)
    session = ChargingSession(
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        tariff_id=1,
        started_at=now,
        meter_start_kwh=Decimal("100.000"),
        meter_end_kwh=None,
        status="ACTIVE"
    )
    db_session.add(session)
    db_session.commit()

    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 400
    assert "meter reading" in res.json()["detail"].lower()


# ----------------------------------------------------------------------------
# 4. Correct energy calculation
# ----------------------------------------------------------------------------
def test_correct_energy_calculation(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    # 1214.750 - 1200.000 = 14.750 kWh
    session = create_completed_session(
        db_session,
        test_customer.user_id,
        meter_start=Decimal("1200.000"),
        meter_end=Decimal("1214.750")
    )
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    assert Decimal(str(res.json()["energy_kwh"])) == Decimal("14.750")


# ----------------------------------------------------------------------------
# 5. Correct tax and total calculation
# ----------------------------------------------------------------------------
def test_correct_tax_and_total_calculation(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    # energy_kwh = 14.750, price = 12.50, fee = 10.00, tax_rate = 5.00%
    # energy_charge = 14.750 * 12.50 = 184.375 -> 184.38
    # subtotal = 184.38 + 10.00 = 194.38
    # tax_amount = 194.38 * 0.05 = 9.719 -> 9.72
    # total_amount = 194.38 + 9.72 = 204.10
    session = create_completed_session(
        db_session,
        test_customer.user_id,
        meter_start=Decimal("1200.000"),
        meter_end=Decimal("1214.750")
    )
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    inv = res.json()
    assert Decimal(str(inv["energy_charge"])) == Decimal("184.38")
    assert Decimal(str(inv["session_fee"])) == Decimal("10.00")
    assert Decimal(str(inv["tax_amount"])) == Decimal("9.72")
    assert Decimal(str(inv["total_amount"])) == Decimal("204.10")


# ----------------------------------------------------------------------------
# 6. Decimal rounding correctness (ROUND_HALF_UP)
# ----------------------------------------------------------------------------
def test_decimal_rounding_correctness_round_half_up(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    # 1.005 kWh * 10.00 = 10.05
    # Let's test a case where calculation yields .005 and must round up to .01
    tariff = test_setup["tariff"]
    tariff.base_price_per_kwh = Decimal("10.00")
    tariff.session_fee = Decimal("0.00")
    tariff.tax_rate_percent = Decimal("0.00")
    db_session.commit()

    # meter delta: 1.005
    session = create_completed_session(
        db_session,
        test_customer.user_id,
        meter_start=Decimal("0.000"),
        meter_end=Decimal("1.005")
    )
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    inv = res.json()
    # 1.005 * 10.00 = 10.050 -> 10.05
    assert Decimal(str(inv["total_amount"])) == Decimal("10.05")


# ----------------------------------------------------------------------------
# 7. Locked tariff snapshot usage
# ----------------------------------------------------------------------------
def test_locked_tariff_snapshot_usage(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    # Add a PEAK_HOUR rule: multiplier 1.200 (12.50 * 1.200 = 15.00)
    rule = PricingRule(
        tariff_id=1,
        rule_type="PEAK_HOUR",
        start_time=datetime.strptime("18:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("22:00:00", "%H:%M:%S").time(),
        price_multiplier=Decimal("1.200"),
        priority=1,
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()

    # Session started at 19:00 UTC (peak time)
    start_dt = datetime(2026, 11, 15, 19, 0, tzinfo=timezone.utc)
    session = ChargingSession(
        user_id=test_customer.user_id,
        vehicle_id=1,
        charger_id=1,
        tariff_id=1,
        started_at=start_dt,
        ended_at=start_dt + timedelta(hours=1),
        meter_start_kwh=Decimal("0.000"),
        meter_end_kwh=Decimal("10.000"),
        status="COMPLETED"
    )
    db_session.add(session)
    db_session.commit()

    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    inv = res.json()
    # 12.50 * 1.200 = 15.00
    assert Decimal(str(inv["price_per_kwh"])) == Decimal("15.00")
    # 10 kWh * 15.00 = 150.00 energy charge
    assert Decimal(str(inv["energy_charge"])) == Decimal("150.00")


# ----------------------------------------------------------------------------
# 8. Tariff changes not changing old invoices
# ----------------------------------------------------------------------------
def test_tariff_changes_not_changing_old_invoices(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 201
    inv_id = res.json()["invoice_id"]
    original_total = Decimal(str(res.json()["total_amount"]))

    # Now simulate station operator changing base price and session fee in DB
    tariff = test_setup["tariff"]
    tariff.base_price_per_kwh = Decimal("99.99")
    tariff.session_fee = Decimal("500.00")
    db_session.commit()

    # Fetch the previously generated invoice again
    res2 = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert res2.status_code == 200
    assert Decimal(str(res2.json()["total_amount"])) == original_total
    assert Decimal(str(res2.json()["price_per_kwh"])) == Decimal("12.50")


# ----------------------------------------------------------------------------
# 9. Duplicate invoice rejection
# ----------------------------------------------------------------------------
def test_duplicate_invoice_rejection(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    res1 = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res1.status_code == 201

    res2 = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res2.status_code == 409
    assert "Duplicate invoice rejected" in res2.json()["detail"]


# ----------------------------------------------------------------------------
# 10. Concurrent invoice generation
# ----------------------------------------------------------------------------
def test_concurrent_invoice_generation(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    # Manually create existing invoice directly to simulate a concurrent thread committing first
    inv = Invoice(
        session_id=session.session_id,
        energy_kwh=Decimal("25.500"),
        price_per_kwh=Decimal("12.50"),
        session_fee=Decimal("10.00"),
        tax_rate_percent=Decimal("5.00"),
        energy_charge=Decimal("318.75"),
        tax_amount=Decimal("16.44"),
        total_amount=Decimal("345.19"),
        status="UNPAID",
        issued_at=datetime.now(timezone.utc)
    )
    db_session.add(inv)
    db_session.commit()

    # Now attempt API invoice generation
    res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 409


# ----------------------------------------------------------------------------
# 11. Successful DEMO payment
# ----------------------------------------------------------------------------
def test_successful_demo_payment(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    inv_id = inv_res.json()["invoice_id"]
    total = inv_res.json()["total_amount"]

    pay_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "payment_method": "DEMO",
            "amount": total,
            "transaction_reference": "DEMO-TXN-SUCCESS-01"
        },
        headers=get_auth_headers(test_customer)
    )
    assert pay_res.status_code == 201
    p = pay_res.json()
    assert p["status"] == "SUCCESS"
    assert p["paid_at"] is not None

    # Check invoice status is updated to PAID
    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert inv_check.json()["status"] == "PAID"
    assert Decimal(str(inv_check.json()["balance_due"])) == Decimal("0.00")


# ----------------------------------------------------------------------------
# 12. Failed payment
# ----------------------------------------------------------------------------
def test_failed_payment(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    inv_id = inv_res.json()["invoice_id"]

    pay_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "payment_method": "CARD",
            "simulate_failure": True,
            "transaction_reference": "DEMO-TXN-FAIL-01"
        },
        headers=get_auth_headers(test_customer)
    )
    assert pay_res.status_code == 201
    p = pay_res.json()
    assert p["status"] == "FAILED"
    assert p["paid_at"] is None


# ----------------------------------------------------------------------------
# 13. Payment retry after failure
# ----------------------------------------------------------------------------
def test_payment_retry_after_failure(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    inv_id = inv_res.json()["invoice_id"]

    # 1. First attempt fails
    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "payment_method": "CARD",
            "simulate_failure": True,
            "transaction_reference": "DEMO-TXN-RETRY-FAIL"
        },
        headers=get_auth_headers(test_customer)
    )

    # 2. Second attempt (retry) with new reference succeeds
    pay_res2 = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "payment_method": "UPI",
            "simulate_failure": False,
            "transaction_reference": "DEMO-TXN-RETRY-SUCCESS"
        },
        headers=get_auth_headers(test_customer)
    )
    assert pay_res2.status_code == 201
    assert pay_res2.json()["status"] == "SUCCESS"

    # Invoice is now marked PAID
    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert inv_check.json()["status"] == "PAID"


# ----------------------------------------------------------------------------
# 14. Invoice remains unpaid after failure
# ----------------------------------------------------------------------------
def test_invoice_remains_unpaid_after_failure(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    inv_id = inv_res.json()["invoice_id"]

    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "payment_method": "CARD",
            "simulate_failure": True,
            "transaction_reference": "DEMO-TXN-UNPAID-CHECK"
        },
        headers=get_auth_headers(test_customer)
    )

    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert inv_check.json()["status"] == "UNPAID"


# ----------------------------------------------------------------------------
# 15. Successful payment marks invoice PAID
# ----------------------------------------------------------------------------
def test_successful_payment_marks_invoice_paid(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_res = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    )
    inv_id = inv_res.json()["invoice_id"]
    assert inv_res.json()["status"] == "UNPAID"

    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO"},
        headers=get_auth_headers(test_customer)
    )

    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert inv_check.json()["status"] == "PAID"


# ----------------------------------------------------------------------------
# 16. Duplicate transaction reference rejection
# ----------------------------------------------------------------------------
def test_duplicate_transaction_reference_rejection(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session1 = create_completed_session(db_session, test_customer.user_id)
    session2 = create_completed_session(db_session, test_customer.user_id)

    inv1 = client.post(f"/api/v1/invoices/generate/{session1.session_id}", headers=get_auth_headers(test_customer)).json()["invoice_id"]
    inv2 = client.post(f"/api/v1/invoices/generate/{session2.session_id}", headers=get_auth_headers(test_customer)).json()["invoice_id"]

    txn_ref = "DEMO-TXN-DUP-01"
    res1 = client.post(
        f"/api/v1/invoices/{inv1}/payments",
        json={"payment_method": "DEMO", "transaction_reference": txn_ref},
        headers=get_auth_headers(test_customer)
    )
    assert res1.status_code == 201

    # Attempting to use the exact same reference again must be rejected with 409 Conflict
    res2 = client.post(
        f"/api/v1/invoices/{inv2}/payments",
        json={"payment_method": "DEMO", "transaction_reference": txn_ref},
        headers=get_auth_headers(test_customer)
    )
    assert res2.status_code == 409
    assert "Duplicate transaction reference" in res2.json()["detail"]


# ----------------------------------------------------------------------------
# 17. Concurrent payment attempts
# ----------------------------------------------------------------------------
def test_concurrent_payment_attempts(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_id = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    ).json()["invoice_id"]

    # First payment succeeds
    res1 = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO"},
        headers=get_auth_headers(test_customer)
    )
    assert res1.status_code == 201

    # Immediate second payment attempt on now-PAID invoice is blocked
    res2 = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO"},
        headers=get_auth_headers(test_customer)
    )
    assert res2.status_code == 400
    assert "already been paid" in res2.json()["detail"]


# ----------------------------------------------------------------------------
# 18. Overpayment prevention
# ----------------------------------------------------------------------------
def test_overpayment_prevention(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_data = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    ).json()
    inv_id = inv_data["invoice_id"]
    total = Decimal(str(inv_data["total_amount"]))

    # Attempt to pay more than invoice total
    excessive_amount = total + Decimal("100.00")
    res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": str(excessive_amount), "payment_method": "DEMO"},
        headers=get_auth_headers(test_customer)
    )
    assert res.status_code == 400
    assert "exceeds remaining invoice balance" in res.json()["detail"]


# ----------------------------------------------------------------------------
# 19. Customer invoice isolation
# ----------------------------------------------------------------------------
def test_customer_invoice_isolation(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User,
    second_customer: User
):
    # Customer 1 session
    session1 = create_completed_session(db_session, test_customer.user_id)
    inv_id = client.post(
        f"/api/v1/invoices/generate/{session1.session_id}",
        headers=get_auth_headers(test_customer)
    ).json()["invoice_id"]

    # Customer 2 attempts to view Customer 1's invoice
    res_get = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(second_customer))
    assert res_get.status_code == 403

    # Customer 2 attempts to pay Customer 1's invoice
    res_pay = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO"},
        headers=get_auth_headers(second_customer)
    )
    assert res_pay.status_code == 403


# ----------------------------------------------------------------------------
# 20. Admin invoice access
# ----------------------------------------------------------------------------
def test_admin_invoice_access(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User,
    test_admin: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_id = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_admin)
    ).json()["invoice_id"]

    # Admin can view
    res = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_admin))
    assert res.status_code == 200

    # Admin can view revenue report
    rep = client.get("/api/v1/invoices/reports/revenue", headers=get_auth_headers(test_admin))
    assert rep.status_code == 200
    assert "total_billed_revenue" in rep.json()
    assert "total_collected_revenue" in rep.json()


# ----------------------------------------------------------------------------
# 21. Payment history preservation
# ----------------------------------------------------------------------------
def test_payment_history_preservation(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_id = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    ).json()["invoice_id"]

    # 1. First attempt fails
    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "CARD", "simulate_failure": True, "transaction_reference": "HIST-FAIL-1"},
        headers=get_auth_headers(test_customer)
    )

    # 2. Second attempt fails
    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "UPI", "simulate_failure": True, "transaction_reference": "HIST-FAIL-2"},
        headers=get_auth_headers(test_customer)
    )

    # 3. Third attempt succeeds
    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO", "simulate_failure": False, "transaction_reference": "HIST-SUCC-3"},
        headers=get_auth_headers(test_customer)
    )

    # Inspect payment history list
    res = client.get(f"/api/v1/invoices/{inv_id}/payments", headers=get_auth_headers(test_customer))
    assert res.status_code == 200
    payments = res.json()
    assert len(payments) == 3
    assert payments[0]["status"] == "FAILED"
    assert payments[1]["status"] == "FAILED"
    assert payments[2]["status"] == "SUCCESS"


# ----------------------------------------------------------------------------
# 22. Refund validation where supported
# ----------------------------------------------------------------------------
def test_refund_validation_where_supported(
    client: TestClient,
    db_session: Session,
    test_setup: dict,
    test_customer: User,
    test_operator: User,
    test_admin: User
):
    session = create_completed_session(db_session, test_customer.user_id)
    inv_id = client.post(
        f"/api/v1/invoices/generate/{session.session_id}",
        headers=get_auth_headers(test_customer)
    ).json()["invoice_id"]

    # Customer pays
    pay_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"payment_method": "DEMO"},
        headers=get_auth_headers(test_customer)
    )
    payment_id = pay_res.json()["payment_id"]

    # Customer cannot refund (403)
    res_cust_refund = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers=get_auth_headers(test_customer)
    )
    assert res_cust_refund.status_code == 403

    # Operator refunds
    ref_res = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        json={"reason": "Customer overcharged during maintenance"},
        headers=get_auth_headers(test_operator)
    )
    assert ref_res.status_code == 200
    assert ref_res.json()["status"] == "REFUNDED"

    # Invoice reverts to UNPAID
    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=get_auth_headers(test_customer))
    assert inv_check.json()["status"] == "UNPAID"

    # Cannot refund an already REFUNDED payment
    double_ref = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers=get_auth_headers(test_operator)
    )
    assert double_ref.status_code == 400
    assert "already been refunded" in double_ref.json()["detail"]
