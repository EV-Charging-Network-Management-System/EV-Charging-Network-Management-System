"""Read administrative changes without exposing authentication or payment secrets."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_admin
from backend.app.core.database import get_db
from backend.app.models.workflow import AdminAuditEvent


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    actor_id: int
    action: str
    resource_id: int
    details: dict[str, Any]
    occurred_at: datetime


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(
    db: Session = Depends(get_db),
    before: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=100),
    action: str | None = Query(None, max_length=40),
):
    query = select(AdminAuditEvent)
    if before is not None:
        query = query.where(AdminAuditEvent.event_id < before)
    if action is not None:
        query = query.where(AdminAuditEvent.action == action)
    return db.scalars(query.order_by(AdminAuditEvent.event_id.desc()).limit(limit)).all()
