"""
Automated Integration and Unit Tests for Module 5:
Station and Charger Management with Geolocation and Audit History.
Tests execute against an isolated in-memory SQLite database to guarantee that
the live PostgreSQL 18 database (ev_charging_network) and its 54 records remain 100% untouched.
"""

import pytest
from datetime import time
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import ConnectorType
from backend.app.models.maintenance import ChargerStatusHistory


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


# ======================================================================
# TASK 1: STATION MANAGEMENT TESTS
# ======================================================================

def test_list_stations(client: TestClient, test_customer: User, test_operator: User, db_session: Session):
    """Test listing stations with city and status filters."""
    # Seed 2 test stations
    s1 = Station(
        operator_id=test_operator.user_id,
        station_name="Bengaluru Central Hub",
        address="MG Road",
        city="Bengaluru",
        latitude=Decimal("12.9716"),
        longitude=Decimal("77.5946"),
        status="ACTIVE"
    )
    s2 = Station(
        operator_id=test_operator.user_id,
        station_name="Mysuru Expressway Hub",
        address="Mysuru Road",
        city="Mysuru",
        latitude=Decimal("12.2958"),
        longitude=Decimal("76.6394"),
        status="INACTIVE"
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    headers = get_auth_headers(test_customer)
    res = client.get("/api/v1/stations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2

    # City filter
    res_city = client.get("/api/v1/stations?city=Bengaluru", headers=headers)
    assert res_city.status_code == 200
    assert all("Bengaluru" in s["city"] for s in res_city.json())

    # Status filter
    res_status = client.get("/api/v1/stations?status=ACTIVE", headers=headers)
    assert res_status.status_code == 200
    assert all(s["status"] == "ACTIVE" for s in res_status.json())


def test_create_station_operator_success(client: TestClient, test_operator: User):
    """Test operator creates station, automatically bound to operator_id."""
    headers = get_auth_headers(test_operator)
    payload = {
        "station_name": "Whitefield Tech Park Hub",
        "address": "ITPB Main Road",
        "city": "Bengaluru",
        "latitude": 12.9698,
        "longitude": 77.7500,
        "opening_time": "06:00:00",
        "closing_time": "23:00:00",
        "status": "ACTIVE"
    }
    response = client.post("/api/v1/stations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["station_name"] == "Whitefield Tech Park Hub"
    assert data["operator_id"] == test_operator.user_id
    assert float(data["latitude"]) == 12.9698
    assert float(data["longitude"]) == 77.7500


def test_create_station_admin_success(client: TestClient, test_admin: User, test_operator: User):
    """Test admin creates station and assigns it to an operator."""
    headers = get_auth_headers(test_admin)
    payload = {
        "station_name": "Koramangala Supercharger",
        "address": "80 Feet Road",
        "city": "Bengaluru",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "operator_id": test_operator.user_id
    }
    response = client.post("/api/v1/stations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["operator_id"] == test_operator.user_id


def test_customer_cannot_create_station(client: TestClient, test_customer: User):
    """Test that customer role is rejected with 403 Forbidden when creating a station."""
    headers = get_auth_headers(test_customer)
    payload = {
        "station_name": "Unauthorized Station",
        "address": "Fake Road",
        "city": "Bengaluru"
    }
    response = client.post("/api/v1/stations", json=payload, headers=headers)
    assert response.status_code == 403


def test_create_station_invalid_latitude_longitude(client: TestClient, test_operator: User):
    """Test coordinate boundary validation (-90..90 for lat, -180..180 for lon)."""
    headers = get_auth_headers(test_operator)

    # Invalid latitude > 90
    bad_lat = {
        "station_name": "North Pole Hub",
        "address": "Arctic",
        "city": "Arctic",
        "latitude": 95.0,
        "longitude": 77.0
    }
    res1 = client.post("/api/v1/stations", json=bad_lat, headers=headers)
    assert res1.status_code == 422

    # Invalid longitude < -180
    bad_lon = {
        "station_name": "Pacific Hub",
        "address": "Ocean",
        "city": "Ocean",
        "latitude": 10.0,
        "longitude": -195.0
    }
    res2 = client.post("/api/v1/stations", json=bad_lon, headers=headers)
    assert res2.status_code == 422


def test_operator_station_ownership(
    client: TestClient,
    test_operator: User,
    other_operator: User
):
    """Test that operators can only update their own stations, not others'."""
    headers_op1 = get_auth_headers(test_operator)
    headers_op2 = get_auth_headers(other_operator)

    # Op 1 creates station
    res_create = client.post("/api/v1/stations", json={
        "station_name": "Op1 Station",
        "address": "Road 1",
        "city": "Bengaluru"
    }, headers=headers_op1)
    station_id = res_create.json()["station_id"]

    # Op 1 updates station -> Success
    res_update_op1 = client.patch(f"/api/v1/stations/{station_id}", json={
        "station_name": "Op1 Station Renamed"
    }, headers=headers_op1)
    assert res_update_op1.status_code == 200
    assert res_update_op1.json()["station_name"] == "Op1 Station Renamed"

    # Op 2 attempts update on Op 1's station -> 403 Forbidden
    res_update_op2 = client.patch(f"/api/v1/stations/{station_id}", json={
        "station_name": "Hacked Station Name"
    }, headers=headers_op2)
    assert res_update_op2.status_code == 403
    assert "Operators can only manage" in res_update_op2.json()["detail"]


def test_admin_can_update_any_station(
    client: TestClient,
    test_admin: User,
    test_operator: User
):
    """Test admin can update any station."""
    headers_op = get_auth_headers(test_operator)
    headers_admin = get_auth_headers(test_admin)

    res_create = client.post("/api/v1/stations", json={
        "station_name": "Op Station",
        "address": "Street",
        "city": "Pune"
    }, headers=headers_op)
    station_id = res_create.json()["station_id"]

    res_admin_update = client.patch(f"/api/v1/stations/{station_id}", json={
        "status": "INACTIVE"
    }, headers=headers_admin)
    assert res_admin_update.status_code == 200
    assert res_admin_update.json()["status"] == "INACTIVE"


# ======================================================================
# TASK 2: CHARGER MANAGEMENT TESTS
# ======================================================================

def test_add_charger_success(client: TestClient, test_operator: User):
    """Test operator successfully adds a charger to their station."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Indiranagar Charging Bay",
        "address": "100ft Road",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    payload = {
        "connector_type_id": 1,
        "charger_code": "IND-CCS-01",
        "power_kw": 60.0,
        "operational_status": "ONLINE"
    }
    ch_res = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload, headers=headers)
    assert ch_res.status_code == 201
    data = ch_res.json()
    assert data["charger_code"] == "IND-CCS-01"
    assert float(data["power_kw"]) == 60.0
    assert data["operational_status"] == "ONLINE"
    assert data["connector_type_id"] == 1


def test_add_duplicate_charger_code_rejected(client: TestClient, test_operator: User):
    """Test duplicate charger_code in same station fails with 409 Conflict."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Hebbal Station",
        "address": "Bellary Road",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    payload = {
        "connector_type_id": 1,
        "charger_code": "HEB-01",
        "power_kw": 50.0
    }
    res1 = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload, headers=headers)
    assert res1.status_code == 201

    res2 = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload, headers=headers)
    assert res2.status_code == 409
    assert "already exists at this station" in res2.json()["detail"]


def test_add_charger_invalid_power_rejected(client: TestClient, test_operator: User):
    """Test power rating <= 0 is rejected with 422 Unprocessable Entity."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Jayanagar Station",
        "address": "4th Block",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    payload_zero = {
        "connector_type_id": 1,
        "charger_code": "JAY-01",
        "power_kw": 0
    }
    res1 = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload_zero, headers=headers)
    assert res1.status_code == 422

    payload_neg = {
        "connector_type_id": 1,
        "charger_code": "JAY-02",
        "power_kw": -25.0
    }
    res2 = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload_neg, headers=headers)
    assert res2.status_code == 422


def test_add_charger_invalid_connector_rejected(client: TestClient, test_operator: User):
    """Test non-existent connector_type_id fails with 400 Bad Request."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Malleshwaram Hub",
        "address": "Sampige Road",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    payload = {
        "connector_type_id": 9999,
        "charger_code": "MAL-01",
        "power_kw": 50.0
    }
    res = client.post(f"/api/v1/stations/{station_id}/chargers", json=payload, headers=headers)
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


# ======================================================================
# TASK 3: STATUS TRANSITION & AUDIT HISTORY TESTS
# ======================================================================

def test_charger_status_transition_and_history(
    client: TestClient,
    test_operator: User,
    db_session: Session
):
    """Test updating charger status atomically inserts record into charger_status_history."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Electronic City Hub",
        "address": "Phase 1",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    ch_res = client.post(f"/api/v1/stations/{station_id}/chargers", json={
        "connector_type_id": 1,
        "charger_code": "EC-CCS-01",
        "power_kw": 120.0,
        "operational_status": "ONLINE"
    }, headers=headers)
    charger_id = ch_res.json()["charger_id"]

    # Transition from ONLINE to MAINTENANCE
    patch_res = client.patch(f"/api/v1/chargers/{charger_id}", json={
        "operational_status": "MAINTENANCE",
        "reason": "Routine cable and nozzle inspection"
    }, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["operational_status"] == "MAINTENANCE"

    # Query charger_status_history table directly
    history_entries = db_session.query(ChargerStatusHistory).filter(
        ChargerStatusHistory.charger_id == charger_id
    ).order_by(ChargerStatusHistory.history_id.asc()).all()

    assert len(history_entries) >= 2  # 1 from creation, 1 from transition
    latest_history = history_entries[-1]
    assert latest_history.previous_status == "ONLINE"
    assert latest_history.new_status == "MAINTENANCE"
    assert latest_history.changed_by == test_operator.user_id
    assert "Routine cable and nozzle inspection" in latest_history.reason


def test_get_station_details(client: TestClient, test_customer: User, test_operator: User):
    """Test retrieving details of a specific station and 404 for nonexistent."""
    headers = get_auth_headers(test_operator)
    s_res = client.post("/api/v1/stations", json={
        "station_name": "Detail Station",
        "address": "Detail Address",
        "city": "Bengaluru"
    }, headers=headers)
    station_id = s_res.json()["station_id"]

    # Customer fetches details
    headers_cust = get_auth_headers(test_customer)
    res = client.get(f"/api/v1/stations/{station_id}", headers=headers_cust)
    assert res.status_code == 200
    assert res.json()["station_id"] == station_id
    assert res.json()["station_name"] == "Detail Station"

    # Non-existent
    res_404 = client.get("/api/v1/stations/99999", headers=headers_cust)
    assert res_404.status_code == 404


def test_list_and_get_chargers(client: TestClient, test_operator: User, test_customer: User):
    """Test listing chargers with filters and retrieving specific charger details."""
    headers_op = get_auth_headers(test_operator)
    headers_cust = get_auth_headers(test_customer)

    s_res = client.post("/api/v1/stations", json={
        "station_name": "Filter Station",
        "address": "Filter Address",
        "city": "Bengaluru"
    }, headers=headers_op)
    station_id = s_res.json()["station_id"]

    ch1 = client.post(f"/api/v1/stations/{station_id}/chargers", json={
        "connector_type_id": 1,
        "charger_code": "FLT-01",
        "power_kw": 50.0,
        "operational_status": "ONLINE"
    }, headers=headers_op).json()

    ch2 = client.post(f"/api/v1/stations/{station_id}/chargers", json={
        "connector_type_id": 2,
        "charger_code": "FLT-02",
        "power_kw": 22.0,
        "operational_status": "MAINTENANCE"
    }, headers=headers_op).json()

    # List with station_id filter
    res = client.get(f"/api/v1/chargers?station_id={station_id}", headers=headers_cust)
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Filter by operational_status
    res_maint = client.get(f"/api/v1/chargers?operational_status=MAINTENANCE", headers=headers_cust)
    assert res_maint.status_code == 200
    codes = [c["charger_code"] for c in res_maint.json()]
    assert "FLT-02" in codes

    # Get single charger details
    res_single = client.get(f"/api/v1/chargers/{ch1['charger_id']}", headers=headers_cust)
    assert res_single.status_code == 200
    assert res_single.json()["charger_code"] == "FLT-01"

    # Non-existent charger
    res_404 = client.get("/api/v1/chargers/99999", headers=headers_cust)
    assert res_404.status_code == 404


def test_unauthorized_charger_modification_forbidden(
    client: TestClient,
    test_operator: User,
    other_operator: User,
    test_customer: User
):
    """Test customer and non-owner operator cannot modify a charger."""
    headers_op1 = get_auth_headers(test_operator)
    headers_op2 = get_auth_headers(other_operator)
    headers_cust = get_auth_headers(test_customer)

    s_res = client.post("/api/v1/stations", json={
        "station_name": "Op1 Station",
        "address": "Secret Road",
        "city": "Bengaluru"
    }, headers=headers_op1)
    station_id = s_res.json()["station_id"]

    ch_res = client.post(f"/api/v1/stations/{station_id}/chargers", json={
        "connector_type_id": 1,
        "charger_code": "SEC-01",
        "power_kw": 50.0
    }, headers=headers_op1)
    charger_id = ch_res.json()["charger_id"]

    # Customer attempts patch -> 403
    res_cust = client.patch(f"/api/v1/chargers/{charger_id}", json={"power_kw": 60.0}, headers=headers_cust)
    assert res_cust.status_code == 403

    # Other operator attempts patch -> 403
    res_op2 = client.patch(f"/api/v1/chargers/{charger_id}", json={"power_kw": 60.0}, headers=headers_op2)
    assert res_op2.status_code == 403



# ======================================================================
# TASK 4: GEOLOCATION AND NEARBY SEARCH TESTS
# ======================================================================

def test_nearby_stations_search_and_distance(
    client: TestClient,
    test_customer: User,
    test_operator: User,
    db_session: Session
):
    """
    Test finding nearby stations within radius, sorted ascending by distance.
    Uses known coordinates:
    - User reference point: Vidhana Soudha, Bengaluru (12.9797, 77.5906)
    - Station 1: MG Road (12.9756, 77.6066) ~ 1.8 km
    - Station 2: Whitefield (12.9698, 77.7500) ~ 17.3 km
    - Station 3: Mysuru (12.2958, 76.6394) ~ 128 km
    """
    s1 = Station(
        operator_id=test_operator.user_id,
        station_name="MG Road Hub",
        address="MG Road",
        city="Bengaluru",
        latitude=Decimal("12.9756"),
        longitude=Decimal("77.6066"),
        status="ACTIVE"
    )
    s2 = Station(
        operator_id=test_operator.user_id,
        station_name="Whitefield Hub",
        address="Whitefield",
        city="Bengaluru",
        latitude=Decimal("12.9698"),
        longitude=Decimal("77.7500"),
        status="ACTIVE"
    )
    s3 = Station(
        operator_id=test_operator.user_id,
        station_name="Mysuru Palace Hub",
        address="Sayyaji Rao Road",
        city="Mysuru",
        latitude=Decimal("12.2958"),
        longitude=Decimal("76.6394"),
        status="ACTIVE"
    )
    db_session.add_all([s1, s2, s3])
    db_session.flush()

    # Add chargers
    c1 = Charger(station_id=s1.station_id, connector_type_id=1, charger_code="MGR-01", power_kw=Decimal("60.0"), operational_status="ONLINE")
    c2 = Charger(station_id=s2.station_id, connector_type_id=2, charger_code="WFD-01", power_kw=Decimal("22.0"), operational_status="ONLINE")
    db_session.add_all([c1, c2])
    db_session.commit()

    headers = get_auth_headers(test_customer)

    # 1. Search radius 5 km -> Only MG Road Hub should be returned
    res_5km = client.get("/api/v1/stations/nearby?latitude=12.9797&longitude=77.5906&radius_km=5", headers=headers)
    assert res_5km.status_code == 200
    data_5km = res_5km.json()
    assert len(data_5km) == 1
    assert data_5km[0]["station_name"] == "MG Road Hub"
    assert data_5km[0]["distance_km"] < 3.0

    # 2. Search radius 25 km -> MG Road Hub and Whitefield Hub returned, sorted by distance
    res_25km = client.get("/api/v1/stations/nearby?latitude=12.9797&longitude=77.5906&radius_km=25", headers=headers)
    assert res_25km.status_code == 200
    data_25km = res_25km.json()
    assert len(data_25km) == 2
    assert data_25km[0]["distance_km"] <= data_25km[1]["distance_km"]
    assert data_25km[0]["station_name"] == "MG Road Hub"
    assert data_25km[1]["station_name"] == "Whitefield Hub"

    # 3. Search with connector_type_id=1 (CCS-2) -> Only MG Road Hub (Whitefield has Type 2)
    res_conn = client.get(
        "/api/v1/stations/nearby?latitude=12.9797&longitude=77.5906&radius_km=25&connector_type_id=1",
        headers=headers
    )
    assert res_conn.status_code == 200
    assert len(res_conn.json()) == 1
    assert res_conn.json()[0]["station_name"] == "MG Road Hub"

    # 4. Search with min_power_kw=50 -> Only MG Road Hub (60kW), Whitefield is 22kW
    res_power = client.get(
        "/api/v1/stations/nearby?latitude=12.9797&longitude=77.5906&radius_km=25&min_power_kw=50",
        headers=headers
    )
    assert res_power.status_code == 200
    assert len(res_power.json()) == 1
    assert res_power.json()[0]["station_name"] == "MG Road Hub"
