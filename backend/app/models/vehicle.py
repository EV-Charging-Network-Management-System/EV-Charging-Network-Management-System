"""
Vehicle and Connector Type ORM models.
Maps to tables: 'connector_types', 'vehicles', and 'vehicle_connector_types'.
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
    from backend.app.models.station import Charger
    from backend.app.models.session import ChargingSession
    from backend.app.models.reservation import Reservation
    from backend.app.models.tariff import Tariff
    from backend.app.models.user import User


class ConnectorType(Base):
    __tablename__ = "connector_types"

    connector_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    chargers: Mapped[List["Charger"]] = relationship("Charger", back_populates="connector_type")
    tariffs: Mapped[List["Tariff"]] = relationship("Tariff", back_populates="connector_type")
    vehicle_connector_types: Mapped[List["VehicleConnectorType"]] = relationship(
        "VehicleConnectorType", back_populates="connector_type"
    )

    def __repr__(self) -> str:
        return f"<ConnectorType(id={self.connector_type_id}, type_name='{self.type_name}')>"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint(
            "battery_capacity_kwh IS NULL OR battery_capacity_kwh > 0",
            name="vehicles_battery_capacity_check"
        ),
    )

    vehicle_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )
    registration_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    make: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    battery_capacity_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="vehicles")
    vehicle_connector_types: Mapped[List["VehicleConnectorType"]] = relationship(
        "VehicleConnectorType",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="vehicle")
    sessions: Mapped[List["ChargingSession"]] = relationship("ChargingSession", back_populates="vehicle")

    @property
    def connector_types(self) -> List["ConnectorType"]:
        return [vct.connector_type for vct in self.vehicle_connector_types if vct.connector_type]

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.vehicle_id}, reg='{self.registration_number}', model='{self.make} {self.model}')>"


class VehicleConnectorType(Base):
    __tablename__ = "vehicle_connector_types"

    vehicle_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        primary_key=True
    )
    connector_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connector_types.connector_type_id"),
        primary_key=True
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="vehicle_connector_types")
    connector_type: Mapped["ConnectorType"] = relationship(
        "ConnectorType",
        back_populates="vehicle_connector_types",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<VehicleConnectorType(vehicle_id={self.vehicle_id}, connector_type_id={self.connector_type_id})>"

