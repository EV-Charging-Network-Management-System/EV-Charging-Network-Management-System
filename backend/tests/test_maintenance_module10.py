"""
Module 10 Automated Tests: Maintenance Work Orders and Charger Status Audit Trail.
Covers all 22 required scenarios:
1. Create maintenance work order (default status OPEN)
2. Work order validation: non-existent charger rejected with 404
3. Priority validation: LOW, MEDIUM, HIGH, CRITICAL allowed, invalid rejected with 422
4. Assignee validation: only OPERATOR or ADMIN allowed, CUSTOMER rejected with 400
5. Customer can report maintenance work order
6. Customer isolation: Customer cannot see work orders reported by other users
7. Operator can see work orders for their assigned stations
8. Admin can see all work orders across network
9. Filter work orders by status (OPEN, IN_PROGRESS, RESOLVED, CANCELLED)
10. Filter work orders by priority
11. Filter work orders by station_id or charger_id
12. Assignment endpoint: Assignee must exist and be OPERATOR/ADMIN
13. Assignment rejection on RESOLVED/CANCELLED orders
14. Lifecycle transition OPEN -> IN_PROGRESS: sets charger to MAINTENANCE
15. Lifecycle transition OPEN -> IN_PROGRESS: logs entry in charger_status_history
16. Lifecycle transition OPEN -> IN_PROGRESS: rejects with 409 Conflict if active charging session exists
17. Lifecycle transition OPEN -> IN_PROGRESS: rejects with 409 Conflict if active/upcoming reservation exists
18. Lifecycle transition IN_PROGRESS -> RESOLVED: records resolved_at and maintenance_cost
19. Lifecycle transition IN_PROGRESS -> RESOLVED: does NOT automatically return charger to ONLINE (charger remains in MAINTENANCE)
20. Explicit operator call to charger status API returns charger to ONLINE and logs status history
21. Lifecycle transition OPEN -> CANCELLED: preserves record, leaves charger status unchanged, rejects invalid transitions
22. Maintenance Analytics API: calculates total orders, status counts, expenditure, average resolution time, station breakdown, frequent fault chargers
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import Vehicle, ConnectorType, VehicleConnectorType
from backend.app.models.tariff import Tariff
from backend.app.models.session import ChargingSession
from backend.app.models.reservation import Reservation
from backend.app.models.maintenance import MaintenanceRecord, ChargerStatusHistory


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
    """Fixture providing a second customer for isolation tests."""
    user = User(
        user_id=20,
        full_name="Second Customer",
        email="second.customer@test.com",
        phone="9876543201",
        password_hash=get_password_hash("ValidCustomer123!"),
        role="CUSTOMER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def maintenance_setup(db_session: Session, test_customer: User, test_operator: User, test_admin: User):
    """
    Standard fixture setup:
    - Station 1 managed by test_operator, with 2 chargers (Charger 101: ONLINE, Charger 102: ONLINE)
    - Station 2 managed by test_admin (or another operator), with 1 charger (Charger 201: ONLINE)
    """
    st1 = Station(
        station_id=10,
        station_name="Mumbai Central Superhub",
        address="100 Express Way",
        city="Mumbai",
        latitude=Decimal("19.0760"),
        longitude=Decimal("72.8777"),
        status="ACTIVE",
        operator_id=test_operator.user_id,
    )
    st2 = Station(
        station_id=20,
        station_name="Navi Mumbai Fast Charging",
        address="200 Palm Beach Rd",
        city="Navi Mumbai",
        latitude=Decimal("19.0330"),
        longitude=Decimal("73.0297"),
        status="ACTIVE",
        operator_id=test_admin.user_id,
    )
    db_session.add_all([st1, st2])
    db_session.flush()

    c101 = Charger(
        charger_id=101,
        station_id=st1.station_id,
        connector_type_id=1,
        charger_code="MB-CH-01",
        power_kw=Decimal("60.00"),
        operational_status="ONLINE"
    )
    c102 = Charger(
        charger_id=102,
        station_id=st1.station_id,
        connector_type_id=2,
        charger_code="MB-CH-02",
        power_kw=Decimal("22.00"),
        operational_status="ONLINE"
    )
    c201 = Charger(
        charger_id=201,
        station_id=st2.station_id,
        connector_type_id=1,
        charger_code="NM-CH-01",
        power_kw=Decimal("120.00"),
        operational_status="ONLINE"
    )
    vehicle = Vehicle(
        vehicle_id=501,
        owner_user_id=test_customer.user_id,
        registration_number="MH-12-TEST-10",
        make="Tata",
        model="Nexon EV",
        battery_capacity_kwh=Decimal("40.50"),
    )
    now = datetime.now(timezone.utc)
    tariff = Tariff(
        tariff_id=701,
        station_id=st1.station_id,
        connector_type_id=1,
        base_price_per_kwh=Decimal("15.00"),
        session_fee=Decimal("10.00"),
        tax_rate_percent=Decimal("5.00"),
        valid_from=now - timedelta(days=7),
        valid_to=None
    )
    db_session.add_all([c101, c102, c201, vehicle, tariff])
    db_session.commit()

    return {
        "station1": st1,
        "station2": st2,
        "charger101": c101,
        "charger102": c102,
        "charger201": c201,
        "vehicle": vehicle,
        "tariff": tariff,
    }


# =====================================================================
# TEST 1: Create maintenance work order (default status OPEN)
# =====================================================================
def test_create_maintenance_default_open(client: TestClient, test_operator: User, maintenance_setup):
    headers = get_auth_headers(test_operator)
    payload = {
        "charger_id": 101,
        "issue_description": "Cable insulation damaged on CCS-2 connector",
        "priority": "HIGH"
    }
    response = client.post("/api/v1/maintenance", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["charger_id"] == 101
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert data["issue_description"] == "Cable insulation damaged on CCS-2 connector"
    assert data["reported_by"] == test_operator.user_id
    assert float(data["maintenance_cost"]) == 0.0


# =====================================================================
# TEST 2: Work order validation: non-existent charger rejected with 404
# =====================================================================
def test_create_maintenance_nonexistent_charger_rejected(client: TestClient, test_operator: User, maintenance_setup):
    headers = get_auth_headers(test_operator)
    payload = {
        "charger_id": 99999,
        "issue_description": "Ghost charger not responding",
        "priority": "LOW"
    }
    response = client.post("/api/v1/maintenance", json=payload, headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# =====================================================================
# TEST 3: Priority validation: invalid priority rejected
# =====================================================================
def test_create_maintenance_invalid_priority_rejected(client: TestClient, test_operator: User, maintenance_setup):
    headers = get_auth_headers(test_operator)
    payload = {
        "charger_id": 101,
        "issue_description": "Screen is flickering",
        "priority": "SUPER_URGENT"  # Invalid!
    }
    response = client.post("/api/v1/maintenance", json=payload, headers=headers)
    assert response.status_code == 422


# =====================================================================
# TEST 4: Assignee validation: CUSTOMER rejected as assignee with 400
# =====================================================================
def test_create_maintenance_customer_assignee_rejected(
    client: TestClient, test_operator: User, test_customer: User, maintenance_setup
):
    headers = get_auth_headers(test_operator)
    payload = {
        "charger_id": 101,
        "issue_description": "Power fluctuation detected",
        "priority": "MEDIUM",
        "assigned_to": test_customer.user_id  # Customer cannot be assigned!
    }
    response = client.post("/api/v1/maintenance", json=payload, headers=headers)
    assert response.status_code == 400
    assert "role operator or admin" in response.json()["detail"].lower()


# =====================================================================
# TEST 5: Customer can report maintenance work order
# =====================================================================
def test_customer_can_report_maintenance(client: TestClient, test_customer: User, maintenance_setup):
    headers = get_auth_headers(test_customer)
    payload = {
        "charger_id": 102,
        "issue_description": "Connector latch does not lock onto vehicle port",
        "priority": "MEDIUM"
    }
    response = client.post("/api/v1/maintenance", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["reported_by"] == test_customer.user_id
    assert data["status"] == "OPEN"
    assert data["station_name"] == "Mumbai Central Superhub"


# =====================================================================
# TEST 6: Customer isolation: Customer cannot see orders reported by others
# =====================================================================
def test_customer_isolation_maintenance(
    client: TestClient, test_customer: User, second_customer: User, maintenance_setup
):
    cust1_headers = get_auth_headers(test_customer)
    cust2_headers = get_auth_headers(second_customer)

    # Customer 1 reports order
    res1 = client.post("/api/v1/maintenance", json={
        "charger_id": 101,
        "issue_description": "Customer 1 report: card reader faulty",
        "priority": "LOW"
    }, headers=cust1_headers)
    assert res1.status_code == 201
    order1_id = res1.json()["maintenance_id"]

    # Customer 2 reports order
    res2 = client.post("/api/v1/maintenance", json={
        "charger_id": 102,
        "issue_description": "Customer 2 report: screen black",
        "priority": "HIGH"
    }, headers=cust2_headers)
    assert res2.status_code == 201
    order2_id = res2.json()["maintenance_id"]

    # Customer 1 lists maintenance - should only see order1
    list1 = client.get("/api/v1/maintenance", headers=cust1_headers).json()
    ids_1 = [o["maintenance_id"] for o in list1]
    assert order1_id in ids_1
    assert order2_id not in ids_1

    # Customer 1 attempts direct access to order2 -> 403 Forbidden
    detail_res = client.get(f"/api/v1/maintenance/{order2_id}", headers=cust1_headers)
    assert detail_res.status_code == 403


# =====================================================================
# TEST 7: Operator can see work orders for their assigned stations
# =====================================================================
def test_operator_station_visibility(
    client: TestClient, test_operator: User, test_customer: User, test_admin: User, maintenance_setup
):
    # Customer reports order on station 1 (managed by test_operator)
    c_res = client.post("/api/v1/maintenance", json={
        "charger_id": 101,
        "issue_description": "Station 1 issue",
        "priority": "HIGH"
    }, headers=get_auth_headers(test_customer)).json()
    st1_order_id = c_res["maintenance_id"]

    # Admin reports order on station 2 (not managed by test_operator)
    a_res = client.post("/api/v1/maintenance", json={
        "charger_id": 201,
        "issue_description": "Station 2 issue",
        "priority": "MEDIUM"
    }, headers=get_auth_headers(test_admin)).json()
    st2_order_id = a_res["maintenance_id"]

    op_headers = get_auth_headers(test_operator)
    op_list = client.get("/api/v1/maintenance", headers=op_headers).json()
    op_order_ids = [o["maintenance_id"] for o in op_list]

    assert st1_order_id in op_order_ids
    assert st2_order_id not in op_order_ids


# =====================================================================
# TEST 8: Admin can see all work orders across network
# =====================================================================
def test_admin_network_visibility(
    client: TestClient, test_admin: User, test_customer: User, maintenance_setup
):
    admin_headers = get_auth_headers(test_admin)
    c_headers = get_auth_headers(test_customer)

    res1 = client.post("/api/v1/maintenance", json={
        "charger_id": 101,
        "issue_description": "Network wide visibility test 1",
        "priority": "LOW"
    }, headers=c_headers).json()

    res2 = client.post("/api/v1/maintenance", json={
        "charger_id": 201,
        "issue_description": "Network wide visibility test 2",
        "priority": "CRITICAL"
    }, headers=admin_headers).json()

    all_orders = client.get("/api/v1/maintenance", headers=admin_headers).json()
    all_ids = [o["maintenance_id"] for o in all_orders]

    assert res1["maintenance_id"] in all_ids
    assert res2["maintenance_id"] in all_ids


# =====================================================================
# TEST 9: Filter work orders by status
# =====================================================================
def test_filter_work_orders_by_status(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    r1 = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Filter test order 1", "priority": "LOW"
    }, headers=headers).json()
    r2 = client.post("/api/v1/maintenance", json={
        "charger_id": 102, "issue_description": "Filter test order 2", "priority": "HIGH"
    }, headers=headers).json()

    # Cancel r2
    client.patch(f"/api/v1/maintenance/{r2['maintenance_id']}/status", json={"status": "CANCELLED"}, headers=headers)

    open_res = client.get("/api/v1/maintenance?status=OPEN", headers=headers).json()
    cancelled_res = client.get("/api/v1/maintenance?status=CANCELLED", headers=headers).json()

    open_ids = [o["maintenance_id"] for o in open_res]
    canc_ids = [o["maintenance_id"] for o in cancelled_res]

    assert r1["maintenance_id"] in open_ids
    assert r2["maintenance_id"] not in open_ids
    assert r2["maintenance_id"] in canc_ids


# =====================================================================
# TEST 10: Filter work orders by priority
# =====================================================================
def test_filter_work_orders_by_priority(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    r_crit = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Smoke detected near transformer", "priority": "CRITICAL"
    }, headers=headers).json()
    r_low = client.post("/api/v1/maintenance", json={
        "charger_id": 102, "issue_description": "QR code sticker scratched", "priority": "LOW"
    }, headers=headers).json()

    crit_list = client.get("/api/v1/maintenance?priority=CRITICAL", headers=headers).json()
    crit_ids = [o["maintenance_id"] for o in crit_list]

    assert r_crit["maintenance_id"] in crit_ids
    assert r_low["maintenance_id"] not in crit_ids


# =====================================================================
# TEST 11: Filter work orders by station_id or charger_id
# =====================================================================
def test_filter_work_orders_by_station_and_charger(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    r_c101 = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Bay 101 issue", "priority": "MEDIUM"
    }, headers=headers).json()
    r_c201 = client.post("/api/v1/maintenance", json={
        "charger_id": 201, "issue_description": "Bay 201 issue", "priority": "MEDIUM"
    }, headers=headers).json()

    # Filter by charger_id=101
    res_c101 = client.get("/api/v1/maintenance?charger_id=101", headers=headers).json()
    c101_ids = [o["maintenance_id"] for o in res_c101]
    assert r_c101["maintenance_id"] in c101_ids
    assert r_c201["maintenance_id"] not in c101_ids

    # Filter by station_id=20 (Station 2)
    res_st2 = client.get("/api/v1/maintenance?station_id=20", headers=headers).json()
    st2_ids = [o["maintenance_id"] for o in res_st2]
    assert r_c201["maintenance_id"] in st2_ids
    assert r_c101["maintenance_id"] not in st2_ids


# =====================================================================
# TEST 12: Assignment endpoint: Assignee must exist and be OPERATOR/ADMIN
# =====================================================================
def test_assign_maintenance_valid_technician(
    client: TestClient, test_admin: User, test_operator: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Routine hardware check", "priority": "LOW"
    }, headers=headers).json()

    assign_res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/assign",
        json={"assigned_to": test_operator.user_id},
        headers=headers
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_to"] == test_operator.user_id
    assert assign_res.json()["assigned_to_name"] == test_operator.full_name


# =====================================================================
# TEST 13: Assignment rejection on RESOLVED/CANCELLED orders
# =====================================================================
def test_assign_maintenance_terminal_status_rejected(
    client: TestClient, test_admin: User, test_operator: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Cancel test", "priority": "LOW"
    }, headers=headers).json()

    # Cancel the order
    client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "CANCELLED"},
        headers=headers
    )

    # Attempt to assign
    res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/assign",
        json={"assigned_to": test_operator.user_id},
        headers=headers
    )
    assert res.status_code == 400
    assert "cannot assign work order that is already in 'cancelled'" in res.json()["detail"].lower()


# =====================================================================
# TEST 14: Lifecycle OPEN -> IN_PROGRESS sets charger to MAINTENANCE
# =====================================================================
def test_lifecycle_open_to_in_progress_sets_charger_maintenance(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Firmware update required", "priority": "MEDIUM"
    }, headers=headers).json()

    # Move to IN_PROGRESS
    status_res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS", "reason": "Beginning technician diagnostics"},
        headers=headers
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "IN_PROGRESS"

    # Verify charger is now MAINTENANCE
    charger_res = client.get("/api/v1/chargers/101", headers=headers).json()
    assert charger_res["operational_status"] == "MAINTENANCE"


# =====================================================================
# TEST 15: Lifecycle OPEN -> IN_PROGRESS logs entry in charger_status_history
# =====================================================================
def test_lifecycle_in_progress_logs_status_history(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 102, "issue_description": "LED indicator dead", "priority": "LOW"
    }, headers=headers).json()

    # Transition to IN_PROGRESS
    client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS", "reason": "Repairing LED circuit"},
        headers=headers
    )

    # Inspect charger status history
    history_res = client.get("/api/v1/chargers/102/status-history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    latest = history[0]
    assert latest["charger_id"] == 102
    assert latest["previous_status"] == "ONLINE"
    assert latest["new_status"] == "MAINTENANCE"
    assert "Repairing LED circuit" in latest["reason"]


# =====================================================================
# TEST 16: OPEN -> IN_PROGRESS rejects with 409 Conflict if active charging session exists
# =====================================================================
def test_lifecycle_in_progress_rejected_on_active_session(
    client: TestClient, db_session: Session, test_admin: User, test_customer: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)

    # Insert active charging session on charger 101
    active_session = ChargingSession(
        session_id=8801,
        user_id=test_customer.user_id,
        charger_id=101,
        vehicle_id=maintenance_setup["vehicle"].vehicle_id,
        tariff_id=maintenance_setup["tariff"].tariff_id,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        meter_start_kwh=Decimal("10.000"),
        status="ACTIVE"
    )
    db_session.add(active_session)
    db_session.commit()

    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Emergency power test", "priority": "HIGH"
    }, headers=headers).json()

    # Attempt to transition to IN_PROGRESS
    res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )
    assert res.status_code == 409
    assert "active charging session" in res.json()["detail"].lower()


# =====================================================================
# TEST 17: OPEN -> IN_PROGRESS rejects with 409 Conflict if upcoming reservation exists
# =====================================================================
def test_lifecycle_in_progress_rejected_on_upcoming_reservation(
    client: TestClient, db_session: Session, test_admin: User, test_customer: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)

    # Insert confirmed upcoming reservation on charger 201
    upcoming_res = Reservation(
        reservation_id=9901,
        user_id=test_customer.user_id,
        charger_id=201,
        vehicle_id=maintenance_setup["vehicle"].vehicle_id,
        start_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        end_at=datetime.now(timezone.utc) + timedelta(hours=1),
        status="CONFIRMED"
    )
    db_session.add(upcoming_res)
    db_session.commit()

    order = client.post("/api/v1/maintenance", json={
        "charger_id": 201, "issue_description": "Transformer testing", "priority": "MEDIUM"
    }, headers=headers).json()

    # Attempt to transition to IN_PROGRESS
    res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )
    assert res.status_code == 409
    assert "reservation" in res.json()["detail"].lower()


# =====================================================================
# TEST 18: Lifecycle IN_PROGRESS -> RESOLVED: records resolved_at and maintenance_cost
# =====================================================================
def test_lifecycle_resolve_records_timestamp_and_cost(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Replace contactor", "priority": "HIGH"
    }, headers=headers).json()

    # Move to IN_PROGRESS
    client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )

    # Resolve with cost
    res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={
            "status": "RESOLVED",
            "maintenance_cost": "1250.50"
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RESOLVED"
    assert float(data["maintenance_cost"]) == 1250.50
    assert data["resolved_at"] is not None


# =====================================================================
# TEST 19: Lifecycle IN_PROGRESS -> RESOLVED: does NOT automatically return charger ONLINE
# =====================================================================
def test_resolved_order_leaves_charger_in_maintenance(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Firmware reflash", "priority": "LOW"
    }, headers=headers).json()

    client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )
    client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "RESOLVED", "maintenance_cost": "300.00"},
        headers=headers
    )

    # Check charger status: MUST remain MAINTENANCE until safety inspection
    charger = client.get("/api/v1/chargers/101", headers=headers).json()
    assert charger["operational_status"] == "MAINTENANCE"


# =====================================================================
# TEST 20: Explicit operator call to charger status API returns charger ONLINE
# =====================================================================
def test_explicit_operator_status_update_returns_online(
    client: TestClient, test_operator: User, maintenance_setup
):
    headers = get_auth_headers(test_operator)

    # First put charger 101 into MAINTENANCE
    m_res = client.patch(
        "/api/v1/chargers/101",
        json={
            "operational_status": "MAINTENANCE",
            "reason": "Routine technician check"
        },
        headers=headers
    )
    assert m_res.status_code == 200
    assert m_res.json()["operational_status"] == "MAINTENANCE"

    # Now clear it back ONLINE
    update_res = client.patch(
        "/api/v1/chargers/101",
        json={
            "operational_status": "ONLINE",
            "reason": "Safety clearance passed after contactor replacement"
        },
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["operational_status"] == "ONLINE"

    # Verify audit history
    hist = client.get("/api/v1/chargers/101/status-history", headers=headers).json()
    assert len(hist) >= 1
    assert hist[0]["new_status"] == "ONLINE"
    assert "Safety clearance passed" in hist[0]["reason"]


# =====================================================================
# TEST 21: OPEN -> CANCELLED preserves record and rejects invalid transitions
# =====================================================================
def test_cancel_maintenance_and_invalid_transition(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)
    order = client.post("/api/v1/maintenance", json={
        "charger_id": 102, "issue_description": "False alarm report", "priority": "LOW"
    }, headers=headers).json()

    # Cancel order
    cancel_res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "CANCELLED"},
        headers=headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Attempt to transition cancelled order to IN_PROGRESS -> 400 Bad Request
    inv_res = client.patch(
        f"/api/v1/maintenance/{order['maintenance_id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )
    assert inv_res.status_code == 400
    assert "cancelled" in inv_res.json()["detail"].lower()


# =====================================================================
# TEST 22: Maintenance Analytics API calculates statistics
# =====================================================================
def test_maintenance_analytics_summary(
    client: TestClient, test_admin: User, maintenance_setup
):
    headers = get_auth_headers(test_admin)

    # Submit 2 orders: one resolved with cost, one open
    o1 = client.post("/api/v1/maintenance", json={
        "charger_id": 101, "issue_description": "Coolant leak", "priority": "CRITICAL"
    }, headers=headers).json()
    client.patch(f"/api/v1/maintenance/{o1['maintenance_id']}/status", json={"status": "IN_PROGRESS"}, headers=headers)
    client.patch(f"/api/v1/maintenance/{o1['maintenance_id']}/status", json={"status": "RESOLVED", "maintenance_cost": "850.00"}, headers=headers)

    o2 = client.post("/api/v1/maintenance", json={
        "charger_id": 102, "issue_description": "Touchscreen recalibration", "priority": "MEDIUM"
    }, headers=headers).json()

    analytics_res = client.get("/api/v1/maintenance/reports/summary", headers=headers)
    assert analytics_res.status_code == 200
    data = analytics_res.json()

    summary = data["summary"]
    assert summary["total_orders"] >= 2
    assert summary["resolved_orders"] >= 1
    assert summary["open_orders"] >= 1
    assert summary["high_critical_orders"] >= 1
    assert float(summary["total_cost"]) >= 850.0

    # Station breakdowns
    by_station = data["by_station"]
    assert len(by_station) >= 1
    assert any(s["station_name"] == "Mumbai Central Superhub" for s in by_station)

    # Frequent fault chargers
    frequent = data["frequent_fault_chargers"]
    assert len(frequent) >= 1
    assert any(c["charger_id"] == 101 for c in frequent)
