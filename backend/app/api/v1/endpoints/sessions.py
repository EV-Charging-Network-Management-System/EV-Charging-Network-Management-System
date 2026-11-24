"""
Charging Sessions and Energy Metering API Endpoints.
Provides session initiation (reservation-based and walk-in), active session monitoring,
meter-driven session completion, and interruption controls.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.pagination import PageParam
from backend.app.services.idempotency import IdempotencyKey, run_idempotent
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.meter_reading import MeterReading
from backend.app.schemas.session import (
    SessionStartRequest,
    SessionCompleteRequest,
    SessionInterruptRequest,
    MeterReadingResponse,
    SessionResponse
)
from backend.app.services.session_service import (
    start_charging_session,
    complete_charging_session,
    interrupt_charging_session,
    get_session_by_id,
    list_sessions
)

router = APIRouter()


@router.post(
    "/start",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an electric vehicle charging session",
    description="Starts a new charging session. Supports both reservation-based charging and walk-in charging."
)
def start_session(
    payload: SessionStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None
):
    """Start an EV charging session transactionally with meter reading validation."""
    return run_idempotent(
        db, current_user.user_id, "session.start", idempotency_key, payload,
        lambda: start_charging_session(
            payload=payload,
            current_user=current_user,
            db=db,
            commit=idempotency_key is None,
        ),
        lambda saved: get_session_by_id(saved["session_id"], current_user, db),
    )


@router.get(
    "/active",
    response_model=List[SessionResponse],
    summary="List active charging sessions",
    description="Retrieve all currently in-progress charging sessions. Scoped by caller role."
)
def get_active_sessions(
    page: PageParam,
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve all ACTIVE charging sessions."""
    return list_sessions(
        current_user=current_user,
        db=db,
        station_id=station_id,
        active_only=True, page=page
    )


@router.get(
    "/history",
    response_model=List[SessionResponse],
    summary="List charging session history",
    description="Retrieve charging session history with optional filtering by status, station, or vehicle."
)
def get_session_history(
    page: PageParam,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (COMPLETED, INTERRUPTED, ACTIVE)"),
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    from_date: Optional[datetime] = Query(None, description="Filter from start date (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="Filter to end date (ISO 8601)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List charging sessions filtered by parameters and caller permissions."""
    return list_sessions(
        current_user=current_user,
        db=db,
        status_filter=status_filter,
        station_id=station_id,
        vehicle_id=vehicle_id,
        from_date=from_date,
        to_date=to_date,
        active_only=False, page=page
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get charging session details",
    description="Retrieve full details of a specific charging session by ID."
)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve charging session details by ID."""
    return get_session_by_id(
        session_id=session_id,
        current_user=current_user,
        db=db
    )


@router.post(
    "/{session_id}/complete",
    response_model=SessionResponse,
    summary="Complete an active charging session",
    description="Records the final meter reading, calculates total energy consumed in kWh, and marks the session COMPLETED."
)
def complete_session(
    session_id: int,
    payload: SessionCompleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None
):
    """Complete a session and calculate total consumption."""
    return run_idempotent(
        db, current_user.user_id, f"session.complete:{session_id}", idempotency_key, payload,
        lambda: complete_charging_session(
            session_id=session_id,
            payload=payload,
            current_user=current_user,
            db=db,
            commit=idempotency_key is None,
        ),
        lambda saved: get_session_by_id(saved["session_id"], current_user, db),
    )


@router.post(
    "/{session_id}/interrupt",
    response_model=SessionResponse,
    summary="Interrupt an active charging session",
    description="Interrupts an active session due to an emergency stop, vehicle disconnection, or station fault."
)
def interrupt_session(
    session_id: int,
    payload: SessionInterruptRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None
):
    """Interrupt a charging session and record final reading."""
    return run_idempotent(
        db, current_user.user_id, f"session.interrupt:{session_id}", idempotency_key, payload,
        lambda: interrupt_charging_session(
            session_id=session_id,
            payload=payload,
            current_user=current_user,
            db=db,
            commit=idempotency_key is None,
        ),
        lambda saved: get_session_by_id(saved["session_id"], current_user, db),
    )


@router.get("/{session_id}/meter-readings", response_model=list[MeterReadingResponse])
def get_meter_readings(
    session_id: int,
    limit: int = Query(100, ge=1, le=500),
    before: datetime | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    get_session_by_id(session_id=session_id, current_user=current_user, db=db)
    query = select(MeterReading).where(MeterReading.session_id == session_id)
    if before is not None:
        query = query.where(MeterReading.recorded_at < before)
    readings = db.scalars(query.order_by(MeterReading.recorded_at.desc()).limit(limit)).all()
    return [MeterReadingResponse.model_validate(reading) for reading in readings]
