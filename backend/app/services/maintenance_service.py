"""
Maintenance Work Order and Charger Status Audit Trail Service.
Handles work order lifecycles, slot/session conflict detection during maintenance transitions,
status history logging, and aggregated maintenance performance analytics.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from backend.app.models.maintenance import MaintenanceRecord, ChargerStatusHistory
from backend.app.models.station import Station, Charger
from backend.app.models.session import ChargingSession
from backend.app.models.reservation import Reservation
from backend.app.models.user import User
from backend.app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdateStatus,
    MaintenanceResponse,
    ChargerStatusHistoryResponse,
    MaintenanceAnalyticsResponse,
    MaintenanceSummaryResponse,
    StationMaintenanceStats,
    ChargerFaultStats,
)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_maintenance_response(record: MaintenanceRecord) -> MaintenanceResponse:
    """Format MaintenanceRecord ORM object into MaintenanceResponse schema."""
    charger_code = record.charger.charger_code if record.charger else None
    station_id = record.charger.station_id if record.charger else None
    station_name = record.charger.station.station_name if (record.charger and record.charger.station) else None
    reporter_name = record.reporter.full_name if record.reporter else f"User #{record.reported_by}"
    assignee_name = record.assignee.full_name if record.assignee else (f"User #{record.assigned_to}" if record.assigned_to else None)

    return MaintenanceResponse(
        maintenance_id=record.maintenance_id,
        charger_id=record.charger_id,
        charger_code=charger_code,
        station_id=station_id,
        station_name=station_name,
        reported_by=record.reported_by,
        reported_by_name=reporter_name,
        assigned_to=record.assigned_to,
        assigned_to_name=assignee_name,
        issue_description=record.issue_description,
        priority=record.priority,
        status=record.status,
        reported_at=record.reported_at,
        scheduled_at=record.scheduled_at,
        resolved_at=record.resolved_at,
        maintenance_cost=record.maintenance_cost or Decimal("0.00"),
    )


def format_status_history_response(entry: ChargerStatusHistory) -> ChargerStatusHistoryResponse:
    """Format ChargerStatusHistory ORM object into response schema."""
    charger_code = entry.charger.charger_code if entry.charger else None
    changed_by_name = entry.changed_by_user.full_name if entry.changed_by_user else (f"User #{entry.changed_by}" if entry.changed_by else "System")

    return ChargerStatusHistoryResponse(
        history_id=entry.history_id,
        charger_id=entry.charger_id,
        charger_code=charger_code,
        previous_status=entry.previous_status,
        new_status=entry.new_status,
        changed_by=entry.changed_by,
        changed_by_name=changed_by_name,
        reason=entry.reason,
        changed_at=entry.changed_at,
    )


def create_maintenance_order(
    payload: MaintenanceCreate,
    current_user: User,
    db: Session,
) -> MaintenanceResponse:
    """
    Create a new maintenance work order.
    Default status: 'OPEN'.
    """
    # 1. Validate Charger
    charger = db.query(Charger).filter(Charger.charger_id == payload.charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {payload.charger_id} not found."
        )

    # 2. Assignee check if specified
    assigned_to_id = payload.assigned_to
    if assigned_to_id is not None:
        assignee = db.query(User).filter(User.user_id == assigned_to_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assigned user with ID {assigned_to_id} does not exist."
            )
        if assignee.role not in ("OPERATOR", "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned technician must have role OPERATOR or ADMIN."
            )

    # 3. Determine reported_by
    reported_by_id = current_user.user_id
    if current_user.role == "ADMIN" and payload.reported_by is not None:
        reported_by_id = payload.reported_by

    new_record = MaintenanceRecord(
        charger_id=payload.charger_id,
        reported_by=reported_by_id,
        assigned_to=assigned_to_id,
        issue_description=payload.issue_description.strip(),
        priority=payload.priority.upper(),
        status="OPEN",
        scheduled_at=ensure_utc(payload.scheduled_at),
        maintenance_cost=Decimal("0.00"),
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return format_maintenance_response(new_record)


def assign_maintenance_order(
    maintenance_id: int,
    assigned_to: int,
    current_user: User,
    db: Session,
) -> MaintenanceResponse:
    """
    Assign a maintenance work order to an operator/admin technician.
    """
    if current_user.role not in ("ADMIN", "OPERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and station operators can assign maintenance work orders."
        )

    record = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.maintenance_id == maintenance_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with ID {maintenance_id} not found."
        )

    if record.status in ("RESOLVED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign work order that is already in '{record.status}' status."
        )

    # If operator, verify station authority
    if current_user.role == "OPERATOR":
        charger = db.query(Charger).filter(Charger.charger_id == record.charger_id).first()
        if charger and charger.station:
            if charger.station.operator_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operators can only assign work orders for chargers at their assigned stations."
                )

    assignee = db.query(User).filter(User.user_id == assigned_to).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician user with ID {assigned_to} not found."
        )
    if assignee.role not in ("OPERATOR", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned technician must have role OPERATOR or ADMIN."
        )

    record.assigned_to = assigned_to
    db.commit()
    db.refresh(record)

    return format_maintenance_response(record)


def update_maintenance_status(
    maintenance_id: int,
    payload: MaintenanceUpdateStatus,
    current_user: User,
    db: Session,
) -> MaintenanceResponse:
    """
    Update maintenance work order status lifecycle:
    - OPEN -> IN_PROGRESS: Locks charger, checks active sessions / upcoming reservations (409 Conflict), sets charger to MAINTENANCE, logs audit history.
    - IN_PROGRESS -> RESOLVED: Records resolved_at, records maintenance_cost. Leaves charger in MAINTENANCE until explicit operator clearance.
    - OPEN -> CANCELLED: Records status, preserves record, leaves charger status unchanged.
    """
    if current_user.role not in ("ADMIN", "OPERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and station operators can update maintenance status."
        )

    record = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.maintenance_id == maintenance_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with ID {maintenance_id} not found."
        )

    # Operator authorization check
    if current_user.role == "OPERATOR":
        charger = db.query(Charger).filter(Charger.charger_id == record.charger_id).first()
        if charger and charger.station:
            if charger.station.operator_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operators can only modify maintenance orders at their assigned stations."
                )

    current_status = record.status
    target_status = payload.status

    if current_status == target_status:
        # No-op or updates cost/notes if applicable
        if payload.maintenance_cost is not None:
            record.maintenance_cost = payload.maintenance_cost
        db.commit()
        db.refresh(record)
        return format_maintenance_response(record)

    # Terminal state checks
    if current_status == "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maintenance record is already RESOLVED and cannot be transitioned to another status."
        )
    if current_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maintenance record is CANCELLED and cannot be transitioned to another status."
        )

    now = datetime.now(timezone.utc)

    # Transition 1: OPEN -> IN_PROGRESS
    if target_status == "IN_PROGRESS":
        if current_status != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition to IN_PROGRESS from '{current_status}'. Allowed only from 'OPEN'."
            )

        # Lock charger row
        charger_query = db.query(Charger).filter(Charger.charger_id == record.charger_id)
        charger = charger_query.with_for_update(of=Charger).first()

        if not charger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated charger {record.charger_id} not found."
            )

        # Conflict check A: Active charging session on this charger
        active_session = db.query(ChargingSession).filter(
            ChargingSession.charger_id == charger.charger_id,
            ChargingSession.status == "ACTIVE"
        ).first()
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot begin maintenance: Charger has an active charging session "
                    f"(Session ID: {active_session.session_id})."
                )
            )

        # Conflict check B: Active or upcoming reservations on this charger bay
        active_reservation = db.query(Reservation).filter(
            Reservation.charger_id == charger.charger_id,
            Reservation.status.in_(["PENDING", "CONFIRMED"]),
            Reservation.end_at > now
        ).first()
        if active_reservation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot begin maintenance: Charger has an active or upcoming reservation "
                    f"(Reservation ID: {active_reservation.reservation_id}, ends at {active_reservation.end_at.isoformat()})."
                )
            )

        # Atomically transition charger status to MAINTENANCE and log to audit trail
        prev_status = charger.operational_status
        if prev_status != "MAINTENANCE":
            charger.operational_status = "MAINTENANCE"
            status_history = ChargerStatusHistory(
                charger_id=charger.charger_id,
                previous_status=prev_status,
                new_status="MAINTENANCE",
                changed_by=current_user.user_id,
                reason=payload.reason or f"Work order #{record.maintenance_id} started (Priority: {record.priority})",
            )
            db.add(status_history)

        record.status = "IN_PROGRESS"

    # Transition 2: IN_PROGRESS -> RESOLVED
    elif target_status == "RESOLVED":
        if current_status != "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resolve work order from '{current_status}'. Work order must be 'IN_PROGRESS' first."
            )

        resolution_dt = ensure_utc(payload.resolved_at) or now
        rep_at = ensure_utc(record.reported_at)
        if rep_at and resolution_dt < rep_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution timestamp cannot be earlier than reported timestamp."
            )

        record.resolved_at = resolution_dt
        if payload.maintenance_cost is not None:
            if payload.maintenance_cost < Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maintenance cost cannot be negative."
                )
            record.maintenance_cost = payload.maintenance_cost

        record.status = "RESOLVED"
        # IMPORTANT: Charger remains in MAINTENANCE status.
        # It must be cleared online explicitly via charger status API by an operator.

    # Transition 3: OPEN -> CANCELLED
    elif target_status == "CANCELLED":
        if current_status != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel work order from '{current_status}'. Only 'OPEN' orders can be cancelled."
            )
        record.status = "CANCELLED"
        # Preserved in DB, charger status unmodified.

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target status '{target_status}'."
        )

    db.commit()
    db.refresh(record)
    return format_maintenance_response(record)


def get_maintenance_order(
    maintenance_id: int,
    current_user: User,
    db: Session,
) -> MaintenanceResponse:
    """Retrieve a single maintenance work order with RBAC authorization."""
    record = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.maintenance_id == maintenance_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with ID {maintenance_id} not found."
        )

    if current_user.role == "CUSTOMER":
        if record.reported_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only access maintenance reports they submitted."
            )

    return format_maintenance_response(record)


def list_maintenance_orders(
    current_user: User,
    db: Session,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    charger_id_filter: Optional[int] = None,
    station_id_filter: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[MaintenanceResponse]:
    """List maintenance work orders with multi-criteria filtering and RBAC isolation."""
    query = db.query(MaintenanceRecord).join(
        Charger, MaintenanceRecord.charger_id == Charger.charger_id
    ).join(
        Station, Charger.station_id == Station.station_id
    )

    # RBAC Scoping
    if current_user.role == "CUSTOMER":
        query = query.filter(MaintenanceRecord.reported_by == current_user.user_id)
    elif current_user.role == "OPERATOR":
        # Operator sees orders at their stations or assigned directly to them
        query = query.filter(
            or_(
                Station.operator_id == current_user.user_id,
                MaintenanceRecord.assigned_to == current_user.user_id,
                MaintenanceRecord.reported_by == current_user.user_id,
            )
        )

    # Filters
    if status_filter:
        query = query.filter(MaintenanceRecord.status == status_filter.upper())
    if priority_filter:
        query = query.filter(MaintenanceRecord.priority == priority_filter.upper())
    if charger_id_filter:
        query = query.filter(MaintenanceRecord.charger_id == charger_id_filter)
    if station_id_filter:
        query = query.filter(Charger.station_id == station_id_filter)

    query = query.order_by(desc(MaintenanceRecord.reported_at))
    records = query.offset(skip).limit(limit).all()

    return [format_maintenance_response(r) for r in records]


def get_charger_status_history(
    charger_id: int,
    current_user: User,
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ChargerStatusHistoryResponse]:
    """Retrieve audit trail of operational status transitions for a specific charger."""
    charger = db.query(Charger).filter(Charger.charger_id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger with ID {charger_id} not found."
        )

    # If operator, verify station
    if current_user.role == "OPERATOR":
        if charger.station and charger.station.operator_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operators can only view status audit history for chargers at their assigned stations."
            )

    query = db.query(ChargerStatusHistory).filter(ChargerStatusHistory.charger_id == charger_id)

    if start_date:
        query = query.filter(ChargerStatusHistory.changed_at >= ensure_utc(start_date))
    if end_date:
        query = query.filter(ChargerStatusHistory.changed_at <= ensure_utc(end_date))

    query = query.order_by(desc(ChargerStatusHistory.changed_at), desc(ChargerStatusHistory.history_id))
    entries = query.offset(skip).limit(limit).all()

    return [format_status_history_response(e) for e in entries]


def get_maintenance_analytics(
    current_user: User,
    db: Session,
) -> MaintenanceAnalyticsResponse:
    """
    SQL aggregation engine for maintenance operations:
    - Counts by status and high/critical priorities
    - Total maintenance expenditure
    - Average resolution time in hours
    - Station-level maintenance breakdown
    - Frequent fault chargers and estimated downtime hours
    """
    if current_user.role not in ("ADMIN", "OPERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and station operators can access maintenance analytics."
        )

    base_query = db.query(MaintenanceRecord).join(
        Charger, MaintenanceRecord.charger_id == Charger.charger_id
    ).join(
        Station, Charger.station_id == Station.station_id
    )

    if current_user.role == "OPERATOR":
        base_query = base_query.filter(Station.operator_id == current_user.user_id)

    records = base_query.all()

    total_orders = len(records)
    open_orders = sum(1 for r in records if r.status == "OPEN")
    in_progress_orders = sum(1 for r in records if r.status == "IN_PROGRESS")
    resolved_orders = sum(1 for r in records if r.status == "RESOLVED")
    cancelled_orders = sum(1 for r in records if r.status == "CANCELLED")
    high_critical_orders = sum(1 for r in records if r.priority in ("HIGH", "CRITICAL"))
    total_cost = sum((r.maintenance_cost or Decimal("0.00") for r in records), Decimal("0.00"))

    # Average resolution time in hours for resolved orders
    resolution_durations = []
    for r in records:
        if r.status == "RESOLVED" and r.resolved_at and r.reported_at:
            res_at = ensure_utc(r.resolved_at)
            rep_at = ensure_utc(r.reported_at)
            if res_at and rep_at and res_at >= rep_at:
                diff_seconds = (res_at - rep_at).total_seconds()
                resolution_durations.append(diff_seconds / 3600.0)

    avg_resolution_hours = (
        round(sum(resolution_durations) / len(resolution_durations), 2)
        if resolution_durations else None
    )

    summary = MaintenanceSummaryResponse(
        total_orders=total_orders,
        open_orders=open_orders,
        in_progress_orders=in_progress_orders,
        resolved_orders=resolved_orders,
        cancelled_orders=cancelled_orders,
        high_critical_orders=high_critical_orders,
        total_cost=total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        avg_resolution_hours=avg_resolution_hours,
    )

    # Station Breakdown
    stations_map: Dict[int, Dict[str, Any]] = {}
    for r in records:
        st_id = r.charger.station_id if r.charger else 0
        st_name = r.charger.station.station_name if (r.charger and r.charger.station) else f"Station #{st_id}"
        if st_id not in stations_map:
            stations_map[st_id] = {
                "station_id": st_id,
                "station_name": st_name,
                "total_orders": 0,
                "open_orders": 0,
                "total_cost": Decimal("0.00"),
            }
        stations_map[st_id]["total_orders"] += 1
        if r.status in ("OPEN", "IN_PROGRESS"):
            stations_map[st_id]["open_orders"] += 1
        stations_map[st_id]["total_cost"] += (r.maintenance_cost or Decimal("0.00"))

    by_station = [
        StationMaintenanceStats(
            station_id=item["station_id"],
            station_name=item["station_name"],
            total_orders=item["total_orders"],
            open_orders=item["open_orders"],
            total_cost=item["total_cost"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )
        for item in stations_map.values()
    ]

    # Frequent fault chargers and estimated downtime
    chargers_map: Dict[int, Dict[str, Any]] = {}
    for r in records:
        c_id = r.charger_id
        c_code = r.charger.charger_code if r.charger else f"CH-{c_id}"
        st_name = r.charger.station.station_name if (r.charger and r.charger.station) else "Unknown Station"
        if c_id not in chargers_map:
            chargers_map[c_id] = {
                "charger_id": c_id,
                "charger_code": c_code,
                "station_name": st_name,
                "fault_count": 0,
                "total_downtime_hours": 0.0,
            }
        chargers_map[c_id]["fault_count"] += 1
        if r.resolved_at and r.reported_at:
            res_at = ensure_utc(r.resolved_at)
            rep_at = ensure_utc(r.reported_at)
            if res_at and rep_at and res_at >= rep_at:
                chargers_map[c_id]["total_downtime_hours"] += (res_at - rep_at).total_seconds() / 3600.0

    frequent_fault_chargers = [
        ChargerFaultStats(
            charger_id=item["charger_id"],
            charger_code=item["charger_code"],
            station_name=item["station_name"],
            fault_count=item["fault_count"],
            total_downtime_hours=round(item["total_downtime_hours"], 2),
        )
        for item in sorted(chargers_map.values(), key=lambda x: x["fault_count"], reverse=True)
    ]

    return MaintenanceAnalyticsResponse(
        summary=summary,
        by_station=by_station,
        frequent_fault_chargers=frequent_fault_chargers,
    )
