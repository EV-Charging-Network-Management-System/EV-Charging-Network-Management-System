"""
Charging Session ORM model.
Maps to table: 'charging_sessions'.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger, Integer, String, Numeric, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


if TYPE_CHECKING:
    from backend.app.models.station import Charger
    from backend.app.models.billing import Invoice
    from backend.app.models.reservation import Reservation
    from backend.app.models.tariff import Tariff
    from backend.app.models.user import User
    from backend.app.models.vehicle import Vehicle


class ChargingSession(Base):
    __tablename__ = "charging_sessions"
    __table_args__ = (
        CheckConstraint("meter_start_kwh >= 0", name="charging_sessions_meter_start_check"),
        CheckConstraint(
            "meter_end_kwh IS NULL OR meter_end_kwh >= meter_start_kwh",
            name="charging_sessions_meter_end_check"
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="charging_sessions_time_check"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'INTERRUPTED')",
            name="charging_sessions_status_check"
        ),
        CheckConstraint(
            "(status = 'ACTIVE' AND ended_at IS NULL AND meter_end_kwh IS NULL) OR "
            "(status IN ('COMPLETED', 'INTERRUPTED') AND ended_at IS NOT NULL AND meter_end_kwh IS NOT NULL)",
            name="charging_sessions_state_check"
        ),
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    reservation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), ForeignKey("reservations.reservation_id"), nullable=True, unique=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("vehicles.vehicle_id"), nullable=False)
    charger_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("chargers.charger_id"), nullable=False, index=True)
    tariff_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("tariffs.tariff_id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    meter_start_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    meter_end_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    reservation: Mapped[Optional["Reservation"]] = relationship("Reservation", back_populates="session")
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="sessions")
    charger: Mapped["Charger"] = relationship("Charger", back_populates="sessions")
    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="sessions")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="session", uselist=False)

    @property
    def energy_consumed_kwh(self) -> Optional[Decimal]:
        if self.meter_end_kwh is not None:
            return self.meter_end_kwh - self.meter_start_kwh
        return None

    def __repr__(self) -> str:
        return f"<ChargingSession(id={self.session_id}, charger={self.charger_id}, status='{self.status}')>"

