"""
Reservation Management and Slot Conflict Engine Endpoints.
Implements charger availability searching, transactional slot booking with row-locking,
exclusion conflict translation, RBAC reservation listing, and booking cancellation.
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from backend.app.api.pagination import PageParam
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.reservation import Reservation
from backend.app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    ReservationCancelResponse,
    ChargerAvailabilityResponse
)
from backend.app.services.reservation_service import (
    get_available_chargers_for_booking,
    create_reservation_transaction,
    cancel_reservation_transaction,
    format_reservation_response
)
from backend.app.services.pricing_service import normalize_datetime

router = APIRouter()


@router.get(
    "/availability",
    response_model=ChargerAvailabilityResponse,
    summary="Check charger availability for vehicle & slot"
)
def check_availability(
    station_id: int = Query(..., description="Target charging station ID"),
    vehicle_id: int = Query(..., description="Customer EV ID"),
    start_at: datetime = Query(..., description="Requested start datetime"),
    end_at: datetime = Query(..., description="Requested end datetime"),
    connector_type_id: Optional[int] = Query(None, description="Optional connector filter"),
    min_power_kw: Optional[Decimal] = Query(None, description="Optional minimum charger power in kW"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ChargerAvailabilityResponse:
    """
    Search available charging points at a station for a given EV and time interval.
    
    Verifies:
      1. Vehicle ownership (Customer owns vehicle, or Admin)
      2. Connector compatibility between EV and charging dispenser
      3. Station operating hours & operational status
      4. Charger operational status (ONLINE vs MAINTENANCE/OUT_OF_SERVICE)
      5. Time-slot availability (excluding overlapping active reservations & ongoing sessions)
      6. Integrates dynamic pricing estimation for the slot
    """
    return get_available_chargers_for_booking(
        station_id=station_id,
        vehicle_id=vehicle_id,
        start_at=start_at,
        end_at=end_at,
        connector_type_id=connector_type_id,
        min_power_kw=min_power_kw,
        current_user=current_user,
        db=db
    )


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve a charging slot"
)
def create_reservation(
    payload: ReservationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ReservationResponse:
    """
    Reserve an EV charging point slot transactionally.
    
    Guarantees:
      - Authenticated user ID is strictly derived from the JWT (never trusted from body)
      - Vehicle ownership verified
      - Charger operational status verified (ONLINE)
      - Station active status & operating hours verified
      - Vehicle connector standard verified against bay connector
      - Row-level locking & exclusion constraint prevent double-booking
      - Returns HTTP 409 Conflict if slot is already occupied
    """
    return create_reservation_transaction(
        payload=payload,
        current_user=current_user,
        db=db
    )


@router.get(
    "",
    response_model=List[ReservationResponse],
    summary="List reservations with role-based access"
)
def list_reservations(
    page: PageParam,
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    status: Optional[str] = Query(None, description="Filter by status (CONFIRMED, PENDING, CANCELLED, etc.)"),
    from_date: Optional[datetime] = Query(None, description="Filter reservations starting on or after"),
    to_date: Optional[datetime] = Query(None, description="Filter reservations starting on or before"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ReservationResponse]:
    """
    Retrieve reservations with strict RBAC visibility:
      - CUSTOMER: Isolated to own reservations
      - OPERATOR: Reservations at stations operated by user
      - ADMIN: Network-wide visibility
    """
    query = select(Reservation).join(Reservation.charger).join(Charger.station)

    # Role-based scoping
    if current_user.role == "CUSTOMER":
        query = query.where(Reservation.user_id == current_user.user_id)
    elif current_user.role == "OPERATOR":
        query = query.where(Station.operator_id == current_user.user_id)

    # Filters
    if station_id is not None:
        query = query.where(Charger.station_id == station_id)
    if vehicle_id is not None:
        query = query.where(Reservation.vehicle_id == vehicle_id)
    if status:
        query = query.where(Reservation.status == status.strip().upper())
    if from_date is not None:
        norm_from = normalize_datetime(from_date)
        query = query.where(Reservation.start_at >= norm_from)
    if to_date is not None:
        norm_to = normalize_datetime(to_date)
        query = query.where(Reservation.start_at <= norm_to)

    reservations = db.execute(
        page.apply(query.order_by(Reservation.start_at.desc(), Reservation.reservation_id.desc()))
    ).scalars().all()

    return [format_reservation_response(r) for r in reservations]


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Get reservation details"
)
def get_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ReservationResponse:
    """
    Retrieve detailed reservation information including customer, vehicle, station, and charger info.
    """
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {reservation_id} not found."
        )

    # RBAC Access control
    if current_user.role == "CUSTOMER" and reservation.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this reservation."
        )

    if current_user.role == "OPERATOR":
        op_id = reservation.charger.station.operator_id if reservation.charger and reservation.charger.station else None
        if op_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only view reservations for stations you operate."
            )

    return format_reservation_response(reservation)


@router.patch(
    "/{reservation_id}/cancel",
    response_model=ReservationCancelResponse,
    summary="Cancel an active reservation"
)
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ReservationCancelResponse:
    """
    Cancel an active PENDING or CONFIRMED reservation.
    Releases the charging point slot immediately for new bookings.
    Preserves audit history in the database.
    """
    res = cancel_reservation_transaction(
        reservation_id=reservation_id,
        current_user=current_user,
        db=db
    )
    return ReservationCancelResponse(**res)

