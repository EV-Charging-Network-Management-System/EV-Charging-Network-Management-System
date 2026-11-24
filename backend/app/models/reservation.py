"""
Reservation ORM model.
Maps to table: 'reservations'.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    BigInteger, Integer, String, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


if TYPE_CHECKING:
    from backend.app.models.station import Charger
    from backend.app.models.session import ChargingSession
    from backend.app.models.user import User
    from backend.app.models.vehicle import Vehicle


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="reservations_time_window_check"),
        CheckConstraint(
            "status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW')",
            name="reservations_status_check"
        ),
    )

    reservation_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )
    vehicle_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("vehicles.vehicle_id"),
        nullable=False
    )
    charger_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("chargers.charger_id"),
        nullable=False,
        index=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reservations")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="reservations")
    charger: Mapped["Charger"] = relationship("Charger", back_populates="reservations")
    session: Mapped[Optional["ChargingSession"]] = relationship(
        "ChargingSession", back_populates="reservation", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Reservation(id={self.reservation_id}, user={self.user_id}, status='{self.status}')>"

