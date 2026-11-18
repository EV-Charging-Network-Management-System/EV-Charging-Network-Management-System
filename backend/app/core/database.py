"""
SQLAlchemy 2.x Database Engine & Session Management for PostgreSQL 18.
Uses the modern psycopg 3 driver (postgresql+psycopg://).

SAFETY PROTOCOLS:
- NEVER run Base.metadata.create_all() or Base.metadata.drop_all().
- Connection pooling configured with pool_pre_ping to drop stale connections.
- Context-managed get_db generator ensuring clean closure.
"""

from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings


# 1. Modern SQLAlchemy 2.0 Declarative Base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# 2. Production-grade Connection Pool Engine
engine = create_engine(
    settings.sync_database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=False
)

# 3. Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


# 4. FastAPI Dependency for Database Sessions
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request,
    guaranteeing rollback on error and proper session cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# 5. Non-Destructive Health Check & Connection Verifier
def verify_db_connection() -> Dict[str, Any]:
    """
    Executes a read-only metadata verification query.
    Returns database name, version, and active table count.
    Never alters existing data.
    """
    try:
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT current_database();")).scalar()
            pg_version = conn.execute(text("SELECT version();")).scalar()
            table_count = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)).scalar()

            return {
                "status": "healthy",
                "database_name": db_name,
                "version": pg_version,
                "table_count": table_count,
                "driver": "psycopg 3 (SQLAlchemy 2.x)"
            }
    except SQLAlchemyError as exc:
        return {
            "status": "unhealthy",
            "error": str(exc),
            "driver": "psycopg 3 (SQLAlchemy 2.x)"
        }

