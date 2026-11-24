"""
Pydantic v2 validation schemas for Charging Sessions and Energy Metering.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Nested Information Models
# ============================================================================

class SessionCustomerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None


class SessionVehicleInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    make: str
    model: str
    registration_number: str
    battery_capacity_kwh: Optional[Decimal] = None


class SessionStationInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: int
    station_name: str
    address: str
    city: str


class SessionChargerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    charger_id: int
    charger_code: str
    power_kw: Decimal
    connector_type_id: int
    connector_type_name: Optional[str] = None
    operational_status: Optional[str] = None


class SessionTariffInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tariff_id: int
    base_price_per_kwh: Decimal
    session_fee: Decimal
    tax_rate_percent: Decimal
    effective_rate_per_kwh: Optional[Decimal] = None
    multiplier: Optional[Decimal] = None
    applied_rule_type: Optional[str] = None


# ============================================================================
# Session Request & Action Models
# ============================================================================

class SessionStartRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of customer EV to charge")
    charger_id: int = Field(..., description="Target charger bay ID")
    meter_start_kwh: Decimal = Field(..., ge=0, description="Starting energy meter reading in kWh")
    reservation_id: Optional[int] = Field(None, description="Optional associated reservation ID (null for walk-in)")


class SessionCompleteRequest(BaseModel):
    meter_end_kwh: Decimal = Field(..., ge=0, description="Ending energy meter reading in kWh (>= meter_start_kwh)")


class SessionInterruptRequest(BaseModel):
    meter_end_kwh: Optional[Decimal] = Field(None, ge=0, description="Final meter reading before interruption")
    reason: Optional[str] = Field(None, description="Reason for session interruption")


# Backwards compatibility alias
SessionStopRequest = SessionCompleteRequest


# ============================================================================
# Session Response Model
# ============================================================================

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    reservation_id: Optional[int] = None
    user_id: int
    vehicle_id: int
    charger_id: int
    tariff_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    meter_start_kwh: Decimal
    meter_end_kwh: Optional[Decimal] = None
    energy_consumed_kwh: Optional[Decimal] = None
    status: str

    # Rich relations
    customer: Optional[SessionCustomerInfo] = None
    vehicle: Optional[SessionVehicleInfo] = None
    station: Optional[SessionStationInfo] = None
    charger: Optional[SessionChargerInfo] = None
    tariff: Optional[SessionTariffInfo] = None
    estimated_cost: Optional[Decimal] = None


class MeterReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime
    energy_kwh: Decimal | None
    power_kw: Decimal | None
