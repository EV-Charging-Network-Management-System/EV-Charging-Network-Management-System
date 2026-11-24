"""
Invoice and Payment ORM models.
Maps to tables: 'invoices' and 'payments'.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger, Integer, String, Numeric, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


if TYPE_CHECKING:
    from backend.app.models.session import ChargingSession


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("energy_kwh >= 0", name="invoices_energy_kwh_check"),
        CheckConstraint("price_per_kwh >= 0", name="invoices_price_per_kwh_check"),
        CheckConstraint("session_fee >= 0", name="invoices_session_fee_check"),
        CheckConstraint("tax_rate_percent BETWEEN 0 AND 100", name="invoices_tax_rate_check"),
        CheckConstraint("energy_charge >= 0", name="invoices_energy_charge_check"),
        CheckConstraint("tax_amount >= 0", name="invoices_tax_amount_check"),
        CheckConstraint("total_amount >= 0", name="invoices_total_amount_check"),
        CheckConstraint("status IN ('UNPAID', 'PAID', 'VOID')", name="invoices_status_check"),
    )

    invoice_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), ForeignKey("charging_sessions.session_id"), nullable=False, unique=True
    )
    energy_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    session_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    tax_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    energy_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNPAID", index=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    session: Mapped["ChargingSession"] = relationship("ChargingSession", back_populates="invoice")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="invoice")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.invoice_id}, session={self.session_id}, total={self.total_amount}, status='{self.status}')>"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="payments_amount_check"),
        CheckConstraint(
            "payment_method IN ('UPI', 'CARD', 'CASH', 'DEMO')",
            name="payments_method_check"
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')",
            name="payments_status_check"
        ),
    )

    payment_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    invoice_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.invoice_id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False, default="DEMO")
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.payment_id}, invoice={self.invoice_id}, amount={self.amount}, status='{self.status}')>"

