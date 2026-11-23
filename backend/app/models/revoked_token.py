"""Record explicitly revoked JWT IDs until their original expiration."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
