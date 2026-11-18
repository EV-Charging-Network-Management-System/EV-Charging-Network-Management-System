"""
Tariff and Dynamic Pricing Rule ORM models.
Maps to tables: 'tariffs' and 'pricing_rules'.
"""

from datetime import datetime, time
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger, Integer, String, Numeric, Time, DateTime,
    ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Tariff(Base):
    __tablename__ = "tariffs"
    __table_args__ = (
        CheckConstraint("base_price_per_kwh >= 0", name="tariffs_base_price_check"),
        CheckConstraint("session_fee >= 0", name="tariffs_session_fee_check"),
        CheckConstraint("tax_rate_percent BETWEEN 0 AND 100", name="tariffs_tax_rate_check"),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="tariffs_validity_check"),
    )

    tariff_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    station_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("stations.station_id"),
        nullable=False,
        index=True
    )
    connector_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("connector_types.connector_type_id"), nullable=True
    )
    base_price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    session_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    tax_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="tariffs")
    connector_type: Mapped[Optional["ConnectorType"]] = relationship("ConnectorType", back_populates="tariffs")
    pricing_rules: Mapped[List["PricingRule"]] = relationship(
        "PricingRule", back_populates="tariff", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["ChargingSession"]] = relationship("ChargingSession", back_populates="tariff")

    def __repr__(self) -> str:
        return f"<Tariff(id={self.tariff_id}, base_price={self.base_price_per_kwh})>"


class PricingRule(Base):
    __tablename__ = "pricing_rules"
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('PEAK_HOUR', 'OFF_PEAK', 'HIGH_DEMAND')",
            name="pricing_rules_rule_type_check"
        ),
        CheckConstraint("price_multiplier > 0", name="pricing_rules_multiplier_check"),
        CheckConstraint(
            "demand_threshold_percent IS NULL OR demand_threshold_percent BETWEEN 0 AND 100",
            name="pricing_rules_demand_threshold_check"
        ),
    )

    rule_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    tariff_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("tariffs.tariff_id", ondelete="CASCADE"),
        nullable=False
    )
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    demand_threshold_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    price_multiplier: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("1.000"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="pricing_rules")

    def __repr__(self) -> str:
        return f"<PricingRule(id={self.rule_id}, type='{self.rule_type}', mult={self.price_multiplier})>"

