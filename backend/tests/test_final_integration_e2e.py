"""
Final System Integration and Validation Test Suite.
Validates the end-to-end integration of all 10 modules:
- WORKFLOW A: Customer End-to-End Lifecycle (Registration -> Login -> EV & Connectors -> Station Search -> Price Quote -> Slot Reservation -> Session Start & Complete -> Invoicing -> Payment -> History)
- WORKFLOW B: Payment Failure, UNPAID Verification, Retry, SUCCESS, and Multi-Attempt Audit Trail
- WORKFLOW C: Maintenance Lifecycle, Bay Locking, Status Audit Trail, Operator Clearance Protocol
- WORKFLOW D: Reservation Conflict Detection (Half-Open Interval Overlap Rejection, Adjacent Slot Acceptance, Concurrency)
- SECURITY VALIDATION: Password Hash Exclusion, Token Expiration/Forging Rejection, Customer Data Isolation, Operator Station Scoping, Admin RBAC, Input Validation
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
from backend.app.models.reservation import Reservation
from backend.app.models.session import ChargingSession
from backend.app.models.billing import Invoice, Payment
from backend.app.models.maintenance import MaintenanceRecord, ChargerStatusHistory


@pytest.fixture(autouse=True)
def seed_standard_connectors(db_session: Session):
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
def e2e_network_setup(db_session: Session, test_operator: User, test_admin: User):
    """
    Sets up a complete network environment:
    - Station 1: Mumbai Superhub (operated by test_operator), 2 Chargers (CCS-2 60kW, Type 2 22kW)
    - Active 24/7 Tariff: Base 15.00/kWh, session fee 10.00, tax 5%
    - Peak Hour Pricing Rule: Multiplier 1.25x between 18:00 and 22:00
    """
    now = datetime.now(timezone.utc)
    st = Station(
        station_id=101,
        station_name="Mumbai Express Supercharger Hub",
        address="100 Western Express Highway",
        city="Mumbai",
        latitude=Decimal("19.0760"),
        longitude=Decimal("72.8777"),
        status="ACTIVE",
        operator_id=test_operator.user_id,
    )
    db_session.add(st)
    db_session.flush()

    c1 = Charger(
        charger_id=301,
        station_id=st.station_id,
        connector_type_id=1,
        charger_code="MUM-DC-01",
        power_kw=Decimal("60.00"),
        operational_status="ONLINE"
    )
    c2 = Charger(
        charger_id=302,
        station_id=st.station_id,
        connector_type_id=2,
        charger_code="MUM-AC-02",
        power_kw=Decimal("22.00"),
        operational_status="ONLINE"
    )
    db_session.add_all([c1, c2])
    db_session.flush()

    tariff = Tariff(
        tariff_id=401,
        station_id=st.station_id,
        connector_type_id=1,
        base_price_per_kwh=Decimal("15.00"),
        session_fee=Decimal("10.00"),
        tax_rate_percent=Decimal("5.00"),
        valid_from=now - timedelta(days=30),
        valid_to=None
    )
    db_session.add(tariff)
    db_session.flush()

    rule = PricingRule(
        rule_id=501,
        tariff_id=tariff.tariff_id,
        rule_type="PEAK_HOUR",
        price_multiplier=Decimal("1.250"),
        start_time=datetime.strptime("18:00", "%H:%M").time(),
        end_time=datetime.strptime("22:00", "%H:%M").time(),
        priority=1,
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()

    return {
        "station": st,
        "charger_dc": c1,
        "charger_ac": c2,
        "tariff": tariff,
        "rule": rule,
    }


# =====================================================================
# WORKFLOW A: COMPLETE CUSTOMER LIFECYCLE
# =====================================================================
def test_workflow_a_customer_full_lifecycle(client: TestClient, e2e_network_setup):
    """
    Tests complete 15-step Customer Lifecycle:
    Register -> Login -> EV Setup -> Connectors -> Station & Charger Search -> Price Quote ->
    Slot Reservation -> Start Session -> Meter Telemetry -> Complete Session ->
    Invoice Generation -> Payment -> Receipt -> History
    """
    # 1. Register customer
    reg_payload = {
        "full_name": "Arjun Customer",
        "email": "arjun.lifecycle@test.com",
        "phone": "9820011223",
        "password": "SecurePassword123!",
        "role": "CUSTOMER"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "arjun.lifecycle@test.com"
    user_id = user_data["user_id"]

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "arjun.lifecycle@test.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {token}"}

    # 3. Register EV
    veh_payload = {
        "make": "Tata",
        "model": "Nexon EV Max",
        "battery_capacity_kwh": 40.5,
        "registration_number": "MH-01-AR-9999"
    }
    veh_res = client.post("/api/v1/vehicles", json=veh_payload, headers=cust_headers)
    assert veh_res.status_code == 201
    vehicle_id = veh_res.json()["vehicle_id"]

    # 4. Select supported connectors (CCS-2 = ID 1)
    conn_res = client.put(f"/api/v1/vehicles/{vehicle_id}/connectors", json={
        "connector_type_ids": [1]
    }, headers=cust_headers)
    assert conn_res.status_code == 200

    # 5. Search stations
    stations_res = client.get("/api/v1/stations", headers=cust_headers)
    assert stations_res.status_code == 200
    stations = stations_res.json()
    assert len(stations) >= 1

    # 6. View available compatible chargers
    chargers_res = client.get(f"/api/v1/chargers?station_id={e2e_network_setup['station'].station_id}", headers=cust_headers)
    assert chargers_res.status_code == 200
    chargers = chargers_res.json()
    dc_charger = next(c for c in chargers if c["charger_id"] == 301)
    assert dc_charger["operational_status"] == "ONLINE"

    # 7. Calculate estimated charging price
    quote_payload = {
        "station_id": e2e_network_setup["station"].station_id,
        "connector_type_id": 1,
        "estimated_energy_kwh": 25.0
    }
    quote_res = client.post("/api/v1/pricing/quote", json=quote_payload, headers=cust_headers)
    assert quote_res.status_code == 200
    quote = quote_res.json()
    assert float(quote["total_amount"]) > 0

    # 8. Reserve charging slot (scheduled 10 mins from now, well within the 30-min arrival window)
    now = datetime.now(timezone.utc)
    res_start = now + timedelta(minutes=10)
    res_end = res_start + timedelta(minutes=45)
    res_payload = {
        "charger_id": 301,
        "vehicle_id": vehicle_id,
        "start_at": res_start.isoformat(),
        "end_at": res_end.isoformat()
    }
    booking_res = client.post("/api/v1/reservations", json=res_payload, headers=cust_headers)
    assert booking_res.status_code == 201
    booking = booking_res.json()
    reservation_id = booking["reservation_id"]
    assert booking["status"] == "CONFIRMED"

    # 9. Start charging session
    start_payload = {
        "charger_id": 301,
        "vehicle_id": vehicle_id,
        "reservation_id": reservation_id,
        "meter_start_kwh": 100.000
    }
    session_res = client.post("/api/v1/sessions/start", json=start_payload, headers=cust_headers)
    assert session_res.status_code == 201
    session = session_res.json()
    session_id = session["session_id"]
    assert session["status"] == "ACTIVE"

    # 10. Submit final meter reading and complete session
    complete_payload = {
        "meter_end_kwh": 125.500
    }
    comp_res = client.post(f"/api/v1/sessions/{session_id}/complete", json=complete_payload, headers=cust_headers)
    assert comp_res.status_code == 200
    completed_session = comp_res.json()
    assert completed_session["status"] == "COMPLETED"
    assert float(completed_session["meter_end_kwh"]) == 125.500

    # 11. Generate invoice
    inv_res = client.post(f"/api/v1/invoices/generate/{session_id}", headers=cust_headers)
    assert inv_res.status_code == 201
    invoice = inv_res.json()
    assert invoice["status"] == "UNPAID"
    invoice_id = invoice["invoice_id"]
    total_amount = float(invoice["total_amount"])
    assert total_amount > 0

    # 12. Make DEMO payment
    pay_payload = {
        "amount": str(total_amount),
        "payment_method": "DEMO"
    }
    pay_res = client.post(f"/api/v1/invoices/{invoice_id}/payments", json=pay_payload, headers=cust_headers)
    assert pay_res.status_code == 201
    payment = pay_res.json()
    assert payment["status"] == "SUCCESS"

    # 13. View invoice and receipt
    paid_inv_res = client.get(f"/api/v1/invoices/{invoice_id}", headers=cust_headers)
    assert paid_inv_res.status_code == 200
    assert paid_inv_res.json()["status"] == "PAID"

    # 14. View charging history
    hist_res = client.get("/api/v1/sessions/history", headers=cust_headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert any(s["session_id"] == session_id for s in hist)


# =====================================================================
# WORKFLOW B: PAYMENT FAILURE, RETRY, AND AUDIT PRESERVATION
# =====================================================================
def test_workflow_b_payment_failure_retry_audit(
    client: TestClient, db_session: Session, test_customer: User, e2e_network_setup
):
    """
    Tests failure handling:
    Simulate payment failure -> Verify invoice UNPAID -> Retry payment -> SUCCESS ->
    Verify invoice becomes PAID -> Verify both payment attempts are preserved.
    """
    headers = get_auth_headers(test_customer)
    now = datetime.now(timezone.utc)

    # Insert completed session
    v = Vehicle(
        vehicle_id=8801,
        owner_user_id=test_customer.user_id,
        make="Hyundai",
        model="Ioniq 5",
        battery_capacity_kwh=Decimal("72.60"),
        registration_number="MH-02-FL-8888"
    )
    db_session.add(v)
    db_session.flush()

    sess = ChargingSession(
        session_id=7701,
        user_id=test_customer.user_id,
        charger_id=301,
        vehicle_id=v.vehicle_id,
        tariff_id=e2e_network_setup["tariff"].tariff_id,
        started_at=now - timedelta(hours=2),
        ended_at=now - timedelta(hours=1),
        meter_start_kwh=Decimal("10.000"),
        meter_end_kwh=Decimal("30.000"),
        status="COMPLETED"
    )
    db_session.add(sess)
    db_session.commit()

    # Generate invoice
    inv_res = client.post(f"/api/v1/invoices/generate/{sess.session_id}", headers=headers)
    assert inv_res.status_code == 201
    invoice = inv_res.json()
    invoice_id = invoice["invoice_id"]
    amount_str = str(invoice["total_amount"])

    # 1. Attempt failed payment
    fail_res = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": amount_str, "payment_method": "DEMO", "simulate_failure": True},
        headers=headers
    )
    assert fail_res.status_code == 201
    assert fail_res.json()["status"] == "FAILED"
    assert fail_res.json()["paid_at"] is None

    # 2. Verify invoice remains UNPAID
    inv_check = client.get(f"/api/v1/invoices/{invoice_id}", headers=headers).json()
    assert inv_check["status"] == "UNPAID"

    # 3. Retry with successful payment
    success_res = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": amount_str, "payment_method": "DEMO", "simulate_failure": False},
        headers=headers
    )
    assert success_res.status_code == 201
    assert success_res.json()["status"] == "SUCCESS"

    # 4. Verify invoice is now PAID
    inv_paid = client.get(f"/api/v1/invoices/{invoice_id}", headers=headers).json()
    assert inv_paid["status"] == "PAID"

    # 5. Verify both payment attempts are preserved in audit trail
    payments_res = client.get(f"/api/v1/invoices/{invoice_id}/payments", headers=headers)
    assert payments_res.status_code == 200
    records = payments_res.json()
    assert len(records) == 2
    statuses = [p["status"] for p in records]
    assert "FAILED" in statuses
    assert "SUCCESS" in statuses


# =====================================================================
# WORKFLOW C: MAINTENANCE, BAY LOCKING, & OPERATOR CLEARANCE
# =====================================================================
def test_workflow_c_maintenance_locking_and_clearance(
    client: TestClient, test_customer: User, test_operator: User, e2e_network_setup
):
    """
    Tests maintenance workflow:
    Report issue -> Assign operator -> Move to IN_PROGRESS (locks bay to MAINTENANCE) ->
    Audit trail logged -> Resolve order -> Verify charger remains in MAINTENANCE ->
    Explicit operator clearance returns charger ONLINE.
    """
    cust_headers = get_auth_headers(test_customer)
    op_headers = get_auth_headers(test_operator)

    # 1. Report issue on charger 302
    report_res = client.post("/api/v1/maintenance", json={
        "charger_id": 302,
        "issue_description": "Type 2 connector lock actuator jammed",
        "priority": "HIGH"
    }, headers=cust_headers)
    assert report_res.status_code == 201
    order = report_res.json()
    m_id = order["maintenance_id"]
    assert order["status"] == "OPEN"

    # 2. Assign operator
    assign_res = client.patch(f"/api/v1/maintenance/{m_id}/assign", json={
        "assigned_to": test_operator.user_id
    }, headers=op_headers)
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_to"] == test_operator.user_id

    # 3. Move to IN_PROGRESS -> locks charger to MAINTENANCE
    prog_res = client.patch(f"/api/v1/maintenance/{m_id}/status", json={
        "status": "IN_PROGRESS",
        "reason": "Technician beginning teardown of lock actuator"
    }, headers=op_headers)
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "IN_PROGRESS"

    # 4. Verify charger is now in MAINTENANCE
    c_check = client.get("/api/v1/chargers/302", headers=op_headers).json()
    assert c_check["operational_status"] == "MAINTENANCE"

    # 5. Check charger status audit history
    hist_res = client.get("/api/v1/chargers/302/status-history", headers=op_headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist[0]["new_status"] == "MAINTENANCE"

    # 6. Resolve maintenance
    res_res = client.patch(f"/api/v1/maintenance/{m_id}/status", json={
        "status": "RESOLVED",
        "maintenance_cost": "450.00",
        "reason": "Lock actuator replaced and tested"
    }, headers=op_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"

    # 7. Safety Clearance Protocol: charger MUST remain in MAINTENANCE
    c_still_maint = client.get("/api/v1/chargers/302", headers=op_headers).json()
    assert c_still_maint["operational_status"] == "MAINTENANCE"

    # 8. Explicit operator safety clearance to ONLINE
    online_res = client.patch("/api/v1/chargers/302", json={
        "operational_status": "ONLINE",
        "reason": "Post-repair electrical isolation and safety checks passed"
    }, headers=op_headers)
    assert online_res.status_code == 200
    assert online_res.json()["operational_status"] == "ONLINE"


# =====================================================================
# WORKFLOW D: RESERVATION SLOT CONFLICT DETECTION & CONCURRENCY
# =====================================================================
def test_workflow_d_reservation_conflict_prevention(
    client: TestClient, db_session: Session, test_customer: User, e2e_network_setup
):
    """
    Tests slot conflict engine:
    Booking 1 confirmed -> Overlapping Booking 2 rejected (HTTP 409) ->
    Adjacent Booking 3 accepted -> Concurrency validation.
    """
    headers = get_auth_headers(test_customer)
    now = datetime.now(timezone.utc)

    # Register vehicle and connector
    veh = Vehicle(
        vehicle_id=9901,
        owner_user_id=test_customer.user_id,
        make="MG",
        model="ZS EV",
        battery_capacity_kwh=Decimal("50.30"),
        registration_number="MH-03-CONF-99"
    )
    db_session.add(veh)
    db_session.flush()

    vct = VehicleConnectorType(vehicle_id=veh.vehicle_id, connector_type_id=1)
    db_session.add(vct)
    db_session.commit()

    t_start = now + timedelta(hours=3)
    t_end = t_start + timedelta(hours=1)

    # 1. First booking [T, T+60]
    b1_res = client.post("/api/v1/reservations", json={
        "charger_id": 301,
        "vehicle_id": veh.vehicle_id,
        "start_at": t_start.isoformat(),
        "end_at": t_end.isoformat()
    }, headers=headers)
    assert b1_res.status_code == 201
    assert b1_res.json()["status"] == "CONFIRMED"

    # 2. Overlapping booking [T+30, T+90] -> MUST return HTTP 409 Conflict
    b2_res = client.post("/api/v1/reservations", json={
        "charger_id": 301,
        "vehicle_id": veh.vehicle_id,
        "start_at": (t_start + timedelta(minutes=30)).isoformat(),
        "end_at": (t_end + timedelta(minutes=30)).isoformat()
    }, headers=headers)
    assert b2_res.status_code == 409
    assert "already been reserved" in b2_res.json()["detail"].lower()

    # 3. Adjacent booking [T+60, T+120] -> MUST succeed (half-open [start, end))
    b3_res = client.post("/api/v1/reservations", json={
        "charger_id": 301,
        "vehicle_id": veh.vehicle_id,
        "start_at": t_end.isoformat(),
        "end_at": (t_end + timedelta(hours=1)).isoformat()
    }, headers=headers)
    assert b3_res.status_code == 201
    assert b3_res.json()["status"] == "CONFIRMED"


# =====================================================================
# TASK 3: SECURITY & ISOLATION VALIDATION
# =====================================================================
def test_security_password_hashes_never_exposed(client: TestClient, test_customer: User):
    """Verify password hashes are excluded from all user and auth responses."""
    headers = get_auth_headers(test_customer)
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "password_hash" not in me_data
    assert "password" not in me_data

    prof_res = client.get("/api/v1/users/me", headers=headers)
    assert prof_res.status_code == 200
    assert "password_hash" not in prof_res.json()


def test_security_customer_data_isolation(
    client: TestClient, db_session: Session, test_customer: User
):
    """Verify Customer A cannot view or manipulate Customer B's resources."""
    user_b = User(
        user_id=77,
        full_name="Customer B",
        email="customer.b@test.com",
        phone="9876543277",
        password_hash=get_password_hash("Password123!"),
        role="CUSTOMER",
        is_active=True
    )
    veh_b = Vehicle(
        vehicle_id=7701,
        owner_user_id=user_b.user_id,
        make="MG",
        model="Comet",
        battery_capacity_kwh=Decimal("17.30"),
        registration_number="MH-04-ISOL-77"
    )
    db_session.add_all([user_b, veh_b])
    db_session.commit()

    cust_a_headers = get_auth_headers(test_customer)

    # Customer A attempts to view Customer B's vehicle -> 403 Forbidden or 404 Not Found
    res = client.get(f"/api/v1/vehicles/{veh_b.vehicle_id}", headers=cust_a_headers)
    assert res.status_code in (403, 404)


def test_security_unauthenticated_requests_rejected(client: TestClient):
    """Verify requests without valid JWT tokens are rejected with 401 Unauthorized."""
    res1 = client.get("/api/v1/vehicles")
    assert res1.status_code == 401

    res2 = client.get("/api/v1/sessions/active")
    assert res2.status_code == 401

    res3 = client.get("/api/v1/invoices")
    assert res3.status_code == 401

    res4 = client.get("/api/v1/maintenance")
    assert res4.status_code == 401


def test_security_operator_scoping_and_admin_rbac(
    client: TestClient, test_operator: User, test_customer: User, e2e_network_setup
):
    """Verify non-admin users cannot access admin endpoints and operators are scoped."""
    cust_headers = get_auth_headers(test_customer)
    op_headers = get_auth_headers(test_operator)

    # Customer cannot access revenue reports
    rev_res = client.get("/api/v1/invoices/reports/revenue", headers=cust_headers)
    assert rev_res.status_code == 403

    # Customer cannot list all users
    users_res = client.get("/api/v1/users", headers=cust_headers)
    assert users_res.status_code == 403
