# Workflow operations

- Send an `Idempotency-Key` header for a start, complete, interrupt or invoice payment request. Reuse the key only when retrying the same input. The caller and operation scope the key. A change to the request with the same key returns HTTP 409. The operation and saved response commit together.
- Administrators can page through `GET /api/v1/admin/audit-events` with `limit`, `before` and `action`. The audit records account status changes, tariff writes and refunds in the same transaction as the change.
- Common collection endpoints accept `skip` and `limit` with their existing filters. Omitting those parameters preserves the existing list behavior. Audit events and meter readings retain cursor pagination.
- Login limits repeated attempts by normalized account. The Compose proxy also limits requests to login and registration by client IP.
- Add `--profile automation` to the local Compose startup command to run the worker. It expires reservations after their grace period, marks configured chargers with stale heartbeats out of service, and generates missing invoices for recently closed sessions. The worker uses a PostgreSQL advisory lock to avoid concurrent cycles.
- The analytics endpoint uses the caller's station scope. Uptime is based on charger status history and utilization is share of elapsed calendar time. Energy is grouped by session completion hour in UTC. Estimated demand is the average number of session starts for each UTC hour over the selected period.
- CI scans newly introduced commits. The separate **Secret history audit** still reports the earlier documentation findings and can be run by hand. Rotate any old signing key that was used in a deployment.
