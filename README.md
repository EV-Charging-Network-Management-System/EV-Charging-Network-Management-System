# EV Charging Network Management System

Find compatible chargers, reserve a bay, track charging, and manage billing and maintenance in one application.

[![CI](https://github.com/EV-Charging-Network-Management-System/EV-Charging-Network-Management-System/actions/workflows/ci.yml/badge.svg)](https://github.com/EV-Charging-Network-Management-System/EV-Charging-Network-Management-System/actions/workflows/ci.yml)

![Customer dashboard with a registered EV and upcoming reservations](docs/images/customer-dashboard.png)

React and TypeScript provide the client. FastAPI, SQLAlchemy, psycopg and PostgreSQL handle the API and transactions. The browser client uses a same-origin proxy.

```mermaid
flowchart LR
    Driver[Driver, operator or administrator] --> UI[React client]
    UI --> API[FastAPI routes]
    API --> Services[Workflow services]
    Services --> Database[(PostgreSQL)]
```

## Run a seeded local demo

Generate a secret and place it in `.env` as `SECRET_KEY=<generated value>`.

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up --build -d
docker compose logs init
```

Open [the local app](http://127.0.0.1:8080). The init logs contain randomly generated credentials for the sample customer, operator and administrator on first initialization. Register directly in the app to try a new customer account. Compose binds the demo to loopback.

### Run without Docker

1. Create a PostgreSQL database. Set `DATABASE_URL`, `SECRET_KEY` and `SECURE_COOKIES=false` in the root `.env` for local HTTP. Use secure cookies for HTTPS.
2. From the root, install the package and migrate with `python -m pip install -e ".[dev]"` and `alembic upgrade head`.
3. For an isolated demo, run `python -m database.seed.demo --confirm-demo-database`.
4. Start the API from the root with `uvicorn backend.app.main:app --port 8000`. In another terminal, run `cd frontend`, `npm ci` and `npm run dev`.

For a database created using the original base SQL, back it up and verify that it matches the unmodified baseline before running `alembic stamp 0001_base` and `alembic upgrade head`. A previously customized database needs a migration review first. Any conflicting active bookings must be resolved before the exclusion constraint can be installed.

## Engineering decisions

- **Concurrent bookings.** PostgreSQL excludes overlapping pending or confirmed reservations for the same charger. The half-open range allows a new booking to start as the previous one ends. Tests race two independent API requests and verify the constraint directly in SQL.
- **Billing records.** The effective rate, pricing rule, fee and tax are captured when charging starts. Each invoice uses the captured terms, and each payment attempt is a separate record.
- **Authentication.** Passwords use Argon2. Access tokens expire after 15 minutes and logout revokes the token in PostgreSQL. The browser stores its token in an HttpOnly cookie and signs in again when it expires.

For a public demo, use the [free hosting setup](docs/HOSTED_DEMO.md). The app also supports [workflow safeguards and background jobs](docs/WORKFLOW_OPERATIONS.md).

See [design decisions](docs/DESIGN_DECISIONS.md), [API reference](docs/API_REFERENCE.md), and [schema](docs/DATABASE_SCHEMA.md).

```text
backend/app/         API routes, services, schemas and models
backend/tests/       PostgreSQL integration and workflow tests
database/migrations/ Alembic migration history
database/schema/     Initial DDL and historical proposals
database/seed/       Sample records and demo user setup
frontend/src/        Dashboards, workflow screens and API client
docs/                Database design and usage documentation
.github/workflows/   CI configuration
```

## Verification

Set `TEST_DATABASE_URL` to a dedicated empty PostgreSQL database whose name starts with `ev_test_`. The suite resets that database's app tables.

```sh
python -m pip install -e ".[dev]"
ruff check .
mypy
python -m pytest --cov=backend.app
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

Local k6 run on November 24, 2026 against the hosted image and PostgreSQL 18 produced one successful booking and 19 conflicts from 20 concurrent requests for the same slot. No slot was double-booked. The all-request p95 was 1.53 seconds, including setup login. See [benchmark setup](benchmarks/README.md).

Use Conventional Commit subjects for new changes, such as `fix: reject overlapping reservations`.

## Limitations and roadmap

The manual charging workflow and simulated payments remain available. The [charger simulator](docs/CHARGER_SIMULATOR.md) covers a subset of OCPP 1.6J. Live charger and session views use PostgreSQL notifications, so use a direct PostgreSQL connection.

- Integrate Stripe test mode, connect the advisory site power allocation to physical charger power limits and expand automated ownership checks across all endpoint types.
- Broaden the accessibility audit, expand query caching on the remaining screens, and split the remaining large billing workflows.
