"""
Pydantic v2 validation schemas for Reservations, Availability, and Slot Conflict Engine.
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from backend.app.schemas.tariff import PricingQuoteResponse


# ============================================================================
# Nested Display Models
# ============================================================================

class ReservationCustomerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None


class ReservationVehicleInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    make: str
    model: str
    registration_number: str
    battery_capacity_kwh: Optional[Decimal] = None


class ReservationStationInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: int
    station_name: str
    address: str
    city: str


class ReservationChargerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    charger_id: int
    charger_code: str
    power_kw: Decimal
    connector_type_id: int
    connector_type_name: Optional[str] = None


# ============================================================================
# Reservation Request & Response Schemas
# ============================================================================

class ReservationCreate(BaseModel):
    vehicle_id: int = Field(..., description="ID of customer EV to charge")
    charger_id: int = Field(..., description="Target charger bay ID")
    start_at: datetime = Field(..., description="Slot start time (ISO 8601 with timezone)")
    end_at: datetime = Field(..., description="Slot end time (ISO 8601 with timezone)")

    @model_validator(mode="after")
    def validate_time_window(self) -> "ReservationCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be strictly after start_at")
        return self


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reservation_id: int
    user_id: int
    vehicle_id: int
    charger_id: int
    start_at: datetime
    end_at: datetime
    status: str
    created_at: datetime

    # Rich relationships
    customer: Optional[ReservationCustomerInfo] = None
    vehicle: Optional[ReservationVehicleInfo] = None
    station: Optional[ReservationStationInfo] = None
    charger: Optional[ReservationChargerInfo] = None


class ReservationCancelResponse(BaseModel):
    reservation_id: int
    status: str
    message: str


# ============================================================================
# Availability Inspection Schemas
# ============================================================================

class AvailableChargerResponse(BaseModel):
    charger_id: int
    charger_code: str
    power_kw: Decimal
    connector_type_id: int
    connector_type_name: str
    operational_status: str
    is_available: bool
    unavailability_reason: Optional[str] = None
    estimated_price: Optional[PricingQuoteResponse] = None


class ChargerAvailabilityResponse(BaseModel):
    station_id: int
    station_name: str
    vehicle_id: int
    vehicle_make_model: str
    start_at: datetime
    end_at: datetime
    total_compatible_chargers: int
    available_chargers_count: int
    chargers: List[AvailableChargerResponse]


# Backwards compatibility alias
ReservationBase = ReservationCreate
ReservationStatusUpdate = ReservationCancelResponse
