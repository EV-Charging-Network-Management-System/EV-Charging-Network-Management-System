"""
Tariff Management Endpoints.
Implements CRUD, querying with filters, validation, temporal overlap prevention,
and role-based station authorization.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.api.pagination import PageParam
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_operator_or_admin
from backend.app.models.user import User
from backend.app.models.station import Station
from backend.app.models.vehicle import ConnectorType
from backend.app.models.tariff import Tariff
from backend.app.models.workflow import AdminAuditEvent
from backend.app.schemas.tariff import (
    TariffCreate,
    TariffUpdate,
    TariffResponse
)
from backend.app.services.pricing_service import check_tariff_overlap, normalize_datetime

router = APIRouter()


def format_tariff_response(tariff: Tariff) -> TariffResponse:
    """Helper to populate station and connector names on response."""
    return TariffResponse(
        tariff_id=tariff.tariff_id,
        station_id=tariff.station_id,
        station_name=tariff.station.station_name if tariff.station else None,
        connector_type_id=tariff.connector_type_id,
        connector_type_name=tariff.connector_type.type_name if tariff.connector_type else None,
        base_price_per_kwh=tariff.base_price_per_kwh,
        session_fee=tariff.session_fee,
        tax_rate_percent=tariff.tax_rate_percent,
        valid_from=tariff.valid_from,
        valid_to=tariff.valid_to,
        pricing_rules=tariff.pricing_rules
    )


@router.get(
    "",
    response_model=List[TariffResponse],
    summary="List tariffs with optional filters"
)
def list_tariffs(
    page: PageParam,
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    connector_type_id: Optional[int] = Query(None, description="Filter by connector type ID"),
    active_at: Optional[datetime] = Query(None, description="Filter tariffs active at this datetime"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[TariffResponse]:
    """
    List all tariffs in the network.
    Filterable by station, connector type, and active datetime.
    Accessible to all active authenticated users.
    """
    query = select(Tariff)

    if station_id is not None:
        query = query.where(Tariff.station_id == station_id)
    if connector_type_id is not None:
        query = query.where(Tariff.connector_type_id == connector_type_id)

    if active_at is not None:
        active = normalize_datetime(active_at)
        query = query.where(Tariff.valid_from <= active, Tariff.valid_to.is_(None) | (Tariff.valid_to >= active))
    tariffs = db.scalars(page.apply(query.order_by(Tariff.station_id, Tariff.tariff_id))).all()
    return [format_tariff_response(t) for t in tariffs]


@router.post(
    "",
    response_model=TariffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tariff"
)
def create_tariff(
    payload: TariffCreate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> TariffResponse:
    """
    Create a new base tariff for a station.
    Operators can only create tariffs for stations they operate. Admins can create for any station.
    Enforces non-negative rates, valid dates, and rejects temporal overlaps with existing tariffs.
    """
    station = db.get(Station, payload.station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {payload.station_id} does not exist."
        )

    # RBAC ownership check for operators
    if current_user.role == "OPERATOR" and station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only configure tariffs for charging stations you operate."
        )

    # Check connector type if specified
    if payload.connector_type_id is not None:
        connector = db.get(ConnectorType, payload.connector_type_id)
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ConnectorType with ID {payload.connector_type_id} does not exist."
            )

    # Temporal overlap check
    has_overlap = check_tariff_overlap(
        station_id=payload.station_id,
        connector_type_id=payload.connector_type_id,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        db=db
    )
    if has_overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tariff already exists for this station and connector configuration with an overlapping validity period."
        )

    tariff = Tariff(
        station_id=payload.station_id,
        connector_type_id=payload.connector_type_id,
        base_price_per_kwh=payload.base_price_per_kwh,
        session_fee=payload.session_fee,
        tax_rate_percent=payload.tax_rate_percent,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to
    )
    db.add(tariff)
    db.flush()
    db.add(AdminAuditEvent(
        actor_id=current_user.user_id, action="tariff.created", resource_id=tariff.tariff_id, details={"station_id": tariff.station_id, **payload.model_dump(mode="json", exclude={"station_id"})},
    ))
    db.commit()
    db.refresh(tariff)

    return format_tariff_response(tariff)


@router.get(
    "/{tariff_id}",
    response_model=TariffResponse,
    summary="Get tariff details"
)
def get_tariff(
    tariff_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TariffResponse:
    """
    Retrieve tariff details by ID including associated dynamic pricing rules.
    """
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tariff with ID {tariff_id} not found."
        )
    return format_tariff_response(tariff)


@router.patch(
    "/{tariff_id}",
    response_model=TariffResponse,
    summary="Update a tariff"
)
def update_tariff(
    tariff_id: int,
    payload: TariffUpdate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> TariffResponse:
    """
    Update tariff pricing parameters or validity window.
    Operators can only update tariffs for stations they operate. Admins can update any.
    Validates non-negative values and prevents temporal overlaps if dates change.
    """
    tariff = db.scalar(select(Tariff).where(Tariff.tariff_id == tariff_id).with_for_update(of=Tariff))
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tariff with ID {tariff_id} not found."
        )

    # RBAC ownership check
    if current_user.role == "OPERATOR" and tariff.station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only update tariffs for charging stations you operate."
        )

    # Check valid_to constraints if modified
    new_valid_to = payload.valid_to if payload.valid_to is not None else tariff.valid_to
    if new_valid_to is not None and new_valid_to <= tariff.valid_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="valid_to must be strictly after valid_from."
        )

    if payload.valid_to is not None:
        has_overlap = check_tariff_overlap(
            station_id=tariff.station_id,
            connector_type_id=tariff.connector_type_id,
            valid_from=tariff.valid_from,
            valid_to=new_valid_to,
            db=db,
            exclude_tariff_id=tariff.tariff_id
        )
        if has_overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Updating tariff validity window creates an overlap with another existing tariff."
            )
        tariff.valid_to = new_valid_to

    if payload.base_price_per_kwh is not None:
        tariff.base_price_per_kwh = payload.base_price_per_kwh
    if payload.session_fee is not None:
        tariff.session_fee = payload.session_fee
    if payload.tax_rate_percent is not None:
        tariff.tax_rate_percent = payload.tax_rate_percent

    db.add(AdminAuditEvent(
        actor_id=current_user.user_id, action="tariff.updated", resource_id=tariff_id, details=payload.model_dump(mode="json", exclude_none=True),
    ))
    db.commit()
    db.refresh(tariff)
    return format_tariff_response(tariff)
