"""
Pydantic v2 validation schemas for Invoices, Payments, and Reconciliation Reports.
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class InvoiceCustomerInfo(BaseModel):
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None


class InvoiceStationInfo(BaseModel):
    station_id: int
    station_name: str
    charger_id: int
    charger_code: str
    address: str
    city: str


class PaymentCreate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, description="Amount to pay. If omitted, full outstanding balance is charged.")
    payment_method: str = Field("DEMO", pattern="^(UPI|CARD|CASH|DEMO)$")
    transaction_reference: Optional[str] = Field(None, max_length=120)
    simulate_failure: bool = Field(False, description="Simulate a gateway payment decline for testing reconciliation.")


class PaymentRefundRequest(BaseModel):
    reason: Optional[str] = Field("Customer requested refund", max_length=255)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    transaction_reference: Optional[str] = None
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    invoice_number: str
    session_id: int
    energy_kwh: Decimal
    price_per_kwh: Decimal
    session_fee: Decimal
    tax_rate_percent: Decimal
    energy_charge: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    issued_at: datetime
    customer: Optional[InvoiceCustomerInfo] = None
    station: Optional[InvoiceStationInfo] = None
    amount_paid: Decimal = Decimal("0.00")
    balance_due: Decimal = Decimal("0.00")
    payments: List[PaymentResponse] = Field(default_factory=list)


class DailyRevenue(BaseModel):
    date: str
    amount: Decimal
    invoice_count: int


class MonthlyRevenue(BaseModel):
    month: str
    amount: Decimal
    invoice_count: int


class StationRevenue(BaseModel):
    station_id: int
    station_name: str
    city: str
    total_billed: Decimal
    total_collected: Decimal
    session_count: int


class PaymentMethodBreakdown(BaseModel):
    payment_method: str
    total_collected: Decimal
    transaction_count: int


class RevenueReportResponse(BaseModel):
    total_billed_revenue: Decimal
    total_collected_revenue: Decimal
    outstanding_invoice_amount: Decimal
    failed_payment_count: int
    refunded_payment_count: int
    daily_revenue: List[DailyRevenue] = Field(default_factory=list)
    monthly_revenue: List[MonthlyRevenue] = Field(default_factory=list)
    station_wise_revenue: List[StationRevenue] = Field(default_factory=list)
    payment_method_breakdown: List[PaymentMethodBreakdown] = Field(default_factory=list)
    note: str = "Billed revenue represents total invoiced charges; collected revenue represents confirmed payments minus refunds."
