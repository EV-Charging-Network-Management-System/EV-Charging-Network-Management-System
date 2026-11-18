"""
Vehicle Management Endpoints.
Implements vehicle registration, listing, retrieval, updates, and connector assignments.
"""

from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle, ConnectorType, VehicleConnectorType
from backend.app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleConnectorUpdate,
    ConnectorTypeResponse
)

router = APIRouter()


@router.get(
    "",
    response_model=List[VehicleResponse],
    summary="List vehicles"
)
def list_vehicles(
    owner_user_id: Optional[int] = Query(None, description="Filter by owner ID (Admin/Operator only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Vehicle]:
    """
    Retrieve vehicles.
    - CUSTOMER: Strictly returns only vehicles owned by the logged-in user.
    - ADMIN/OPERATOR: Can view all vehicles or filter by owner_user_id.
    """
    query = db.query(Vehicle)

    if current_user.role == "CUSTOMER":
        # Customers can ONLY view their own vehicles
        query = query.filter(Vehicle.owner_user_id == current_user.user_id)
    else:
        # Admin / Operator can optionally filter by owner
        if owner_user_id is not None:
            query = query.filter(Vehicle.owner_user_id == owner_user_id)

    vehicles = query.order_by(Vehicle.created_at.desc(), Vehicle.vehicle_id.desc()).all()
    return vehicles


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle"
)
def register_vehicle(
    vehicle_in: VehicleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Vehicle:
    """
    Register a new electric vehicle.
    Security: The owner is ALWAYS bound to the authenticated user. Untrusted owner_user_id input is rejected.
    """
    reg_clean = vehicle_in.registration_number.strip().upper()

    # 1. Uniqueness check for registration number
    existing_reg = db.query(Vehicle).filter(Vehicle.registration_number == reg_clean).first()
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vehicle with registration number '{reg_clean}' is already registered"
        )

    # 2. Battery capacity positive check
    if vehicle_in.battery_capacity_kwh is not None and vehicle_in.battery_capacity_kwh <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Battery capacity must be strictly greater than 0 kWh"
        )

    # 3. Validate connector type IDs if provided
    unique_connector_ids = list(dict.fromkeys(vehicle_in.connector_type_ids)) if vehicle_in.connector_type_ids else []
    if unique_connector_ids:
        found_connectors = db.query(ConnectorType).filter(
            ConnectorType.connector_type_id.in_(unique_connector_ids)
        ).all()
        found_ids = {c.connector_type_id for c in found_connectors}
        missing_ids = set(unique_connector_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector type ID(s) {sorted(list(missing_ids))} do not exist"
            )

    # 4. Create vehicle bound strictly to current_user
    new_vehicle = Vehicle(
        owner_user_id=current_user.user_id,
        registration_number=reg_clean,
        make=vehicle_in.make.strip(),
        model=vehicle_in.model.strip(),
        battery_capacity_kwh=vehicle_in.battery_capacity_kwh
    )
    db.add(new_vehicle)
    db.flush()

    # 5. Assign connector types
    for cid in unique_connector_ids:
        mapping = VehicleConnectorType(
            vehicle_id=new_vehicle.vehicle_id,
            connector_type_id=cid
        )
        db.add(mapping)

    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Get vehicle details"
)
def get_vehicle_details(
    vehicle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Vehicle:
    """
    Retrieve specific vehicle details.
    Ownership: Customers can only access their own vehicles.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    if current_user.role == "CUSTOMER" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this vehicle"
        )

    return vehicle


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle information"
)
def update_vehicle(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Vehicle:
    """
    Update vehicle specifications.
    Ownership: Customers can only update vehicles they own.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    if current_user.role == "CUSTOMER" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this vehicle"
        )

    # If updating registration number, check for duplicates
    if vehicle_in.registration_number is not None:
        new_reg = vehicle_in.registration_number.strip().upper()
        if new_reg != vehicle.registration_number:
            existing = db.query(Vehicle).filter(
                Vehicle.registration_number == new_reg,
                Vehicle.vehicle_id != vehicle_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Registration number '{new_reg}' is already in use by another vehicle"
                )
            vehicle.registration_number = new_reg

    if vehicle_in.make is not None:
        vehicle.make = vehicle_in.make.strip()

    if vehicle_in.model is not None:
        vehicle.model = vehicle_in.model.strip()

    if vehicle_in.battery_capacity_kwh is not None:
        if vehicle_in.battery_capacity_kwh <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Battery capacity must be strictly greater than 0 kWh"
            )
        vehicle.battery_capacity_kwh = vehicle_in.battery_capacity_kwh

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get(
    "/{vehicle_id}/connectors",
    response_model=List[ConnectorTypeResponse],
    summary="Get connectors supported by vehicle"
)
def get_vehicle_connectors(
    vehicle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ConnectorType]:
    """
    List all connector types supported by a specific vehicle.
    Ownership: Customer access is restricted to their own vehicles.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    if current_user.role == "CUSTOMER" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access connectors for this vehicle"
        )

    return vehicle.connector_types


@router.put(
    "/{vehicle_id}/connectors",
    response_model=List[ConnectorTypeResponse],
    summary="Update connectors supported by vehicle"
)
def update_vehicle_connectors(
    vehicle_id: int,
    connector_in: VehicleConnectorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ConnectorType]:
    """
    Replace the connector types supported by a vehicle.
    - Validates ownership.
    - Prevents duplicate mappings.
    - Validates all connector IDs exist.
    - Performs atomic update in a database transaction with rollback.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    if current_user.role == "CUSTOMER" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify connectors for this vehicle"
        )

    # Deduplicate requested connector type IDs
    unique_ids = list(dict.fromkeys(connector_in.connector_type_ids))

    if unique_ids:
        found_connectors = db.query(ConnectorType).filter(
            ConnectorType.connector_type_id.in_(unique_ids)
        ).all()
        found_ids = {c.connector_type_id for c in found_connectors}
        missing_ids = set(unique_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector type ID(s) {sorted(list(missing_ids))} do not exist"
            )

    # Atomic transaction replacement
    try:
        # Delete existing mappings
        db.query(VehicleConnectorType).filter(
            VehicleConnectorType.vehicle_id == vehicle_id
        ).delete(synchronize_session="fetch")

        # Insert new mappings
        for cid in unique_ids:
            db.add(VehicleConnectorType(vehicle_id=vehicle_id, connector_type_id=cid))

        db.commit()
        db.refresh(vehicle)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vehicle connector mappings: {str(exc)}"
        )

    return vehicle.connector_types

