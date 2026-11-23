"""
Main FastAPI Application Entrypoint.
EV Charging Network Management System.
"""

import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.api.ocpp import router as ocpp_router
from backend.app.api.session_stream import router as stream_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for EV Charging Network Management System",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ocpp_router)
app.include_router(stream_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_status():
    """Root endpoint providing links to documentation and health check."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "db_health_check": f"{settings.API_V1_STR}/db-health"
    }



@app.middleware("http")
async def log_request(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    start = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
    finally:
        route = request.scope.get("route")
        logging.getLogger("uvicorn.error").info(json.dumps({
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "route": getattr(route, "path", None),
            "status": status_code,
            "duration_ms": round((perf_counter() - start) * 1000, 2),
        }))


@app.get("/health", tags=["Health"])
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    """Report whether the API can reach the migrated schema."""
    try:
        revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable or migrations pending.") from exc
    if revision is None:
        raise HTTPException(status_code=503, detail="Database migrations pending.")
    return {"status": "ready"}

