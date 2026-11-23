"""Notify active session views after the surrounding database transaction commits."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def notify_session(db: Session, session_id: int) -> None:
    db.execute(text("SELECT pg_notify(:channel, '')"), {"channel": f"ev_session_{session_id}"})
