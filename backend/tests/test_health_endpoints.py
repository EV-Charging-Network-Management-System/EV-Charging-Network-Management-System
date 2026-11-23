"""
Module 2 Automated Tests: Health Check & Database Inspection APIs.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import engine

client = TestClient(app)


def test_api_health_endpoint():
    """Verify GET /api/v1/health returns HTTP 200 with healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "EV Charging Network Management System"
    assert "version" in data
    assert "timestamp" in data


def test_db_health_endpoint():
    """
    Verify GET /api/v1/db-health returns HTTP 200 with database name,
    PostgreSQL version, and confirmed table count of 14.
    """
    response = client.get("/api/v1/db-health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_name"] == engine.url.database
    assert "PostgreSQL 18" in data["version"]
    assert data["table_count"] >= 14
    assert "psycopg 3" in data["driver"]


def test_root_endpoint():
    """Verify GET / returns links to documentation and health endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["health_check"] == "/api/v1/health"
    assert data["db_health_check"] == "/api/v1/db-health"
    assert data["docs_url"] == "/api/v1/docs"

