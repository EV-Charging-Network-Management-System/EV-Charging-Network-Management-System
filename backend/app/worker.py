"""Run recurring maintenance against a migrated PostgreSQL database."""

import argparse
import logging
from datetime import datetime, timedelta, timezone
from time import sleep

from fastapi import HTTPException
from sqlalchemy import exists, select, text, update
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, engine
from backend.app.models.billing import Invoice
from backend.app.models.maintenance import ChargerStatusHistory
from backend.app.models.reservation import Reservation
from backend.app.models.session import ChargingSession
from backend.app.models.station import Charger
from backend.app.models.workflow import ChargerHeartbeat
from backend.app.services.billing_service import generate_invoice_for_session

LOGGER = logging.getLogger(__name__)
WORKER_LOCK = 728115305


def expire_reservations(db: Session, now: datetime) -> int:
    stale = (
        select(Reservation.reservation_id)
        .where(
            Reservation.status.in_(("PENDING", "CONFIRMED")),
            Reservation.end_at < now - timedelta(minutes=30),
            ~exists().where(
                ChargingSession.reservation_id == Reservation.reservation_id,
                ChargingSession.status == "ACTIVE",
            ),
        )
        .order_by(Reservation.end_at, Reservation.reservation_id)
        .limit(100)
        .with_for_update(of=Reservation, skip_locked=True)
    )
    ids = db.scalars(stale).all()
    if not ids:
        return 0
    expired = db.scalars(
        update(Reservation)
        .where(
            Reservation.reservation_id.in_(ids),
            ~exists().where(
                ChargingSession.reservation_id == Reservation.reservation_id,
                ChargingSession.status == "ACTIVE",
            ),
        )
        .values(status="NO_SHOW")
        .returning(Reservation.reservation_id)
    ).all()
    return len(expired)


def mark_stale_chargers(db: Session, now: datetime) -> int:
    stale = db.scalars(
        select(ChargerHeartbeat)
        .join(Charger, Charger.charger_id == ChargerHeartbeat.charger_id)
        .where(ChargerHeartbeat.last_seen_at < now - timedelta(minutes=5), Charger.operational_status == "ONLINE")
        .order_by(ChargerHeartbeat.last_seen_at)
        .limit(100)
        .with_for_update(of=ChargerHeartbeat, skip_locked=True)
    ).all()
    flagged = 0
    for heartbeat in stale:
        charger = db.scalar(
            select(Charger).where(Charger.charger_id == heartbeat.charger_id)
            .with_for_update(of=Charger, skip_locked=True)
        )
        if charger is None or charger.operational_status != "ONLINE":
            continue
        charger.operational_status = "OUT_OF_SERVICE"
        db.add(ChargerStatusHistory(
            charger_id=charger.charger_id,
            previous_status="ONLINE",
            new_status="OUT_OF_SERVICE",
            reason="No charger messages received for five minutes",
        ))
        flagged += 1
    return flagged


def bill_newly_closed_sessions(now: datetime) -> int:
    """Scan a bounded recent window, with the existing invoice invariant as a guard."""
    with SessionLocal() as db:
        ids = db.scalars(
            select(ChargingSession.session_id)
            .where(
                ChargingSession.status.in_(("COMPLETED", "INTERRUPTED")),
                ChargingSession.ended_at >= now - timedelta(days=7),
                ~exists().where(Invoice.session_id == ChargingSession.session_id),
            )
            .order_by(ChargingSession.ended_at, ChargingSession.session_id)
            .limit(100)
        ).all()
    created = 0
    for session_id in ids:
        with SessionLocal() as db:
            try:
                generate_invoice_for_session(session_id, current_user=None, db=db)
                created += 1
            except HTTPException as exc:
                if exc.status_code != 409:
                    LOGGER.warning("Invoice job skipped session id=%s status=%s", session_id, exc.status_code)
    return created


def run_cycle(now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    with engine.connect() as lock:
        acquired = lock.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": WORKER_LOCK})
        lock.commit()
        if not acquired:
            return
        try:
            with SessionLocal.begin() as db:
                expired = expire_reservations(db, now)
                flagged = mark_stale_chargers(db, now)
            invoiced = bill_newly_closed_sessions(now)
            LOGGER.info("Maintenance cycle expired=%s offline=%s invoiced=%s", expired, flagged, invoiced)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": WORKER_LOCK})
            lock.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.once:
        run_cycle()
        return
    while True:
        try:
            run_cycle()
        except Exception:
            LOGGER.exception("Maintenance cycle failed")
        sleep(60)


if __name__ == "__main__":
    main()
