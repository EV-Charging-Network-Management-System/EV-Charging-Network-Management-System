"""Time-series readings recorded by a charger during a session."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class MeterReading(Base):
    __tablename__ = "meter_readings"
    __table_args__ = (
        CheckConstraint("energy_kwh >= 0", name="meter_readings_energy_nonnegative"),
        CheckConstraint("power_kw >= 0", name="meter_readings_power_nonnegative"),
        CheckConstraint("energy_kwh IS NOT NULL OR power_kw IS NOT NULL", name="meter_readings_has_value"),
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("charging_sessions.session_id", ondelete="CASCADE"), primary_key=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    energy_kwh: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    power_kw: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
