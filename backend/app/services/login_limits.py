"""Bound repeated password guesses for each normalized account."""

import hmac
from datetime import datetime, timezone
from time import time

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.workflow import LoginWindow

WINDOW_SECONDS = 300
MAX_ATTEMPTS = 5


def consume_login_attempt(db: Session, account: str) -> None:
    now = int(time())
    window = (now // WINDOW_SECONDS) * WINDOW_SECONDS
    subject = hmac.digest(settings.SECRET_KEY.encode(), account.encode(), "sha256").hex()
    statement = (
        insert(LoginWindow)
        .values(subject_hash=subject, window_start=datetime.fromtimestamp(window, timezone.utc), attempts=1)
        .on_conflict_do_update(
            index_elements=[LoginWindow.subject_hash, LoginWindow.window_start],
            set_={"attempts": LoginWindow.attempts + 1},
            where=LoginWindow.attempts < MAX_ATTEMPTS,
        )
        .returning(LoginWindow.attempts)
    )
    counted = db.scalar(statement)
    db.commit()
    if counted is None:
        raise HTTPException(
            status_code=429, detail="Too many sign-in attempts. Try again shortly.",
            headers={"Retry-After": str(window + WINDOW_SECONDS - now)},
        )
    # Clean up lazily even if the deployment does not run background jobs.
    if counted == 1:
        cutoff = datetime.fromtimestamp(window - 3600, timezone.utc)
        db.execute(delete(LoginWindow).where(LoginWindow.window_start < cutoff))
        db.commit()
