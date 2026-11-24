"""
User ORM model representing customers, station operators, and administrators.
Maps exactly to table 'users' in PostgreSQL.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


if TYPE_CHECKING:
    from backend.app.models.session import ChargingSession
    from backend.app.models.maintenance import MaintenanceRecord
    from backend.app.models.reservation import Reservation
    from backend.app.models.station import Station
    from backend.app.models.vehicle import Vehicle


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('CUSTOMER', 'OPERATOR', 'ADMIN')", name="users_role_check"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="CUSTOMER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="owner")
    stations_operated: Mapped[List["Station"]] = relationship("Station", back_populates="operator")
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="user")
    sessions: Mapped[List["ChargingSession"]] = relationship("ChargingSession", back_populates="user")
    reported_maintenance: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord",
        foreign_keys="[MaintenanceRecord.reported_by]",
        back_populates="reporter"
    )
    assigned_maintenance: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord",
        foreign_keys="[MaintenanceRecord.assigned_to]",
        back_populates="assignee"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, email='{self.email}', role='{self.role}')>"
