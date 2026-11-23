"""Authenticate configured chargers and dispatch bounded OCPP 1.6J messages."""

import base64
import binascii
import hmac
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.station import Charger
from backend.app.services.ocpp_service import OcppError, dispatch

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


def _authorized(websocket: WebSocket, charger_id: int) -> bool:
    device = settings.OCPP_DEVICES.get(charger_id)
    prefix, _, encoded = websocket.headers.get("authorization", "").partition(" ")
    if device is None or prefix.lower() != "basic" or len(encoded) > 1024:
        return False
    try:
        username, sep, password = base64.b64decode(encoded, validate=True).partition(b":")
    except (ValueError, binascii.Error):
        return False
    return bool(sep) and username == str(charger_id).encode() and hmac.compare_digest(
        password, device.password.get_secret_value().encode()
    )


def _charger_exists(charger_id: int) -> bool:
    with SessionLocal() as db:
        return db.get(Charger, charger_id) is not None


def _call(charger_id: int, action: str, payload: dict) -> dict:
    with SessionLocal() as db:
        return dispatch(db, charger_id, settings.OCPP_DEVICES[charger_id].driver_tags, action, payload)


@router.websocket("/ocpp/{charger_id}")
async def charger_connection(websocket: WebSocket, charger_id: int):
    if (
        "ocpp1.6" not in websocket.scope.get("subprotocols", [])
        or not _authorized(websocket, charger_id)
        or not await run_in_threadpool(_charger_exists, charger_id)
    ):
        await websocket.close(code=1008)
        return
    await websocket.accept(subprotocol="ocpp1.6")
    booted = False
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw) > 65536:
                await websocket.close(code=1009)
                return
            try:
                message = json.loads(raw)
            except (ValueError, RecursionError):
                await websocket.close(code=1007)
                return
            if (
                not isinstance(message, list) or len(message) != 4 or message[0] != 2
                or not isinstance(message[1], str) or not 1 <= len(message[1]) <= 36
                or not isinstance(message[2], str) or not isinstance(message[3], dict)
            ):
                await websocket.close(code=1007)
                return
            _, message_id, action, payload = message
            try:
                if not booted and action != "BootNotification":
                    raise OcppError("SecurityError", "BootNotification is required first.")
                result = await run_in_threadpool(_call, charger_id, action, payload)
                booted = booted or action == "BootNotification"
                await websocket.send_json([3, message_id, result])
            except OcppError as exc:
                await websocket.send_json([4, message_id, exc.code, exc.description, {}])
            except SQLAlchemyError:
                logger.exception("Charger operation failed for charger %d", charger_id)
                await websocket.send_json([4, message_id, "InternalError", "Database operation failed.", {}])
    except WebSocketDisconnect:
        return
