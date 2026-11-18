"""
Maintenance Work Order and Diagnostics Endpoints.
Provides RESTful APIs for managing maintenance lifecycles, technician assignments,
bay locking / conflict verification, and maintenance analytics.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdateStatus,
    MaintenanceAssignRequest,
    MaintenanceResponse,
    MaintenanceAnalyticsResponse,
    ChargerStatusHistoryResponse,
)
from backend.app.services.maintenance_service import (
    create_maintenance_order,
    assign_maintenance_order,
    update_maintenance_status,
    get_maintenance_order,
    list_maintenance_orders,
    get_maintenance_analytics,
)

router = APIRouter()


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a new maintenance work order.
    Customers, operators, and admins can report issues on chargers.
    Initial status is automatically set to 'OPEN'.
    """
    return create_maintenance_order(payload=payload, current_user=current_user, db=db)


@router.get("", response_model=List[MaintenanceResponse])
def list_maintenance(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, IN_PROGRESS, RESOLVED, CANCELLED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)"),
    charger_id: Optional[int] = Query(None, description="Filter by charger ID"),
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List maintenance work orders with multi-criteria filtering and RBAC isolation.
    - Admins see all orders.
    - Operators see orders for their assigned stations or assigned to them.
    - Customers see only orders they reported.
    """
    return list_maintenance_orders(
        current_user=current_user,
        db=db,
        status_filter=status,
        priority_filter=priority,
        charger_id_filter=charger_id,
        station_id_filter=station_id,
        skip=skip,
        limit=limit,
    )


@router.get("/reports/summary", response_model=MaintenanceAnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve comprehensive maintenance analytics, SLA resolution times, and station breakdowns.
    Available to Admins and Operators only.
    """
    return get_maintenance_analytics(current_user=current_user, db=db)


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details of a single maintenance work order.
    """
    return get_maintenance_order(maintenance_id=maintenance_id, current_user=current_user, db=db)


@router.patch("/{maintenance_id}/assign", response_model=MaintenanceResponse)
def assign_maintenance(
    maintenance_id: int,
    payload: MaintenanceAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a maintenance work order to an operator or administrator technician.
    """
    return assign_maintenance_order(
        maintenance_id=maintenance_id,
        assigned_to=payload.assigned_to,
        current_user=current_user,
        db=db,
    )


@router.patch("/{maintenance_id}/status", response_model=MaintenanceResponse)
def update_status(
    maintenance_id: int,
    payload: MaintenanceUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Transition maintenance status lifecycle:
    - OPEN -> IN_PROGRESS: Verifies no active sessions or reservations (409 Conflict), sets charger to MAINTENANCE, logs status audit trail.
    - IN_PROGRESS -> RESOLVED: Records resolution timestamp and maintenance cost. Leaves charger in MAINTENANCE status until operator safety clearance.
    - OPEN -> CANCELLED: Cancels work order, preserves history without altering charger state.
    """
    return update_maintenance_status(
        maintenance_id=maintenance_id,
        payload=payload,
        current_user=current_user,
        db=db,
    )
