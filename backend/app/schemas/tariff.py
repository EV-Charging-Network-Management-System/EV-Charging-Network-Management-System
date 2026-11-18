"""
Pydantic v2 validation schemas for Tariffs, Pricing Rules, and Dynamic Pricing Quotes.
"""

from datetime import datetime, time
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================================
# Pricing Rule Schemas
# ============================================================================

class PricingRuleBase(BaseModel):
    rule_type: str = Field(..., description="PEAK_HOUR, OFF_PEAK, or HIGH_DEMAND")
    start_time: Optional[time] = Field(None, description="Start time for time-of-use rules")
    end_time: Optional[time] = Field(None, description="End time for time-of-use rules")
    demand_threshold_percent: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Station demand threshold percentage"
    )
    price_multiplier: Decimal = Field(..., gt=0, description="Multiplier applied to base price (e.g. 1.200)")
    priority: int = Field(default=1, ge=1, description="Rule evaluation priority (higher number takes precedence)")
    is_active: bool = Field(default=True, description="Whether rule is currently active")


class PricingRuleCreate(PricingRuleBase):
    tariff_id: int = Field(..., description="Parent tariff ID")

    @model_validator(mode="after")
    def validate_rule_parameters(self) -> "PricingRuleCreate":
        rule_type = self.rule_type.upper()
        if rule_type in ("PEAK_HOUR", "OFF_PEAK"):
            if self.start_time is None or self.end_time is None:
                raise ValueError(f"{rule_type} rule requires both start_time and end_time")
        elif rule_type == "HIGH_DEMAND":
            if self.demand_threshold_percent is None:
                raise ValueError("HIGH_DEMAND rule requires demand_threshold_percent")
        else:
            raise ValueError(f"Invalid rule_type: {self.rule_type}. Must be PEAK_HOUR, OFF_PEAK, or HIGH_DEMAND")
        return self


class PricingRuleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    demand_threshold_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    price_multiplier: Optional[Decimal] = Field(None, gt=0)
    priority: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class PricingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: int
    tariff_id: int
    rule_type: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    demand_threshold_percent: Optional[Decimal] = None
    price_multiplier: Decimal
    priority: int
    is_active: bool


# ============================================================================
# Tariff Schemas
# ============================================================================

class TariffBase(BaseModel):
    station_id: int = Field(..., description="Target station ID")
    connector_type_id: Optional[int] = Field(None, description="Optional connector type ID (null = station-wide default)")
    base_price_per_kwh: Decimal = Field(..., ge=0, description="Base rate per kWh in INR")
    session_fee: Decimal = Field(default=Decimal("0.00"), ge=0, description="Flat session fee in INR")
    tax_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Tax rate percentage")
    valid_from: datetime = Field(..., description="Activation start datetime (with timezone)")
    valid_to: Optional[datetime] = Field(None, description="Optional expiration datetime (with timezone)")


class TariffCreate(TariffBase):
    @model_validator(mode="after")
    def validate_validity_window(self) -> "TariffCreate":
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be strictly after valid_from")
        return self


class TariffUpdate(BaseModel):
    base_price_per_kwh: Optional[Decimal] = Field(None, ge=0)
    session_fee: Optional[Decimal] = Field(None, ge=0)
    tax_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    valid_to: Optional[datetime] = None


class TariffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tariff_id: int
    station_id: int
    station_name: Optional[str] = None
    connector_type_id: Optional[int] = None
    connector_type_name: Optional[str] = None
    base_price_per_kwh: Decimal
    session_fee: Decimal
    tax_rate_percent: Decimal
    valid_from: datetime
    valid_to: Optional[datetime] = None
    pricing_rules: List[PricingRuleResponse] = Field(default_factory=list)


# ============================================================================
# Dynamic Pricing Quote & Demand Schemas
# ============================================================================

class AppliedRuleInfo(BaseModel):
    rule_id: int
    rule_type: str
    price_multiplier: Decimal
    priority: int
    description: Optional[str] = None


class PricingQuoteRequest(BaseModel):
    station_id: int = Field(..., description="Target charging station ID")
    connector_type_id: Optional[int] = Field(None, description="Optional connector type ID")
    estimated_energy_kwh: Decimal = Field(..., ge=0, description="Estimated energy to charge in kWh")
    start_at: Optional[datetime] = Field(None, description="Requested session start datetime (defaults to now)")
    end_at: Optional[datetime] = Field(None, description="Requested session end datetime (defaults to start_at + 1h)")


class PricingQuoteResponse(BaseModel):
    station_id: int
    station_name: Optional[str] = None
    tariff_id: int
    connector_type_id: Optional[int] = None
    connector_type_name: Optional[str] = None
    base_price_per_kwh: Decimal
    multiplier: Decimal
    effective_rate_per_kwh: Decimal
    estimated_energy_kwh: Decimal
    energy_charge: Decimal
    session_fee: Decimal
    subtotal: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str = "INR"
    station_demand_percent: Decimal
    applied_rule: Optional[AppliedRuleInfo] = None
    calculation_timestamp: datetime


class StationDemandResponse(BaseModel):
    station_id: int
    total_online_chargers: int
    occupied_chargers: int
    demand_percent: Decimal
    as_of: datetime


# Backwards compatibility aliases
TariffEstimateRequest = PricingQuoteRequest
TariffEstimateResponse = PricingQuoteResponse
