"""
Station Management and Geolocation Endpoints.
Implements station CRUD, nearby radius search, and station charger creation.
"""

import math
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import (
    get_current_active_user,
    require_operator_or_admin,
    require_admin
)
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import ConnectorType
from backend.app.models.maintenance import ChargerStatusHistory
from backend.app.schemas.station import (
    StationCreate,
    StationUpdate,
    StationResponse,
    StationNearbyResponse,
    ChargerCreate,
    ChargerResponse
)

router = APIRouter()


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth's mean radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def build_station_response(station: Station) -> StationResponse:
    """Constructs a StationResponse including computed charger metrics."""
    chargers_list = station.chargers or []
    online_count = sum(1 for ch in chargers_list if ch.operational_status == "ONLINE")
    
    return StationResponse(
        station_id=station.station_id,
        operator_id=station.operator_id,
        station_name=station.station_name,
        address=station.address,
        city=station.city,
        latitude=station.latitude,
        longitude=station.longitude,
        opening_time=station.opening_time,
        closing_time=station.closing_time,
        status=station.status,
        chargers=chargers_list,
        total_chargers=len(chargers_list),
        online_chargers=online_count
    )


@router.get(
    "",
    response_model=List[StationResponse],
    summary="List charging stations"
)
def list_stations(
    city: Optional[str] = Query(None, description="Filter by city name"),
    status: Optional[str] = Query(None, description="Filter by station status (ACTIVE/INACTIVE)"),
    operator_id: Optional[int] = Query(None, description="Filter by station operator ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[StationResponse]:
    """
    List stations. Customers have read-only access.
    Supports filtering by city, status, and operator.
    """
    query = db.query(Station)

    if city:
        query = query.filter(Station.city.ilike(f"%{city.strip()}%"))
    if status:
        query = query.filter(Station.status == status.strip().upper())
    if operator_id is not None:
        query = query.filter(Station.operator_id == operator_id)

    stations = query.order_by(Station.station_id.asc()).all()
    return [build_station_response(s) for s in stations]


@router.get(
    "/nearby",
    response_model=List[StationNearbyResponse],
    summary="Search nearby charging stations by coordinates and radius"
)
def search_nearby_stations(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="User latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="User longitude"),
    radius_km: float = Query(10.0, gt=0.0, le=500.0, description="Search radius in kilometers"),
    connector_type_id: Optional[int] = Query(None, description="Filter by required connector standard"),
    min_power_kw: Optional[float] = Query(None, gt=0.0, description="Minimum charging power rating in kW"),
    operational_status: Optional[str] = Query(None, description="Filter charger status (e.g. ONLINE)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[StationNearbyResponse]:
    """
    Find nearby charging stations using pure mathematical Haversine spherical distance.
    No external paid APIs or PostGIS extensions required.
    Results are filtered by radius and compatibility criteria, and sorted ascending by distance.
    """
    # Fetch active stations with coordinates
    stations = db.query(Station).filter(
        Station.status == "ACTIVE",
        Station.latitude.isnot(None),
        Station.longitude.isnot(None)
    ).all()

    results: List[StationNearbyResponse] = []

    for s in stations:
        st_lat = float(s.latitude)
        st_lon = float(s.longitude)
        dist = haversine_distance_km(latitude, longitude, st_lat, st_lon)

        if dist > radius_km:
            continue

        chargers_list = s.chargers or []
        compatible = chargers_list

        if connector_type_id is not None:
            compatible = [ch for ch in compatible if ch.connector_type_id == connector_type_id]
        if min_power_kw is not None:
            compatible = [ch for ch in compatible if float(ch.power_kw) >= min_power_kw]
        if operational_status is not None:
            compatible = [ch for ch in compatible if ch.operational_status == operational_status.strip().upper()]

        # If connector or power filter is specified, only return station if it has compatible chargers
        if (connector_type_id is not None or min_power_kw is not None or operational_status is not None) and not compatible:
            continue

        base_res = build_station_response(s)
        results.append(
            StationNearbyResponse(
                **base_res.model_dump(),
                distance_km=dist,
                compatible_chargers=compatible
            )
        )

    # Sort ascending by distance
    results.sort(key=lambda item: item.distance_km)
    return results


@router.post(
    "",
    response_model=StationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new charging station"
)
def create_station(
    station_in: StationCreate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> StationResponse:
    """
    Create a new charging station.
    - OPERATOR: Station is bound strictly to the authenticated operator's user_id.
    - ADMIN: Can assign any valid operator or leave unassigned.
    """
    # Determine operator_id
    if current_user.role == "OPERATOR":
        op_id = current_user.user_id
    else:  # ADMIN
        op_id = station_in.operator_id or current_user.user_id

    # If op_id is set, verify the operator user exists
    if op_id is not None:
        operator_user = db.query(User).filter(User.user_id == op_id).first()
        if not operator_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operator with ID {op_id} does not exist"
            )

    new_station = Station(
        operator_id=op_id,
        station_name=station_in.station_name.strip(),
        address=station_in.address.strip(),
        city=station_in.city.strip(),
        latitude=station_in.latitude,
        longitude=station_in.longitude,
        opening_time=station_in.opening_time,
        closing_time=station_in.closing_time,
        status=station_in.status
    )
    db.add(new_station)
    db.commit()
    db.refresh(new_station)
    return build_station_response(new_station)


@router.get(
    "/{station_id}",
    response_model=StationResponse,
    summary="Get charging station details"
)
def get_station_details(
    station_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StationResponse:
    """Retrieve full details of a charging station including all installed chargers."""
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging station with ID {station_id} not found"
        )
    return build_station_response(station)


@router.patch(
    "/{station_id}",
    response_model=StationResponse,
    summary="Update charging station details"
)
def update_station(
    station_id: int,
    station_in: StationUpdate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> StationResponse:
    """
    Update station specifications.
    - OPERATOR: Can update only their own stations.
    - ADMIN: Can update any station.
    """
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging station with ID {station_id} not found"
        )

    # Ownership check for operators
    if current_user.role == "OPERATOR" and station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operators can only manage stations assigned to them"
        )

    if station_in.station_name is not None:
        station.station_name = station_in.station_name.strip()
    if station_in.address is not None:
        station.address = station_in.address.strip()
    if station_in.city is not None:
        station.city = station_in.city.strip()
    if station_in.latitude is not None:
        station.latitude = station_in.latitude
    if station_in.longitude is not None:
        station.longitude = station_in.longitude
    if station_in.opening_time is not None:
        station.opening_time = station_in.opening_time
    if station_in.closing_time is not None:
        station.closing_time = station_in.closing_time
    if station_in.status is not None:
        station.status = station_in.status

    # Only admins can reassign station operator
    if station_in.operator_id is not None:
        if current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reassign station operators"
            )
        op_user = db.query(User).filter(User.user_id == station_in.operator_id).first()
        if not op_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operator with ID {station_in.operator_id} does not exist"
            )
        station.operator_id = station_in.operator_id

    db.commit()
    db.refresh(station)
    return build_station_response(station)


@router.post(
    "/{station_id}/chargers",
    response_model=ChargerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new charger to a station"
)
def add_charger_to_station(
    station_id: int,
    charger_in: ChargerCreate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> Charger:
    """
    Add a new charger to an existing station.
    - Validates station existence and operator ownership.
    - Validates connector type existence.
    - Validates positive power rating.
    - Enforces unique charger_code within the station.
    - Records initial status transition in charger_status_history.
    """
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {station_id} not found"
        )

    # Ownership check
    if current_user.role == "OPERATOR" and station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operators can only add chargers to their own stations"
        )

    # Validate connector type existence
    connector = db.query(ConnectorType).filter(
        ConnectorType.connector_type_id == charger_in.connector_type_id
    ).first()
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connector type with ID {charger_in.connector_type_id} does not exist"
        )

    # Validate duplicate charger_code in same station
    code_clean = charger_in.charger_code.strip().upper()
    existing_charger = db.query(Charger).filter(
        Charger.station_id == station_id,
        Charger.charger_code == code_clean
    ).first()
    if existing_charger:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Charger code '{code_clean}' already exists at this station"
        )

    # Create charger & record initial status history in atomic transaction
    initial_status = charger_in.operational_status or "ONLINE"
    new_charger = Charger(
        station_id=station_id,
        connector_type_id=charger_in.connector_type_id,
        charger_code=code_clean,
        power_kw=charger_in.power_kw,
        operational_status=initial_status
    )

    try:
        db.add(new_charger)
        db.flush()

        history_entry = ChargerStatusHistory(
            charger_id=new_charger.charger_id,
            previous_status=None,
            new_status=initial_status,
            changed_by=current_user.user_id,
            reason="Charger commissioned and added to station."
        )
        db.add(history_entry)
        db.commit()
        db.refresh(new_charger)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create charger: {str(exc)}"
        )

    return new_charger

