"""
Module 2 Automated Tests: Database Connectivity, Model Mapping & Read-Only Safety.
Guarantees zero modifications to the existing 14 tables and 54 sample records.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models import (
    User, ConnectorType, Vehicle, VehicleConnectorType,
    Station, Charger, Tariff, PricingRule,
    Reservation, ChargingSession, Invoice, Payment,
    MaintenanceRecord, ChargerStatusHistory
)

EXPECTED_14_TABLES = [
    "users",
    "connector_types",
    "vehicles",
    "vehicle_connector_types",
    "stations",
    "chargers",
    "tariffs",
    "pricing_rules",
    "reservations",
    "charging_sessions",
    "invoices",
    "payments",
    "maintenance_records",
    "charger_status_history"
]

EXPECTED_ROW_COUNTS = {
    User: 5,
    ConnectorType: 4,
    Vehicle: 3,
    VehicleConnectorType: 6,
    Station: 3,
    Charger: 5,
    Tariff: 4,
    PricingRule: 3,
    Reservation: 7,
    ChargingSession: 3,
    Invoice: 2,
    Payment: 3,
    MaintenanceRecord: 2,
    ChargerStatusHistory: 4
}


def test_db_engine_connectivity():
    """Verify live connection to PostgreSQL 18 ev_charging_network via psycopg 3."""
    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT current_database();")).scalar()
        assert db_name == "ev_charging_network", f"Expected 'ev_charging_network', got '{db_name}'"


def test_db_version_is_postgresql_18():
    """Verify PostgreSQL version is 18."""
    with engine.connect() as conn:
        version_str = conn.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL 18" in version_str, f"Expected PostgreSQL 18, got '{version_str}'"


def test_14_tables_exist_in_information_schema():
    """Verify all 14 required tables exist in public schema."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)).fetchall()
        tables = [row[0] for row in result]
        assert len(tables) == 14, f"Expected 14 tables, got {len(tables)}: {tables}"
        for exp in EXPECTED_14_TABLES:
            assert exp in tables, f"Expected table '{exp}' not found in database."


def test_sqlalchemy_metadata_registers_14_tables():
    """Verify Base.metadata has mapped all 14 tables."""
    metadata_tables = list(Base.metadata.tables.keys())
    assert len(metadata_tables) == 14, f"Expected 14 metadata tables, got {len(metadata_tables)}"
    for exp in EXPECTED_14_TABLES:
        assert exp in metadata_tables, f"Table '{exp}' missing from SQLAlchemy metadata."


def test_sqlalchemy_models_query_existing_54_records():
    """
    Verify each ORM model accurately queries its table and the dummy record count
    remains strictly intact at 54 records.
    """
    db: Session = SessionLocal()
    try:
        total_records = 0
        for model, expected_count in EXPECTED_ROW_COUNTS.items():
            count = db.query(model).count()
            assert count == expected_count, (
                f"Model {model.__name__} count mismatch: expected {expected_count}, got {count}"
            )
            total_records += count

        assert total_records == 54, f"Expected 54 dummy records across models, found {total_records}"
    finally:
        db.close()

