"""
Pytest Fixtures for Module 3 Testing.
Uses an isolated in-memory SQLite database to guarantee that the live
PostgreSQL 18 database (ev_charging_network) and its 54 records remain 100% untouched.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.main import app

# 1. In-memory SQLite Test Database Engine
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all 14 tables in the isolated in-memory test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a fresh isolated database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Wipe rows in test DB between tests
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency pointing to the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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
