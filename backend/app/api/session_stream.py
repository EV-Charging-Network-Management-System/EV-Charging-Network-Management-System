"""Bounded session event stream backed by PostgreSQL notifications."""

from collections.abc import Iterator
from time import time

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from psycopg import sql
from sqlalchemy.orm import Session

from backend.app.api.deps import get_access_token, get_current_active_user
from backend.app.core.database import engine, get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.services.session_service import get_session_by_id

router = APIRouter()


def session_updates(session_id: int, duration: float) -> Iterator[str]:
    url = engine.url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
        connection.execute(sql.SQL("LISTEN {}").format(sql.Identifier(f"ev_session_{session_id}")))
        # Refresh after LISTEN is armed to cover updates between page load and subscription.
        yield "event: changed\ndata: {}\n\n"
        for _ in connection.notifies(timeout=duration):
            yield "event: changed\ndata: {}\n\n"


@router.get("/sessions/{session_id}/events")
def stream_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(get_access_token),
    db: Session = Depends(get_db),
):
    get_session_by_id(session_id=session_id, current_user=current_user, db=db)
    duration = min(25.0, decode_access_token(token)["exp"] - time())
    if duration <= 0:
        raise HTTPException(status_code=401, detail="Session expired.")
    db.close()
    return StreamingResponse(
        session_updates(session_id, duration),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
