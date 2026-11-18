"""
Health and Database Inspection Endpoints.
READ-ONLY non-destructive verification.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.common import HealthResponse, DatabaseHealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic API Health Check",
    tags=["Health"]
)
def get_api_health() -> HealthResponse:
    """Returns the operational status of the FastAPI backend application."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get(
    "/db-health",
    response_model=DatabaseHealthResponse,
    summary="PostgreSQL 18 Read-Only Health Check",
    tags=["Health"]
)
def get_database_health(db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    """
    Executes a read-only SELECT query against PostgreSQL 18.
    Confirms:
    1. Current database name
    2. PostgreSQL version string
    3. Total count of base tables in the public schema
    """
    try:
        db_name = db.execute(text("SELECT current_database();")).scalar()
        pg_version = db.execute(text("SELECT version();")).scalar()
        table_count = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)).scalar()

        if not db_name or table_count is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database query returned incomplete metadata."
            )

        return DatabaseHealthResponse(
            status="healthy",
            database_name=str(db_name),
            version=str(pg_version),
            table_count=int(table_count),
            driver="psycopg 3 (SQLAlchemy 2.x)"
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity failed: {str(exc)}"
        )

