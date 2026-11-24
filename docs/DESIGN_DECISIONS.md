# Design decisions

## PostgreSQL booking constraint

Bookings occupy half-open intervals. A pending or confirmed booking excludes another overlapping booking on the same charger. The GiST exclusion constraint applies to all writers, including SQL clients and API workers. The API also checks for conflicts so the customer gets a useful HTTP 409.

## Billing snapshots

An invoice preserves its energy, rate, fees and tax figures for reconciliation. Multiple payment attempts can refer to one invoice. A complete start-time tariff snapshot is a separate schema and workflow change. Treat the historical proposal scripts as design material.

## Synchronous SQLAlchemy

The application uses FastAPI synchronous handlers for database operations. A request-scoped SQLAlchemy session provides a transaction and row locks where needed. The service layer owns workflow changes, routes own request and response validation, and models express the stored schema.

## Browser sessions

A short-lived cookie carries the access token. State-changing cookie-authenticated requests carry a custom header and cross-origin access is limited to configured origins. API clients can continue to use bearer tokens. PostgreSQL stores revoked token IDs until expiry so revocation works across workers.
