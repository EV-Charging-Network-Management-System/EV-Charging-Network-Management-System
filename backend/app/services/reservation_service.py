"""
Reservation Management and Slot Conflict Engine Service.
Provides charger availability calculation, vehicle connector compatibility validation,
transactional reservation booking with row-level locking, and cancellation management.
"""

from datetime import datetime, timezone, timedelta, time
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import Vehicle, ConnectorType
from backend.app.models.tariff import Tariff
from backend.app.models.session import ChargingSession
from backend.app.models.reservation import Reservation
from backend.app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    ReservationCustomerInfo,
    ReservationVehicleInfo,
    ReservationStationInfo,
    ReservationChargerInfo,
    AvailableChargerResponse,
    ChargerAvailabilityResponse
)
from backend.app.services.pricing_service import (
    normalize_datetime,
    calculate_price_quote
)


def format_reservation_response(res: Reservation) -> ReservationResponse:
    """Format an ORM Reservation model into a rich ReservationResponse schema."""
    customer_info = None
    if res.user:
        customer_info = ReservationCustomerInfo(
            user_id=res.user.user_id,
            full_name=res.user.full_name,
            email=res.user.email,
            phone=res.user.phone
        )

    vehicle_info = None
    if res.vehicle:
        vehicle_info = ReservationVehicleInfo(
            vehicle_id=res.vehicle.vehicle_id,
            make=res.vehicle.make,
            model=res.vehicle.model,
            registration_number=res.vehicle.registration_number,
            battery_capacity_kwh=res.vehicle.battery_capacity_kwh
        )

    station_info = None
    charger_info = None
    if res.charger:
        charger_info = ReservationChargerInfo(
            charger_id=res.charger.charger_id,
            charger_code=res.charger.charger_code,
            power_kw=res.charger.power_kw,
            connector_type_id=res.charger.connector_type_id,
            connector_type_name=res.charger.connector_type.type_name if res.charger.connector_type else None
        )
        if res.charger.station:
            station_info = ReservationStationInfo(
                station_id=res.charger.station.station_id,
                station_name=res.charger.station.station_name,
                address=res.charger.station.address,
                city=res.charger.station.city
            )

    return ReservationResponse(
        reservation_id=res.reservation_id,
        user_id=res.user_id,
        vehicle_id=res.vehicle_id,
        charger_id=res.charger_id,
        start_at=res.start_at,
        end_at=res.end_at,
        status=res.status,
        created_at=res.created_at,
        customer=customer_info,
        vehicle=vehicle_info,
        station=station_info,
        charger=charger_info
    )


def is_within_operating_hours(
    opening_time: Optional[time],
    closing_time: Optional[time],
    start_at: datetime,
    end_at: datetime
) -> Tuple[bool, Optional[str]]:
    """
    Validate whether requested start_at and end_at fall within the station's operating hours.
    Returns (True, None) if open or 24/7, or (False, reason) if outside hours.
    """
    if opening_time is None or closing_time is None:
        return True, None
    if opening_time == closing_time:
        return True, None

    req_start = start_at.time()
    req_end = end_at.time()

    if opening_time < closing_time:
        # Standard day window (e.g. 06:00 to 22:00)
        if not (opening_time <= req_start and req_end <= closing_time):
            return False, f"Outside station operating hours ({opening_time.strftime('%H:%M')} - {closing_time.strftime('%H:%M')})"
    else:
        # Overnight window (e.g. 18:00 to 06:00)
        start_valid = (req_start >= opening_time or req_start <= closing_time)
        end_valid = (req_end >= opening_time or req_end <= closing_time)
        if not (start_valid and end_valid):
            return False, f"Outside station overnight operating hours ({opening_time.strftime('%H:%M')} - {closing_time.strftime('%H:%M')})"

    return True, None


