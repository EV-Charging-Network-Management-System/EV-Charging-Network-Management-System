"""
Charging Session Management and Energy Metering Service.
Implements:
- Reservation-based and walk-in session start.
- Meter reading validation & energy consumption tracking.
- Session completion & interruption with transactional state integrity.
- Integration with Module 6 dynamic tariff & pricing calculation engine.
- RBAC data isolation (Customer, Operator, Admin).
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import Vehicle
from backend.app.models.tariff import Tariff, PricingRule
from backend.app.models.reservation import Reservation
from backend.app.models.session import ChargingSession
from backend.app.schemas.session import (
    SessionStartRequest,
    SessionCompleteRequest,
    SessionInterruptRequest,
    SessionResponse,
    SessionCustomerInfo,
    SessionVehicleInfo,
    SessionStationInfo,
    SessionChargerInfo,
    SessionTariffInfo
)
from backend.app.services.session_events import notify_session
from backend.app.services.pricing_service import (
    select_applicable_tariff,
    evaluate_pricing_rules,
    normalize_datetime
)


def calculate_session_cost(
    energy_kwh: Decimal,
    base_price_per_kwh: Decimal,
    multiplier: Decimal,
    session_fee: Decimal,
    tax_rate_percent: Decimal
) -> Decimal:
    """Calculate total payable cost for a charging session using half-up financial rounding."""
    effective_rate = (base_price_per_kwh * multiplier).quantize(Decimal("0.01"))
    energy_charge = (energy_kwh * effective_rate).quantize(Decimal("0.01"))
    subtotal = (energy_charge + session_fee).quantize(Decimal("0.01"))
    tax_amount = (subtotal * (tax_rate_percent / Decimal("100.00"))).quantize(Decimal("0.01"))
    return (subtotal + tax_amount).quantize(Decimal("0.01"))


def format_session_response(
    session: ChargingSession,
    db: Session
) -> SessionResponse:
    """Format an ORM ChargingSession model into a rich SessionResponse schema."""
    customer_info = None
    if session.user:
        customer_info = SessionCustomerInfo(
            user_id=session.user.user_id,
            full_name=session.user.full_name,
            email=session.user.email,
            phone=session.user.phone
        )

    vehicle_info = None
    if session.vehicle:
        vehicle_info = SessionVehicleInfo(
            vehicle_id=session.vehicle.vehicle_id,
            make=session.vehicle.make,
            model=session.vehicle.model,
            registration_number=session.vehicle.registration_number,
            battery_capacity_kwh=session.vehicle.battery_capacity_kwh
        )

    charger_info = None
    station_info = None
    if session.charger:
        charger_info = SessionChargerInfo(
            charger_id=session.charger.charger_id,
            charger_code=session.charger.charger_code,
            power_kw=session.charger.power_kw,
            connector_type_id=session.charger.connector_type_id,
            connector_type_name=session.charger.connector_type.type_name if session.charger.connector_type else None,
            operational_status=session.charger.operational_status
        )
        if session.charger.station:
            station_info = SessionStationInfo(
                station_id=session.charger.station.station_id,
                station_name=session.charger.station.station_name,
                address=session.charger.station.address,
                city=session.charger.station.city
            )

    tariff_info = None
    estimated_cost = None
    if session.tariff:
        # Determine pricing rule snapshot at session start
        try:
            rule_multiplier, active_rule = evaluate_pricing_rules(
                tariff=session.tariff,
                target_time=session.started_at,
                station_demand_percent=Decimal("0.00")
            )
            effective_rate = (session.tariff.base_price_per_kwh * rule_multiplier).quantize(Decimal("0.01"))
            rule_type = active_rule.rule_type if active_rule else "STANDARD"
        except Exception:
            rule_multiplier = Decimal("1.00")
            effective_rate = session.tariff.base_price_per_kwh
            rule_type = "STANDARD"

        tariff_info = SessionTariffInfo(
            tariff_id=session.tariff.tariff_id,
            base_price_per_kwh=session.tariff.base_price_per_kwh,
            session_fee=session.tariff.session_fee,
            tax_rate_percent=session.tariff.tax_rate_percent,
            effective_rate_per_kwh=effective_rate,
            multiplier=rule_multiplier,
            applied_rule_type=rule_type
        )

        if session.energy_consumed_kwh is not None:
            estimated_cost = calculate_session_cost(
                energy_kwh=session.energy_consumed_kwh,
                base_price_per_kwh=session.tariff.base_price_per_kwh,
                multiplier=rule_multiplier,
                session_fee=session.tariff.session_fee,
                tax_rate_percent=session.tariff.tax_rate_percent
            )

    return SessionResponse(
        session_id=session.session_id,
        reservation_id=session.reservation_id,
        user_id=session.user_id,
        vehicle_id=session.vehicle_id,
        charger_id=session.charger_id,
        tariff_id=session.tariff_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        meter_start_kwh=session.meter_start_kwh,
        meter_end_kwh=session.meter_end_kwh,
        energy_consumed_kwh=session.energy_consumed_kwh,
        status=session.status,
        customer=customer_info,
        vehicle=vehicle_info,
        station=station_info,
        charger=charger_info,
        tariff=tariff_info,
        estimated_cost=estimated_cost
    )


def start_charging_session(
    payload: SessionStartRequest,
    current_user: User,
    db: Session
) -> SessionResponse:
    """
    Start an electric vehicle charging session transactionally.
    Supports both reservation-based charging and walk-in charging.
    """
    now = datetime.now(timezone.utc)

    # 1. Meter start non-negative validation
    if payload.meter_start_kwh < Decimal("0.000"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="meter_start_kwh cannot be negative."
        )

    # 2. Lock physical Charger row to serialize sessions on this bay
    charger = db.execute(
        select(Charger)
        .where(Charger.charger_id == payload.charger_id)
        .with_for_update(of=Charger)
    ).scalar_one_or_none()

    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {payload.charger_id} not found."
        )

    # 3. Charger and Station operational health check
    if charger.operational_status != "ONLINE":
        status_label = charger.operational_status.replace("_", " ").title()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start session on charger {charger.charger_code}: Bay is currently {status_label}."
        )

    station = charger.station
    if station and station.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Charging station is currently inactive."
        )

    # 4. Prevent multiple ACTIVE sessions on the same charger
    active_session = db.execute(
        select(ChargingSession)
        .where(
            ChargingSession.charger_id == payload.charger_id,
            ChargingSession.status == "ACTIVE"
        )
        .with_for_update(of=ChargingSession)
    ).scalars().first()

    if active_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Charger {charger.charger_code} already has an active charging session in progress."
        )

    # 5. Validate Vehicle & Ownership
    vehicle = db.get(Vehicle, payload.vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {payload.vehicle_id} not found."
        )

    if current_user.role != "ADMIN" and vehicle.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only start charging sessions for vehicles registered to your account."
        )

    # 6. Validate Connector Compatibility
    vehicle_connector_ids = {vct.connector_type_id for vct in vehicle.vehicle_connector_types}
    if not vehicle_connector_ids and hasattr(vehicle, "connector_types"):
        vehicle_connector_ids = {c.connector_type_id for c in vehicle.connector_types if c}

    if charger.connector_type_id not in vehicle_connector_ids:
        c_name = charger.connector_type.type_name if charger.connector_type else f"ID {charger.connector_type_id}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Incompatible connector: Charger requires {c_name}, which is not supported by {vehicle.make} {vehicle.model}."
        )

    # 7. Reservation validation (Reservation-based vs Walk-in)
    if payload.reservation_id is not None:
        reservation = db.get(Reservation, payload.reservation_id)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation with ID {payload.reservation_id} not found."
            )

        # Ownership verification
        if current_user.role != "ADMIN" and reservation.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: This reservation does not belong to your account."
            )

        # Vehicle and charger matching
        if reservation.vehicle_id != payload.vehicle_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation is registered for a different vehicle."
            )
        if reservation.charger_id != payload.charger_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation is assigned to a different charger bay."
            )

        # Reservation status
        if reservation.status not in ("PENDING", "CONFIRMED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start session: Reservation is already {reservation.status}."
            )

        # Slot time window validation (allow start from 30 mins before start_at up to 30 mins after end_at)
        res_start = normalize_datetime(reservation.start_at)
        res_end = normalize_datetime(reservation.end_at)
        if now < res_start - timedelta(minutes=30):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too early: Your reserved slot starts at {res_start.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )
        if now > res_end + timedelta(minutes=30):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reservation slot has expired at {res_end.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )

        # Unique reservation session check
        existing_res_session = db.execute(
            select(ChargingSession).where(ChargingSession.reservation_id == payload.reservation_id)
        ).scalars().first()
        if existing_res_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A charging session has already been started for this reservation."
            )

    else:
        # Walk-in charging: Verify no conflicting confirmed reservation on this bay right now
        conflicting_res = db.execute(
            select(Reservation).where(
                Reservation.charger_id == charger.charger_id,
                Reservation.status.in_(["PENDING", "CONFIRMED"]),
                Reservation.start_at <= now + timedelta(minutes=15),
                Reservation.end_at > now
            )
        ).scalars().first()

        if conflicting_res:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Charger bay is reserved for another driver during this time window. Walk-in unavailable."
            )

    # 8. Resolve Applicable Tariff via Module 6 pricing engine
    tariff = select_applicable_tariff(
        station_id=charger.station_id,
        connector_type_id=charger.connector_type_id,
        target_time=now,
        db=db
    )
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active tariff found for station #{charger.station_id}."
        )

    # 9. Create Charging Session
    session = ChargingSession(
        reservation_id=payload.reservation_id,
        user_id=current_user.user_id,
        vehicle_id=payload.vehicle_id,
        charger_id=payload.charger_id,
        tariff_id=tariff.tariff_id,
        started_at=now,
        ended_at=None,
        meter_start_kwh=payload.meter_start_kwh,
        meter_end_kwh=None,
        status="ACTIVE"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return format_session_response(session, db)


def complete_charging_session(
    session_id: int,
    payload: SessionCompleteRequest,
    current_user: User,
    db: Session
) -> SessionResponse:
    """
    Complete an active charging session, record final meter reading, and calculate consumption.
    """
    session = db.execute(
        select(ChargingSession)
        .where(ChargingSession.session_id == session_id)
        .with_for_update(of=ChargingSession)
    ).scalars().first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging session with ID {session_id} not found."
        )

    # Authorization
    is_owner = session.user_id == current_user.user_id
    is_admin = current_user.role == "ADMIN"
    is_operator = (
        current_user.role == "OPERATOR"
        and session.charger
        and session.charger.station
        and session.charger.station.operator_id == current_user.user_id
    )

    if not (is_owner or is_admin or is_operator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to complete this charging session."
        )

    # Status check
    if session.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete session: Session is already {session.status}."
        )

    # Meter reading check
    if payload.meter_end_kwh < session.meter_start_kwh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ending meter reading ({payload.meter_end_kwh} kWh) cannot be less than starting reading ({session.meter_start_kwh} kWh)."
        )

    now = datetime.now(timezone.utc)
    session.meter_end_kwh = payload.meter_end_kwh
    session.ended_at = now
    session.status = "COMPLETED"

    # Update associated reservation to COMPLETED if active
    if session.reservation_id is not None:
        reservation = db.get(Reservation, session.reservation_id)
        if reservation and reservation.status in ("CONFIRMED", "PENDING"):
            reservation.status = "COMPLETED"

    notify_session(db, session.session_id)
    db.commit()
    db.refresh(session)

    return format_session_response(session, db)


def interrupt_charging_session(
    session_id: int,
    payload: SessionInterruptRequest,
    current_user: User,
    db: Session
) -> SessionResponse:
    """
    Interrupt an active charging session due to user request, fault, or emergency stop.
    """
    session = db.execute(
        select(ChargingSession)
        .where(ChargingSession.session_id == session_id)
        .with_for_update(of=ChargingSession)
    ).scalars().first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging session with ID {session_id} not found."
        )

    # Authorization
    is_owner = session.user_id == current_user.user_id
    is_admin = current_user.role == "ADMIN"
    is_operator = (
        current_user.role == "OPERATOR"
        and session.charger
        and session.charger.station
        and session.charger.station.operator_id == current_user.user_id
    )

    if not (is_owner or is_admin or is_operator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to interrupt this charging session."
        )

    if session.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot interrupt session: Session is already {session.status}."
        )

    # Final meter reading must satisfy PostgreSQL constraint:
    # ((status IN ('COMPLETED', 'INTERRUPTED') AND ended_at IS NOT NULL AND meter_end_kwh IS NOT NULL))
    final_meter = payload.meter_end_kwh if payload.meter_end_kwh is not None else session.meter_start_kwh
    if final_meter < session.meter_start_kwh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ending meter reading ({final_meter} kWh) cannot be less than starting reading ({session.meter_start_kwh} kWh)."
        )

    now = datetime.now(timezone.utc)
    session.meter_end_kwh = final_meter
    session.ended_at = now
    session.status = "INTERRUPTED"

    # Associated reservation is completed so slot is freed
    if session.reservation_id is not None:
        reservation = db.get(Reservation, session.reservation_id)
        if reservation and reservation.status in ("CONFIRMED", "PENDING"):
            reservation.status = "COMPLETED"

    notify_session(db, session.session_id)
    db.commit()
    db.refresh(session)

    return format_session_response(session, db)


def get_session_by_id(
    session_id: int,
    current_user: User,
    db: Session
) -> SessionResponse:
    """Retrieve a single charging session by ID enforcing RBAC data isolation."""
    session = db.get(ChargingSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging session with ID {session_id} not found."
        )

    # RBAC Isolation Check
    if current_user.role == "CUSTOMER" and session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only view your own charging sessions."
        )

    if current_user.role == "OPERATOR":
        station_op_id = (
            session.charger.station.operator_id
            if session.charger and session.charger.station
            else None
        )
        if station_op_id != current_user.user_id and session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only view charging sessions at stations you operate."
            )

    return format_session_response(session, db)


def list_sessions(
    current_user: User,
    db: Session,
    status_filter: Optional[str] = None,
    station_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    active_only: bool = False
) -> List[SessionResponse]:
    """List charging sessions according to caller's role and search parameters."""
    query = select(ChargingSession)

    # Role-Based Scoping
    if current_user.role == "CUSTOMER":
        query = query.where(ChargingSession.user_id == current_user.user_id)
    elif current_user.role == "OPERATOR":
        query = query.join(Charger, ChargingSession.charger_id == Charger.charger_id)\
                     .join(Station, Charger.station_id == Station.station_id)\
                     .where(Station.operator_id == current_user.user_id)
    # ADMIN has full visibility

    if active_only:
        query = query.where(ChargingSession.status == "ACTIVE")
    elif status_filter:
        query = query.where(ChargingSession.status == status_filter.upper())

    if station_id is not None:
        if current_user.role != "OPERATOR":
            query = query.join(Charger, ChargingSession.charger_id == Charger.charger_id)
        query = query.where(Charger.station_id == station_id)

    if vehicle_id is not None:
        query = query.where(ChargingSession.vehicle_id == vehicle_id)

    if from_date:
        query = query.where(ChargingSession.started_at >= from_date)
    if to_date:
        query = query.where(ChargingSession.started_at <= to_date)

    query = query.order_by(ChargingSession.started_at.desc())
    sessions = db.execute(query).scalars().all()

    return [format_session_response(s, db) for s in sessions]
