"""
FastAPI V1 API Router.
Aggregates authentication, user management, and health endpoints.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    audit,
    analytics,
    power,
    users,
    health,
    vehicles,
    connectors,
    stations,
    chargers,
    tariffs,
    pricing_rules,
    pricing,
    reservations,
    sessions,
    invoices,
    payments,
    maintenance
)

api_router = APIRouter()

# Health endpoints (/api/v1/health, /api/v1/db-health)
api_router.include_router(health.router, tags=["Health"])

# Authentication endpoints (/api/v1/auth/register, /login, /me, /logout)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management endpoints (/api/v1/users/me, /api/v1/users, /{user_id}/status)
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Vehicle management endpoints (/api/v1/vehicles, /{vehicle_id}, /{vehicle_id}/connectors)
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])

# Connector standards endpoints (/api/v1/connectors)
api_router.include_router(connectors.router, prefix="/connectors", tags=["Connectors"])

# Station management & Geolocation endpoints (/api/v1/stations, /nearby, /{station_id})
api_router.include_router(stations.router, prefix="/stations", tags=["Stations"])

# Charger management endpoints (/api/v1/chargers, /{charger_id})
api_router.include_router(chargers.router, prefix="/chargers", tags=["Chargers"])

# Tariff management endpoints (/api/v1/tariffs, /{tariff_id})
api_router.include_router(tariffs.router, prefix="/tariffs", tags=["Tariffs"])

# Dynamic pricing rules endpoints (/api/v1/pricing-rules, /{rule_id})
api_router.include_router(pricing_rules.router, prefix="/pricing-rules", tags=["Pricing Rules"])

# Dynamic pricing calculation & quote endpoints (/api/v1/pricing/quote, /demand)
api_router.include_router(pricing.router, prefix="/pricing", tags=["Dynamic Pricing"])

# Reservation management & Slot conflict engine endpoints (/api/v1/reservations, /availability, /{id}/cancel)
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])

# Charging Session management & Energy metering endpoints (/api/v1/sessions/start, /active, /history, /{id}/complete)
api_router.include_router(sessions.router, prefix="/sessions", tags=["Charging Sessions"])

# Invoicing & Billing endpoints (/api/v1/invoices, /generate/{session_id}, /{id}/payments, /reports/revenue)
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices & Billing"])

# Payment management endpoints (/api/v1/payments, /{payment_id}, /{payment_id}/refund)
api_router.include_router(payments.router, prefix="/payments", tags=["Payments & Reconciliation"])

# Maintenance work order & diagnostics endpoints (/api/v1/maintenance, /reports/summary, /{id}/assign, /{id}/status)
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance & Audit Trail"])

api_router.include_router(audit.router, tags=["Audit"])

api_router.include_router(analytics.router, tags=["Analytics"])

api_router.include_router(power.router, tags=["Smart charging"])
