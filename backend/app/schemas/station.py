"""
Pydantic v2 validation schemas for Stations, Chargers, and Geolocation queries.
"""

from datetime import time
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.schemas.vehicle import ConnectorTypeResponse


class ChargerBase(BaseModel):
    charger_code: str = Field(..., min_length=1, max_length=40)
    power_kw: Decimal = Field(..., gt=0)
    operational_status: str = Field("ONLINE", pattern="^(ONLINE|MAINTENANCE|OUT_OF_SERVICE)$")

    @field_validator("charger_code", mode="before")
    @classmethod
    def clean_charger_code(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if not v_clean:
                raise ValueError("Charger code cannot be empty or whitespace")
            return v_clean
        return v


class ChargerCreate(BaseModel):
    connector_type_id: int
    charger_code: str = Field(..., min_length=1, max_length=40)
    power_kw: Decimal = Field(..., gt=0)
    operational_status: Optional[str] = Field("ONLINE", pattern="^(ONLINE|MAINTENANCE|OUT_OF_SERVICE)$")

    @field_validator("charger_code", mode="before")
    @classmethod
    def clean_charger_code(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if not v_clean:
                raise ValueError("Charger code cannot be empty or whitespace")
            return v_clean
        return v


class ChargerUpdate(BaseModel):
    connector_type_id: Optional[int] = None
    charger_code: Optional[str] = Field(None, min_length=1, max_length=40)
    power_kw: Optional[Decimal] = Field(None, gt=0)
    operational_status: Optional[str] = Field(None, pattern="^(ONLINE|MAINTENANCE|OUT_OF_SERVICE)$")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change in audit history")

    @field_validator("charger_code", mode="before")
    @classmethod
    def clean_charger_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_clean = v.strip().upper()
            if not v_clean:
                raise ValueError("Charger code cannot be empty or whitespace")
            return v_clean
        return v


class ChargerResponse(ChargerBase):
    model_config = ConfigDict(from_attributes=True)

    charger_id: int
    station_id: int
    connector_type_id: int
    connector_type: Optional[ConnectorTypeResponse] = None


class StationBase(BaseModel):
    station_name: str = Field(..., min_length=1, max_length=120)
    address: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=80)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    status: str = Field("ACTIVE", pattern="^(ACTIVE|INACTIVE)$")

    @field_validator("station_name", "address", "city", mode="before")
    @classmethod
    def clean_text_fields(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Field cannot be empty or blank")
            return v_clean
        return v

    @model_validator(mode="after")
    def validate_times(self) -> "StationBase":
        if self.opening_time is not None and self.closing_time is not None:
            if self.opening_time == self.closing_time:
                raise ValueError("Opening time and closing time cannot be identical")
        return self


class StationCreate(StationBase):
    operator_id: Optional[int] = None


class StationUpdate(BaseModel):
    station_name: Optional[str] = Field(None, min_length=1, max_length=120)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=80)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|INACTIVE)$")
    operator_id: Optional[int] = None

    @field_validator("station_name", "address", "city", mode="before")
    @classmethod
    def clean_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Field cannot be empty or blank")
            return v_clean
        return v


class StationResponse(StationBase):
    model_config = ConfigDict(from_attributes=True)

    station_id: int
    operator_id: Optional[int] = None
    chargers: List[ChargerResponse] = Field(default_factory=list)
    total_chargers: int = 0
    online_chargers: int = 0


class StationNearbyResponse(StationResponse):
    distance_km: float
    compatible_chargers: List[ChargerResponse] = Field(default_factory=list)