def check_charger_slot_availability(
    charger: Charger,
    start_at: datetime,
    end_at: datetime,
    db: Session,
    exclude_reservation_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific charger is physically online and available for the time slot [start_at, end_at).
    """
    # 1. Operational status
    if charger.operational_status != "ONLINE":
        status_label = charger.operational_status.replace("_", " ").title()
        return False, f"Charger is currently {status_label}"

    # 2. Station active check
    if charger.station and charger.station.status != "ACTIVE":
        return False, "Charging station is currently inactive"

    # 3. Operating hours check
    if charger.station:
        is_open, hour_err = is_within_operating_hours(
            charger.station.opening_time,
            charger.station.closing_time,
            start_at,
            end_at
        )
        if not is_open:
            return False, hour_err

    # 4. Overlapping reservations check (half-open [start_at, end_at))
    # Two slots [A_start, A_end) and [B_start, B_end) overlap iff A_start < B_end AND A_end > B_start.
    query = select(Reservation).where(
        Reservation.charger_id == charger.charger_id,
        Reservation.status.in_(["PENDING", "CONFIRMED"]),
        Reservation.start_at < end_at,
        Reservation.end_at > start_at
    )
    if exclude_reservation_id is not None:
        query = query.where(Reservation.reservation_id != exclude_reservation_id)

    conflict = db.execute(query).scalars().first()
    if conflict:
        return False, "This charging slot has already been reserved. Please choose another time."

    # 5. Active sessions check
    # If session is currently ACTIVE on this charger and extends into the slot window
    active_session = db.execute(
        select(ChargingSession).where(
            ChargingSession.charger_id == charger.charger_id,
            ChargingSession.status == "ACTIVE"
        )
    ).scalars().first()

    if active_session:
        now = datetime.now(timezone.utc)
        # If requested start is within 1 hour of now, conflict with current session
        if start_at <= now + timedelta(minutes=15):
            return False, "Charger currently has an active in-progress charging session"

    return True, None


def get_available_chargers_for_booking(
    station_id: int,
    vehicle_id: int,
    start_at: datetime,
    end_at: datetime,
    connector_type_id: Optional[int],
    min_power_kw: Optional[Decimal],
    current_user: User,
    db: Session
) -> ChargerAvailabilityResponse:
    """
    Inspect charger availability for a customer vehicle at a station over [start_at, end_at).
    """
    norm_start = normalize_datetime(start_at)
    norm_end = normalize_datetime(end_at)

    if norm_end <= norm_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_at must be strictly after start_at"
        )

    # 1. Fetch Station
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {station_id} not found."
        )

    # 2. Fetch & Validate Vehicle
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found."
        )

    # Ownership check
    if current_user.role != "ADMIN" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only check availability for electric vehicles registered to your account."
        )

    # 3. Vehicle connector compatibility
    vehicle_connector_ids = {vct.connector_type_id for vct in vehicle.vehicle_connector_types}
    if not vehicle_connector_ids and hasattr(vehicle, "connector_types"):
        vehicle_connector_ids = {c.connector_type_id for c in vehicle.connector_types if c}

    # 4. Query station chargers
    charger_query = select(Charger).where(Charger.station_id == station_id)
    if connector_type_id is not None:
        charger_query = charger_query.where(Charger.connector_type_id == connector_type_id)
    if min_power_kw is not None:
        charger_query = charger_query.where(Charger.power_kw >= min_power_kw)

    chargers = db.execute(charger_query.order_by(Charger.charger_code.asc())).scalars().all()

    available_results: List[AvailableChargerResponse] = []
    available_count = 0

    for ch in chargers:
        # Check compatibility with customer EV
        is_compatible = ch.connector_type_id in vehicle_connector_ids
        if not is_compatible:
            # Skip incompatible chargers unless connector_type_id explicitly filtered
            continue

        is_slot_avail, unavail_reason = check_charger_slot_availability(
            charger=ch,
            start_at=norm_start,
            end_at=norm_end,
            db=db
        )

        if is_slot_avail:
            available_count += 1

        # Calculate estimated price quote
        price_quote = None
        try:
            # Estimate with 25 kWh or vehicle battery capacity
            est_kwh = vehicle.battery_capacity_kwh or Decimal("25.00")
            price_quote = calculate_price_quote(
                station_id=station_id,
                connector_type_id=ch.connector_type_id,
                estimated_energy_kwh=est_kwh,
                start_at=norm_start,
                end_at=norm_end,
                db=db
            )
        except Exception:
            # Pricing quote is an estimate and optional
            price_quote = None

        available_results.append(
            AvailableChargerResponse(
                charger_id=ch.charger_id,
                charger_code=ch.charger_code,
                power_kw=ch.power_kw,
                connector_type_id=ch.connector_type_id,
                connector_type_name=ch.connector_type.type_name if ch.connector_type else "Unknown",
                operational_status=ch.operational_status,
                is_available=is_slot_avail,
                unavailability_reason=unavail_reason,
                estimated_price=price_quote
            )
        )

    return ChargerAvailabilityResponse(
        station_id=station.station_id,
        station_name=station.station_name,
        vehicle_id=vehicle.vehicle_id,
        vehicle_make_model=f"{vehicle.make} {vehicle.model} ({vehicle.registration_number})",
        start_at=norm_start,
        end_at=norm_end,
        total_compatible_chargers=len(available_results),
        available_chargers_count=available_count,
        chargers=available_results
    )


def create_reservation_transaction(
    payload: ReservationCreate,
    current_user: User,
    db: Session
) -> ReservationResponse:
    """
    Reserve a charging slot transactionally with row-level locking and exclusion handling.
    """
    norm_start = normalize_datetime(payload.start_at)
    norm_end = normalize_datetime(payload.end_at)
    now = datetime.now(timezone.utc)

    # 1. Interval checks
    if norm_end <= norm_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_at must be strictly after start_at"
        )

    # Past reservation check (5-minute latency tolerance)
    if norm_start < now - timedelta(minutes=5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a reservation slot in the past."
        )

    # 2. Validate Vehicle
    vehicle = db.get(Vehicle, payload.vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {payload.vehicle_id} not found."
        )

    if current_user.role != "ADMIN" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only create reservations for vehicles registered to your account."
        )

    # 3. Validate Charger
    charger = db.get(Charger, payload.charger_id)
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {payload.charger_id} not found."
        )

    # 4. Charger operational status
    if charger.operational_status != "ONLINE":
        status_label = charger.operational_status.replace("_", " ").title()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reserve charger {charger.charger_code}: Bay is currently {status_label}."
        )

    # 5. Station active and hours
    station = charger.station
    if station and station.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Charging station is currently inactive."
        )

    if station:
        is_open, hour_err = is_within_operating_hours(
            station.opening_time,
            station.closing_time,
            norm_start,
            norm_end
        )
        if not is_open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=hour_err
            )

    # 6. Connector compatibility validation
    vehicle_connector_ids = {vct.connector_type_id for vct in vehicle.vehicle_connector_types}
    if not vehicle_connector_ids and hasattr(vehicle, "connector_types"):
        vehicle_connector_ids = {c.connector_type_id for c in vehicle.connector_types if c}
    if charger.connector_type_id not in vehicle_connector_ids:
        c_name = charger.connector_type.type_name if charger.connector_type else f"ID {charger.connector_type_id}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Incompatible connector: Charger requires {c_name}, which is not supported by {vehicle.make} {vehicle.model}."
        )

    # 7. Transactional slot availability check with row locking
    try:
        # Lock the stable physical Charger row to serialize slot evaluations on this bay
        # We specify of=Charger so that joined relationships on outer joins are not locked
        db.execute(
            select(Charger)
            .where(Charger.charger_id == payload.charger_id)
            .with_for_update(of=Charger)
        ).scalar_one_or_none()

        # Row-level locking on conflicting active reservations
        conflicts = db.execute(
            select(Reservation)
            .where(
                Reservation.charger_id == charger.charger_id,
                Reservation.status.in_(["PENDING", "CONFIRMED"]),
                Reservation.start_at < norm_end,
                Reservation.end_at > norm_start
            )
            .with_for_update()
        ).scalars().all()

        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This charging slot has already been reserved. Please choose another time."
            )

        reservation = Reservation(
            user_id=current_user.user_id,
            vehicle_id=payload.vehicle_id,
            charger_id=payload.charger_id,
            start_at=norm_start,
            end_at=norm_end,
            status="CONFIRMED"
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        return format_reservation_response(reservation)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        err_msg = str(exc).lower()
        if "23p01" in err_msg or "exclude" in err_msg or "overlap" in err_msg or "conflict" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This charging slot has already been reserved. Please choose another time."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violation during reservation creation."
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reserve charging slot: {str(exc)}"
        )


def cancel_reservation_transaction(
    reservation_id: int,
    current_user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Cancel an existing reservation, immediately releasing the slot.
    """
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {reservation_id} not found."
        )

    # Ownership check
    if current_user.role != "ADMIN" and reservation.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only cancel reservations booked under your account."
        )

    # Status check
    if reservation.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation is already cancelled."
        )

    if reservation.status in ("COMPLETED", "NO_SHOW"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a reservation with status '{reservation.status}'."
        )

    reservation.status = "CANCELLED"
    db.commit()
    db.refresh(reservation)

    return {
        "reservation_id": reservation.reservation_id,
        "status": "CANCELLED",
        "message": "Reservation successfully cancelled. Time slot is now available."
    }
