"""
Pydantic v2 validation schemas for Vehicles and Connector Types.
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConnectorTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    connector_type_id: int
    type_name: str
    description: Optional[str] = None


class VehicleBase(BaseModel):
    registration_number: str = Field(..., min_length=1, max_length=30)
    make: str = Field(..., min_length=1, max_length=60)
    model: str = Field(..., min_length=1, max_length=80)
    battery_capacity_kwh: Optional[Decimal] = Field(None, gt=0)

    @field_validator("registration_number", mode="before")
    @classmethod
    def clean_reg_number(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if not v_clean:
                raise ValueError("Registration number cannot be empty or blank")
            return v_clean
        return v

    @field_validator("make", "model", mode="before")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Field cannot be empty or blank")
            return v_clean
        return v


class VehicleCreate(VehicleBase):
    connector_type_ids: List[int] = Field(default_factory=list)


class VehicleUpdate(BaseModel):
    make: Optional[str] = Field(None, min_length=1, max_length=60)
    model: Optional[str] = Field(None, min_length=1, max_length=80)
    registration_number: Optional[str] = Field(None, min_length=1, max_length=30)
    battery_capacity_kwh: Optional[Decimal] = Field(None, gt=0)

    @field_validator("registration_number", mode="before")
    @classmethod
    def clean_reg_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_clean = v.strip().upper()
            if not v_clean:
                raise ValueError("Registration number cannot be empty or blank")
            return v_clean
        return v

    @field_validator("make", "model", mode="before")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Field cannot be empty or blank")
            return v_clean
        return v


class VehicleConnectorUpdate(BaseModel):
    connector_type_ids: List[int] = Field(
        ...,
        description="List of connector type IDs to associate with this vehicle"
    )


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    owner_user_id: int
    created_at: datetime
    connector_types: List[ConnectorTypeResponse] = Field(default_factory=list)
