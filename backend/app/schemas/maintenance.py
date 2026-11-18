"""
Pydantic v2 validation schemas for Maintenance Records and Charger Status History.
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    charger_id: int
    issue_description: str = Field(..., min_length=3)
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    assigned_to: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    reported_by: Optional[int] = None


class MaintenanceUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(OPEN|IN_PROGRESS|RESOLVED|CANCELLED)$")
    maintenance_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    resolved_at: Optional[datetime] = None
    reason: Optional[str] = None


class MaintenanceAssignRequest(BaseModel):
    assigned_to: int


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    maintenance_id: int
    charger_id: int
    charger_code: Optional[str] = None
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    reported_by: int
    reported_by_name: Optional[str] = None
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    issue_description: str
    priority: str
    status: str
    reported_at: datetime
    scheduled_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    maintenance_cost: Decimal


class ChargerStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    charger_id: int
    charger_code: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None
    reason: Optional[str] = None
    changed_at: datetime


class MaintenanceSummaryResponse(BaseModel):
    total_orders: int
    open_orders: int
    in_progress_orders: int
    resolved_orders: int
    cancelled_orders: int
    high_critical_orders: int
    total_cost: Decimal
    avg_resolution_hours: Optional[float] = None


class StationMaintenanceStats(BaseModel):
    station_id: int
    station_name: str
    total_orders: int
    open_orders: int
    total_cost: Decimal


class ChargerFaultStats(BaseModel):
    charger_id: int
    charger_code: str
    station_name: str
    fault_count: int
    total_downtime_hours: float


class MaintenanceAnalyticsResponse(BaseModel):
    summary: MaintenanceSummaryResponse
    by_station: List[StationMaintenanceStats]
    frequent_fault_chargers: List[ChargerFaultStats]
