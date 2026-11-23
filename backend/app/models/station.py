"""
Station and Charger ORM models.
Maps to tables: 'stations' and 'chargers'.
"""

from datetime import time
from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger, Integer, String, Numeric, Time,
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


if TYPE_CHECKING:
    from backend.app.models.maintenance import ChargerStatusHistory
    from backend.app.models.session import ChargingSession
    from backend.app.models.vehicle import ConnectorType
    from backend.app.models.maintenance import MaintenanceRecord
    from backend.app.models.reservation import Reservation
    from backend.app.models.tariff import Tariff
    from backend.app.models.user import User


class Station(Base):
    __tablename__ = "stations"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="stations_status_check"),
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="stations_latitude_check"),
        CheckConstraint("longitude IS NULL OR longitude BETWEEN -180 AND 180", name="stations_longitude_check"),
    )

    station_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    operator_id: Mapped[Optional[int]] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    station_name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    opening_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    closing_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    operator: Mapped[Optional["User"]] = relationship("User", back_populates="stations_operated")
    chargers: Mapped[List["Charger"]] = relationship("Charger", back_populates="station", cascade="all, delete-orphan", lazy="selectin")
    tariffs: Mapped[List["Tariff"]] = relationship("Tariff", back_populates="station")

    def __repr__(self) -> str:
        return f"<Station(id={self.station_id}, name='{self.station_name}', city='{self.city}')>"


class Charger(Base):
    __tablename__ = "chargers"
    __table_args__ = (
        UniqueConstraint("station_id", "charger_code", name="chargers_station_id_charger_code_key"),
        CheckConstraint("power_kw > 0", name="chargers_power_kw_check"),
        CheckConstraint(
            "operational_status IN ('ONLINE', 'MAINTENANCE', 'OUT_OF_SERVICE')",
            name="chargers_operational_status_check"
        ),
    )

    charger_id: Mapped[int] = mapped_column(
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
    connector_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("connector_types.connector_type_id"), nullable=False
    )
    charger_code: Mapped[str] = mapped_column(String(40), nullable=False)
    power_kw: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    operational_status: Mapped[str] = mapped_column(String(25), nullable=False, default="ONLINE")

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="chargers")
    connector_type: Mapped["ConnectorType"] = relationship("ConnectorType", back_populates="chargers", lazy="joined")
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="charger")
    sessions: Mapped[List["ChargingSession"]] = relationship("ChargingSession", back_populates="charger")
    maintenance_records: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="charger"
    )
    status_history: Mapped[List["ChargerStatusHistory"]] = relationship(
        "ChargerStatusHistory", back_populates="charger", order_by="desc(ChargerStatusHistory.changed_at)"
    )

    def __repr__(self) -> str:
        return f"<Charger(id={self.charger_id}, code='{self.charger_code}', status='{self.operational_status}')>"

