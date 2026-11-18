"""
Maintenance Record and Charger Status History ORM models.
Maps to tables: 'maintenance_records' and 'charger_status_history'.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger, Integer, String, Text, Numeric, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="maintenance_records_priority_check"
        ),
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED')",
            name="maintenance_records_status_check"
        ),
        CheckConstraint("maintenance_cost >= 0", name="maintenance_records_cost_check"),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= reported_at",
            name="maintenance_records_resolution_time_check"
        ),
    )

    maintenance_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    charger_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("chargers.charger_id"),
        nullable=False
    )
    reported_by: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id"),
        nullable=False
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(15), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    maintenance_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # Relationships
    charger: Mapped["Charger"] = relationship("Charger", back_populates="maintenance_records")
    reporter: Mapped["User"] = relationship(
        "User", foreign_keys=[reported_by], back_populates="reported_maintenance"
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_maintenance"
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRecord(id={self.maintenance_id}, charger={self.charger_id}, priority='{self.priority}', status='{self.status}')>"


class ChargerStatusHistory(Base):
    __tablename__ = "charger_status_history"
    __table_args__ = (
        CheckConstraint(
            "new_status IN ('ONLINE', 'MAINTENANCE', 'OUT_OF_SERVICE')",
            name="charger_status_history_new_status_check"
        ),
        CheckConstraint(
            "previous_status IS NULL OR previous_status IN ('ONLINE', 'MAINTENANCE', 'OUT_OF_SERVICE')",
            name="charger_status_history_previous_status_check"
        ),
    )

    history_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    charger_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("chargers.charger_id"),
        nullable=False,
        index=True
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    new_status: Mapped[str] = mapped_column(String(25), nullable=False)
    changed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    charger: Mapped["Charger"] = relationship("Charger", back_populates="status_history")
    changed_by_user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<ChargerStatusHistory(id={self.history_id}, charger={self.charger_id}, {self.previous_status}->{self.new_status})>"

