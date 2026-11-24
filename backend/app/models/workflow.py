"""Transaction records for API mutations and administrative actions."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class IdempotentOperation(Base):
    __tablename__ = "idempotent_operations"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    operation: Mapped[str] = mapped_column(String(80), primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class AdminAuditEvent(Base):
    __tablename__ = "admin_audit_events"

    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[int] = mapped_column(BigInteger)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginWindow(Base):
    __tablename__ = "login_windows"

    subject_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, index=True)
    attempts: Mapped[int]


class ChargerHeartbeat(Base):
    __tablename__ = "charger_heartbeats"

    charger_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chargers.charger_id", ondelete="CASCADE"), primary_key=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
