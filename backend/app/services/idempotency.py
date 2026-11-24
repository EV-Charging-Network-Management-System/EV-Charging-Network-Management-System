"""Replay successful requests without repeating their side effects."""

import hashlib
import json
from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.models.workflow import IdempotentOperation

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
IdempotencyKey = Annotated[str | None, Header(min_length=1, max_length=128, pattern=r"^[!-~]+$")]


def run_idempotent(
    db: Session,
    user_id: int,
    operation: str,
    key: str | None,
    payload: BaseModel,
    mutate: Callable[[], ResponseModel],
    authorize_replay: Callable[[dict], object],
) -> ResponseModel | dict:
    if key is None:
        return mutate()

    key_hash = hashlib.sha256(key.encode()).hexdigest()
    data = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    request_hash = hashlib.sha256(data.encode()).hexdigest()

    # Competing inserts wait for the first transaction to commit or roll back.
    created = db.scalar(
        insert(IdempotentOperation)
        .values(user_id=user_id, operation=operation, key_hash=key_hash, request_hash=request_hash)
        .on_conflict_do_nothing()
        .returning(IdempotentOperation)
    )
    if created is None:
        existing = db.get(IdempotentOperation, (user_id, operation, key_hash))
        if existing is None or existing.response is None:
            raise HTTPException(503, "The original operation is temporarily unavailable.")
        if existing.request_hash != request_hash:
            raise HTTPException(409, "This idempotency key was already used with different input.")
        authorize_replay(existing.response)
        return existing.response

    # The mutation must flush only. The response and all effects commit together.
    response = mutate()
    created.response = response.model_dump(mode="json")
    db.commit()
    return response
