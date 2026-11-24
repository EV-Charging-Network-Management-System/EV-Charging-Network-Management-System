"""Handle the subset of OCPP 1.6J used by the charger simulator."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from pydantic import AwareDatetime, BaseModel, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.models.maintenance import ChargerStatusHistory
from backend.app.models.meter_reading import MeterReading
from backend.app.models.reservation import Reservation
from backend.app.models.session import ChargingSession
from backend.app.models.station import Charger
from backend.app.models.user import User
from backend.app.schemas.session import SessionCompleteRequest, SessionStartRequest
from backend.app.services.session_events import notify_session
from backend.app.services.session_service import complete_charging_session, start_charging_session


class OcppError(Exception):
    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description


class Boot(BaseModel):
    chargePointVendor: str = Field(min_length=1, max_length=20)
    chargePointModel: str = Field(min_length=1, max_length=20)


class Status(BaseModel):
    connectorId: int = Field(ge=0, le=1)
    status: str = Field(max_length=30)
    errorCode: str = Field(max_length=30)


class Start(BaseModel):
    connectorId: int = Field(ge=1, le=1)
    idTag: str = Field(min_length=1, max_length=20)
    meterStart: int = Field(ge=0, le=999999999999)
    timestamp: AwareDatetime
    reservationId: int = Field(gt=0)


class Sample(BaseModel):
    value: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    measurand: str = "Energy.Active.Import.Register"
    unit: str = "Wh"


class Reading(BaseModel):
    timestamp: AwareDatetime
    sampledValue: list[Sample] = Field(min_length=1, max_length=12)


class MeterValues(BaseModel):
    connectorId: int = Field(ge=1, le=1)
    transactionId: int = Field(gt=0)
    meterValue: list[Reading] = Field(min_length=1, max_length=100)


class Stop(BaseModel):
    transactionId: int = Field(gt=0)
    meterStop: int = Field(ge=0, le=999999999999)
    timestamp: AwareDatetime


def _device_transaction(db: Session, charger_id: int, session_id: int) -> ChargingSession:
    session = db.scalar(
        select(ChargingSession)
        .where(ChargingSession.session_id == session_id, ChargingSession.charger_id == charger_id)
        .with_for_update(of=ChargingSession)
    )
    if session is None:
        raise OcppError("SecurityError", "Transaction is not assigned to this charger.")
    return session


def _status(db: Session, charger_id: int, notice: Status) -> None:
    values = {"Faulted": "OUT_OF_SERVICE", "Unavailable": "OUT_OF_SERVICE", "Available": "ONLINE"}
    new_status = values.get(notice.status)
    if new_status is None:
        return
    charger = db.scalar(select(Charger).where(Charger.charger_id == charger_id).with_for_update(of=Charger))
    if charger is None or charger.operational_status in {new_status, "MAINTENANCE"}:
        return
    if new_status == "ONLINE" and charger.operational_status == "OUT_OF_SERVICE":
        # An operator must clear an out-of-service bay.
        return
    db.add(ChargerStatusHistory(charger_id=charger_id, previous_status=charger.operational_status,
                                new_status=new_status, reason="Reported by charging device"))
    charger.operational_status = new_status
    db.commit()


def _start(db: Session, charger_id: int, message: Start, driver_tags: dict[str, int]) -> dict:
    driver_id = driver_tags.get(message.idTag)
    reservation = db.get(Reservation, message.reservationId)
    if not driver_id or not reservation or reservation.user_id != driver_id or reservation.charger_id != charger_id:
        return {"transactionId": 0, "idTagInfo": {"status": "Invalid"}}
    driver = db.get(User, driver_id)
    if driver is None or not driver.is_active or driver.role != "CUSTOMER":
        return {"transactionId": 0, "idTagInfo": {"status": "Blocked"}}

    start_kwh = Decimal(message.meterStart) / 1000
    existing = db.scalar(select(ChargingSession).where(ChargingSession.reservation_id == reservation.reservation_id))
    if existing and existing.meter_start_kwh == start_kwh:
        return {"transactionId": existing.session_id, "idTagInfo": {"status": "Accepted"}}

    session = start_charging_session(
        SessionStartRequest(vehicle_id=reservation.vehicle_id, charger_id=charger_id,
                            reservation_id=reservation.reservation_id, meter_start_kwh=start_kwh),
        driver, db,
    )
    return {"transactionId": session.session_id, "idTagInfo": {"status": "Accepted"}}


def _store_readings(db: Session, session: ChargingSession, readings: list[Reading]) -> None:
    if session.status != "ACTIVE":
        raise OcppError("PropertyConstraintViolation", "Transaction is no longer active.")
    batch = []
    for reading in readings:
        if reading.timestamp < session.started_at - timedelta(seconds=30):
            raise OcppError("PropertyConstraintViolation", "Reading predates the session.")
        if reading.timestamp > datetime.now(timezone.utc) + timedelta(minutes=2):
            raise OcppError("PropertyConstraintViolation", "Reading timestamp is in the future.")
        values = {}
        for sample in reading.sampledValue:
            if sample.measurand == "Energy.Active.Import.Register" and sample.unit in {"Wh", "kWh"}:
                energy = sample.value / 1000 if sample.unit == "Wh" else sample.value
                if not session.meter_start_kwh <= energy < Decimal("1000000000"):
                    raise OcppError("PropertyConstraintViolation", "Invalid cumulative energy reading.")
                values["energy_kwh"] = energy
            if sample.measurand == "Power.Active.Import" and sample.unit in {"W", "kW"}:
                power = sample.value / 1000 if sample.unit == "W" else sample.value
                if power >= Decimal("10000000"):
                    raise OcppError("PropertyConstraintViolation", "Invalid power reading.")
                values["power_kw"] = power
        if values:
            batch.append(dict(session_id=session.session_id, recorded_at=reading.timestamp, **values))
    for reading in batch:
        db.execute(insert(MeterReading).values(**reading).on_conflict_do_nothing())
    if batch:
        notify_session(db, session.session_id)
    db.commit()


def _stop(db: Session, session: ChargingSession, message: Stop) -> dict:
    end_kwh = Decimal(message.meterStop) / 1000
    if session.status == "COMPLETED" and session.meter_end_kwh == end_kwh:
        return {"idTagInfo": {"status": "Accepted"}}
    highest = db.scalar(select(func.max(MeterReading.energy_kwh)).where(MeterReading.session_id == session.session_id))
    if highest is not None and end_kwh < highest:
        raise OcppError("PropertyConstraintViolation", "Closing meter is below recorded energy.")
    complete_charging_session(session.session_id, SessionCompleteRequest(meter_end_kwh=end_kwh), session.user, db)
    return {"idTagInfo": {"status": "Accepted"}}


def dispatch(db: Session, charger_id: int, driver_tags: dict[str, int], action: str, payload: dict) -> dict:
    try:
        if action == "BootNotification":
            Boot.model_validate(payload)
            return {"status": "Accepted", "interval": 60, "currentTime": datetime.now(timezone.utc).isoformat()}
        if action == "Heartbeat":
            return {"currentTime": datetime.now(timezone.utc).isoformat()}
        if action == "StatusNotification":
            _status(db, charger_id, Status.model_validate(payload))
            return {}
        if action == "StartTransaction":
            return _start(db, charger_id, Start.model_validate(payload), driver_tags)
        if action == "MeterValues":
            meter = MeterValues.model_validate(payload)
            session = _device_transaction(db, charger_id, meter.transactionId)
            _store_readings(db, session, meter.meterValue)
            return {}
        if action == "StopTransaction":
            stop = Stop.model_validate(payload)
            session = _device_transaction(db, charger_id, stop.transactionId)
            return _stop(db, session, stop)
        raise OcppError("NotImplemented", "Action is outside the supported charger subset.")
    except ValidationError as exc:
        raise OcppError("FormationViolation", "Invalid message payload.") from exc
    except HTTPException as exc:
        raise OcppError("PropertyConstraintViolation", str(exc.detail)) from exc
