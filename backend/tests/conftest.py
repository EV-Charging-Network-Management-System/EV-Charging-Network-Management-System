"""Run the API suite against a dedicated, disposable PostgreSQL database."""

import os
import secrets
from pathlib import Path
from typing import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

url = os.environ.get("TEST_DATABASE_URL", "")
if not url:
    raise pytest.UsageError("Set TEST_DATABASE_URL to a dedicated PostgreSQL database named ev_test_*.")
parsed = make_url(url)
if parsed.drivername != "postgresql+psycopg" or not (parsed.database or "").startswith("ev_test_"):
    raise pytest.UsageError("TEST_DATABASE_URL must use psycopg and a disposable ev_test_* database.")
os.environ["DATABASE_URL"] = url
os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)

from backend.app.core.database import Base, SessionLocal, engine, get_db  # noqa: E402
from backend.app.core.security import get_password_hash  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models.user import User  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    root = Path(__file__).resolve().parents[2]
    command.upgrade(Config(str(root / "alembic.ini")), "head")
    yield
    engine.dispose()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
        session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY"))
        session.commit()
        yield session


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def test_customer(db_session: Session) -> User:
    """Fixture providing a verified active customer."""
    customer = User(
        full_name="Rishi Customer",
        email="rishi.customer@test.com",
        phone="9876543210",
        password_hash=get_password_hash("ValidCustomer123!"),
        role="CUSTOMER",
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Fixture providing a verified active administrator."""
    admin = User(
        full_name="Rishi Admin",
        email="rishi.admin@test.com",
        phone="9876543211",
        password_hash=get_password_hash("ValidAdmin123!"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_inactive_user(db_session: Session) -> User:
    """Fixture providing a deactivated customer."""
    inactive = User(
        full_name="Inactive User",
        email="inactive.user@test.com",
        phone="9876543212",
        password_hash=get_password_hash("InactiveUser123!"),
        role="CUSTOMER",
        is_active=False
    )
    db_session.add(inactive)
    db_session.commit()
    db_session.refresh(inactive)
    return inactive


@pytest.fixture
def test_operator(db_session: Session) -> User:
    """Fixture providing an active station operator."""
    operator = User(
        full_name="Vikram Operator",
        email="vikram.operator@test.com",
        phone="9876543215",
        password_hash=get_password_hash("ValidOperator123!"),
        role="OPERATOR",
        is_active=True
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    return operator


@pytest.fixture
def other_operator(db_session: Session) -> User:
    """Fixture providing a second operator for ownership isolation tests."""
    operator = User(
        full_name="Sneha Operator",
        email="sneha.operator@test.com",
        phone="9876543216",
        password_hash=get_password_hash("ValidOperator123!"),
        role="OPERATOR",
        is_active=True
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    return operator
