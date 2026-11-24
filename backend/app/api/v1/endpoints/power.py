"""Fairly distribute a station's power budget across its active sessions."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_operator_or_admin
from backend.app.core.database import get_db
from backend.app.models.session import ChargingSession
from backend.app.models.station import Charger, Station
from backend.app.models.user import User
from backend.app.models.workflow import AdminAuditEvent

router = APIRouter()


class SitePowerCap(BaseModel):
    site_power_cap_kw: Decimal | None = Field(..., gt=0, max_digits=10, decimal_places=3)


class ChargingAllocation(BaseModel):
    session_id: int
    charger_id: int
    allocated_kw: Decimal


class StationAllocation(BaseModel):
    station_id: int
    site_power_cap_kw: Decimal | None
    total_allocated_kw: Decimal
    sessions: list[ChargingAllocation]


def allocate_watts(capacity_by_session: dict[int, int], budget: int) -> dict[int, int]:
    """Apply max-min fairness in whole watts, breaking rounding ties by session ID."""
    allocation = {}
    entries = sorted(capacity_by_session.items(), key=lambda item: (item[1], item[0]))
    for i, (session_id, rated) in enumerate(entries):
        remaining_count = len(entries) - i
        if rated * remaining_count > budget:
            equal, remainder = divmod(budget, remaining_count)
            for j, identifier in enumerate(sorted(key for key, _ in entries[i:])):
                allocation[identifier] = equal + int(j < remainder)
            break
        allocation[session_id] = rated
        budget -= rated
    return allocation


def _station_for_staff(db: Session, station_id: int, user: User, *, lock: bool = False) -> Station:
    query = select(Station).where(Station.station_id == station_id)
    if lock:
        query = query.with_for_update(of=Station)
    station = db.scalar(query)
    if station is None:
        raise HTTPException(404, "Station not found.")
    if user.role == "OPERATOR" and station.operator_id != user.user_id:
        raise HTTPException(403, "Station is managed by another operator.")
    return station


def _station_allocation(db: Session, station: Station) -> StationAllocation:
    rows = db.execute(
        select(ChargingSession.session_id, Charger.charger_id, Charger.power_kw, Charger.operational_status)
        .join(Charger, Charger.charger_id == ChargingSession.charger_id)
        .where(Charger.station_id == station.station_id, ChargingSession.status == "ACTIVE")
        .order_by(ChargingSession.session_id)
    ).all()
    ratings = {
        row.session_id: int(row.power_kw * 1000) if row.operational_status == "ONLINE" else 0
        for row in rows
    }
    budget = sum(ratings.values())
    if station.site_power_cap_kw is not None:
        budget = min(budget, int(station.site_power_cap_kw * 1000))
    allocation = allocate_watts(ratings, budget)
    return StationAllocation(
        station_id=station.station_id, site_power_cap_kw=station.site_power_cap_kw,
        total_allocated_kw=Decimal(sum(allocation.values())) / 1000,
        sessions=[
            ChargingAllocation(session_id=row.session_id, charger_id=row.charger_id,
                               allocated_kw=Decimal(allocation[row.session_id]) / 1000)
            for row in rows
        ],
    )


@router.get("/stations/{station_id}/power-allocation", response_model=StationAllocation)
def get_power_allocation(
    station_id: int, current_user: User = Depends(require_operator_or_admin), db: Session = Depends(get_db),
):
    return _station_allocation(db, _station_for_staff(db, station_id, current_user))


@router.put("/stations/{station_id}/power-cap", response_model=StationAllocation)
def set_power_cap(
    station_id: int, cap: SitePowerCap, current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db),
):
    station = _station_for_staff(db, station_id, current_user, lock=True)
    db.add(AdminAuditEvent(
        actor_id=current_user.user_id, action="station.power_cap_changed", resource_id=station_id,
        details={"site_power_cap_kw": str(cap.site_power_cap_kw) if cap.site_power_cap_kw is not None else None},
    ))
    station.site_power_cap_kw = cap.site_power_cap_kw
    db.commit()
    return _station_allocation(db, station)
