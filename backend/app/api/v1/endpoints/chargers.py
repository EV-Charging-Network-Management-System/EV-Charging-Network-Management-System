"""
Charger Management Endpoints.
Implements charger querying, inspection, updating, and atomic status change audit logging.
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_operator_or_admin
from backend.app.models.user import User
from backend.app.models.station import Station, Charger
from backend.app.models.vehicle import ConnectorType
from backend.app.models.maintenance import ChargerStatusHistory
from backend.app.schemas.station import ChargerUpdate, ChargerResponse
from backend.app.schemas.maintenance import ChargerStatusHistoryResponse
from backend.app.services.maintenance_service import get_charger_status_history

router = APIRouter()


@router.get(
    "",
    response_model=List[ChargerResponse],
    summary="List chargers"
)
def list_chargers(
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    connector_type_id: Optional[int] = Query(None, description="Filter by connector standard ID"),
    operational_status: Optional[str] = Query(None, description="Filter by operational status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Charger]:
    """
    List chargers across the network with optional filtering.
    """
    query = db.query(Charger)

    if station_id is not None:
        query = query.filter(Charger.station_id == station_id)
    if connector_type_id is not None:
        query = query.filter(Charger.connector_type_id == connector_type_id)
    if operational_status:
        query = query.filter(Charger.operational_status == operational_status.strip().upper())

    chargers = query.order_by(Charger.station_id.asc(), Charger.charger_id.asc()).all()
    return chargers


@router.get(
    "/{charger_id}",
    response_model=ChargerResponse,
    summary="Get charger details"
)
def get_charger_details(
    charger_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Charger:
    """Retrieve specifications for a single charging bay."""
    charger = db.query(Charger).filter(Charger.charger_id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {charger_id} not found"
        )
    return charger


@router.patch(
    "/{charger_id}",
    response_model=ChargerResponse,
    summary="Update charger specifications or operational status"
)
def update_charger(
    charger_id: int,
    charger_in: ChargerUpdate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> Charger:
    """
    Update charger specs or operational status.
    Transitions write an audit row into charger_status_history.
    """
    charger = db.query(Charger).filter(Charger.charger_id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {charger_id} not found"
        )

    # Operator authorization check: must manage the parent station
    if current_user.role == "OPERATOR" and charger.station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operators can only manage chargers at stations assigned to them"
        )

    # Validate connector type if changed
    if charger_in.connector_type_id is not None:
        connector = db.query(ConnectorType).filter(
            ConnectorType.connector_type_id == charger_in.connector_type_id
        ).first()
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector type with ID {charger_in.connector_type_id} does not exist"
            )
        charger.connector_type_id = charger_in.connector_type_id

    # Validate unique code if changed
    if charger_in.charger_code is not None:
        new_code = charger_in.charger_code.strip().upper()
        if new_code != charger.charger_code:
            existing = db.query(Charger).filter(
                Charger.station_id == charger.station_id,
                Charger.charger_code == new_code,
                Charger.charger_id != charger_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Charger code '{new_code}' already in use at this station"
                )
            charger.charger_code = new_code

    if charger_in.power_kw is not None:
        if charger_in.power_kw <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Power rating must be strictly greater than 0 kW"
            )
        charger.power_kw = charger_in.power_kw

    # Status transition handling & audit logging
    status_changed = (
        charger_in.operational_status is not None
        and charger_in.operational_status != charger.operational_status
    )

    try:
        if status_changed:
            prev_status = charger.operational_status
            new_status = charger_in.operational_status
            charger.operational_status = new_status

            # Insert history record
            history_entry = ChargerStatusHistory(
                charger_id=charger_id,
                previous_status=prev_status,
                new_status=new_status,
                changed_by=current_user.user_id,
                reason=charger_in.reason or "Status updated via management portal."
            )
            db.add(history_entry)

        db.commit()
        db.refresh(charger)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update charger: {str(exc)}"
        )

    return charger


@router.get(
    "/{charger_id}/status-history",
    response_model=List[ChargerStatusHistoryResponse],
    summary="Get charger operational status audit trail"
)
def get_charger_history(
    charger_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter history from date"),
    end_date: Optional[datetime] = Query(None, description="Filter history to date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve chronological audit trail of operational status changes for this charger (newest first).
    """
    return get_charger_status_history(
        charger_id=charger_id,
        current_user=current_user,
        db=db,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
