"""Network KPIs scoped to stations the caller can operate."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_operator_or_admin
from backend.app.core.database import get_db
from backend.app.models.billing import Invoice, Payment
from backend.app.models.maintenance import ChargerStatusHistory, MaintenanceRecord
from backend.app.models.session import ChargingSession
from backend.app.models.station import Charger, Station
from backend.app.models.user import User


class BayKpi(BaseModel):
    charger_id: int
    charger_code: str
    station_name: str
    uptime_percent: float
    utilization_percent: float


class HourKpi(BaseModel):
    hour_utc: int
    energy_kwh: Decimal
    expected_starts: float


class NetworkKpis(BaseModel):
    days: int
    average_session_minutes: float | None
    mean_repair_minutes: float | None
    net_revenue_per_kwh: Decimal | None
    chargers: list[BayKpi]
    hours: list[HourKpi]


router = APIRouter()


def _uptime(history, current_status: str, begin: datetime, now: datetime) -> float:
    start, seconds = begin, 0.0
    status = current_status if not history else (history[0].previous_status or history[0].new_status)
    for event in history:
        if event.changed_at >= begin:
            if status == "ONLINE":
                seconds += (event.changed_at - start).total_seconds()
            start = event.changed_at
        status = event.new_status
    if status == "ONLINE":
        seconds += (now - start).total_seconds()
    return round(100 * seconds / (now - begin).total_seconds(), 2)


@router.get("/admin/network-kpis", response_model=NetworkKpis)
def get_network_kpis(
    days: int = Query(30, ge=1, le=90),
    station_id: int | None = Query(None, ge=1),
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db),
) -> NetworkKpis:
    now = datetime.now(timezone.utc)
    begin = now - timedelta(days=days)
    bays = select(Charger.charger_id, Charger.charger_code, Charger.operational_status, Station.station_name).join(
        Station, Station.station_id == Charger.station_id
    )
    if current_user.role == "OPERATOR":
        bays = bays.where(Station.operator_id == current_user.user_id)
    if station_id is not None:
        bays = bays.where(Station.station_id == station_id)

    charger_rows = db.execute(bays.order_by(Station.station_name, Charger.charger_code, Charger.charger_id)).all()
    ids = [row.charger_id for row in charger_rows]
    sessions = db.scalars(select(ChargingSession).where(
        ChargingSession.charger_id.in_(ids),
        ChargingSession.started_at < now,
        (ChargingSession.ended_at.is_(None) | (ChargingSession.ended_at >= begin)),
    )).all()

    prior = (
        select(ChargerStatusHistory)
        .where(ChargerStatusHistory.charger_id.in_(ids), ChargerStatusHistory.changed_at < begin)
        .distinct(ChargerStatusHistory.charger_id)
        .order_by(ChargerStatusHistory.charger_id, ChargerStatusHistory.changed_at.desc(), ChargerStatusHistory.history_id.desc())
    )
    history = defaultdict(list)
    for event in db.scalars(prior):
        history[event.charger_id].append(event)
    for event in db.scalars(select(ChargerStatusHistory).where(
        ChargerStatusHistory.charger_id.in_(ids), ChargerStatusHistory.changed_at >= begin,
        ChargerStatusHistory.changed_at <= now,
    ).order_by(ChargerStatusHistory.changed_at, ChargerStatusHistory.history_id)):
        history[event.charger_id].append(event)

    occupied = defaultdict(float)
    energy = defaultdict(Decimal)
    starts = defaultdict(int)
    closed_ids = []
    durations = []
    for session in sessions:
        if session.started_at >= begin:
            starts[session.started_at.astimezone(timezone.utc).hour] += 1
        end = session.ended_at or now
        occupied[session.charger_id] += (min(end, now) - max(session.started_at, begin)).total_seconds()
        if session.ended_at is not None and session.ended_at <= now:
            consumed = session.energy_consumed_kwh or Decimal(0)
            energy[session.ended_at.astimezone(timezone.utc).hour] += consumed
            durations.append((session.ended_at - session.started_at).total_seconds() / 60)
            closed_ids.append(session.session_id)

    total_energy = sum(energy.values(), Decimal(0))
    received = db.scalar(select(func.sum(case((Payment.status == "SUCCESS", Payment.amount), else_=0))).join(
        Invoice, Invoice.invoice_id == Payment.invoice_id,
    ).where(Invoice.session_id.in_(closed_ids))) or Decimal(0)
    repair_minutes = db.scalar(select(func.avg(func.extract(
        "epoch", MaintenanceRecord.resolved_at - MaintenanceRecord.reported_at,
    ) / 60)).where(
        MaintenanceRecord.charger_id.in_(ids),
        MaintenanceRecord.status == "RESOLVED",
        MaintenanceRecord.resolved_at >= begin,
        MaintenanceRecord.resolved_at <= now,
    ))

    period_seconds = (now - begin).total_seconds()
    return NetworkKpis(
        days=days,
        average_session_minutes=round(sum(durations)/len(durations), 2) if durations else None,
        mean_repair_minutes=round(float(repair_minutes), 2) if repair_minutes is not None else None,
        net_revenue_per_kwh=round(received/total_energy, 2) if total_energy else None,
        chargers=[
            BayKpi(
                charger_id=bay.charger_id, charger_code=bay.charger_code, station_name=bay.station_name,
                uptime_percent=_uptime(history[bay.charger_id], bay.operational_status, begin, now),
                utilization_percent=round(min(100, 100 * occupied[bay.charger_id] / period_seconds), 2),
            )
            for bay in charger_rows
        ],
        hours=[
            HourKpi(hour_utc=hour, energy_kwh=energy[hour], expected_starts=round(starts[hour]/days, 2))
            for hour in range(24)
        ],
    )
