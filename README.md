# EV Charging Network Management System

An enterprise-ready **Electric Vehicle (EV) Charging Network Management System** built with **PostgreSQL 18**, **FastAPI (Python)**, **React (TypeScript)**, and **Leaflet (OpenStreetMap)**.

---

## 1. Project Overview & Architecture

The EV Charging Network Management System provides end-to-end station management, slot reservations, real-time charging telemetry simulation, dynamic time-of-use and demand tariffs, invoicing with payment reconciliation, and equipment maintenance tracking.

### Technology Stack
- **Database:** PostgreSQL 18 (14 normalized tables, 54 pre-populated dummy records)
- **Backend:** FastAPI (Python 3.11+) with **SQLAlchemy 2.x** and **psycopg 3** driver
- **Security & Authentication:** Argon2 password hashing via `pwdlib`, cryptographically signed JWT access tokens (`pyjwt`), Role-Based Access Control (RBAC)
- **Data Validation:** Pydantic v2 & Pydantic Settings
- **Frontend:** React 18 + TypeScript + Vite with custom EV dark theme
- **Mapping & Geolocation:** Leaflet + OpenStreetMap + React-Leaflet
- **Testing & Verification:** Pytest + Read-Only Database Inspection Engine

---

## 2. Database Status & Safety Principles

> [!IMPORTANT]
> **EXISTING DATABASE GROUND-TRUTH RULES:**
> - Database Name: `ev_charging_network`
> - Host: `localhost` | Port: `5432` | User: `postgres`
> - Status: **14 core tables** and **54 dummy records** are pre-existing and verified.
> - **SAFETY RULE:** **NEVER DROP, DELETE, TRUNCATE OR RECREATE EXISTING DATABASE TABLES OR SAMPLE DATA.**
> - `Base.metadata.create_all()` is **never** invoked against PostgreSQL. Schema creation/migrations are forbidden against the live database.
> - All inspection and test scripts operate under explicit read-only transactions (`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`) or use isolated in-memory test databases.

### The 14 Verified Base Tables & SQLAlchemy ORM Models (54 Records)
| # | Model Class | Table Name | Purpose | Verified Row Count |
| :-: | :--- | :--- | :--- | :-: |
| 1 | `User` | `users` | Customers, station operators, and administrators | **5** |
| 2 | `ConnectorType` | `connector_types` | Connector standards (CCS2, Type 2, CHAdeMO, GB/T) | **4** |
| 3 | `Vehicle` | `vehicles` | User-registered electric vehicles | **3** |
| 4 | `VehicleConnectorType` | `vehicle_connector_types` | Many-to-many vehicle & connector compatibility | **6** |
| 5 | `Station` | `stations` | Station locations, opening hours, coordinates | **3** |
| 6 | `Charger` | `chargers` | Individually reservable charging bays/ports | **5** |
| 7 | `Tariff` | `tariffs` | Station base pricing per kWh & session fees | **4** |
| 8 | `PricingRule` | `pricing_rules` | Peak hour, off-peak, and demand multipliers | **3** |
| 9 | `Reservation` | `reservations` | Slot bookings with time ranges and status | **7** |
| 10 | `ChargingSession` | `charging_sessions` | Active and completed charging sessions & meters | **3** |
| 11 | `Invoice` | `invoices` | Billing snapshots, energy charges, taxes | **2** |
| 12 | `Payment` | `payments` | Multi-attempt transactions (UPI, Card, Cash, Demo) | **3** |
| 13 | `MaintenanceRecord` | `maintenance_records` | Fault reports, work orders, repair costs | **2** |
| 14 | `ChargerStatusHistory` | `charger_status_history` | Audit log of charger operational transitions | **4** |
| **Total** | **14 Models** | **14 Tables** | **Complete Network State** | **54 Records** |

---

## 3. Project Directory Tree

All files are strictly contained inside the workspace root (`mh_dbms`):

```
mh_dbms/
├── .env.example                                  # Sanitized environment template
├── .env                                          # Secure local environment file (git-ignored)
├── .gitignore                                    # Git exclusion rules
├── README.md                                     # Master project documentation
├── backend/                                      # FastAPI Python backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                          # Auth & RBAC dependencies (get_current_user, require_admin)
│   │   │   └── v1/
│   │   │       ├── api.py                       # V1 API router aggregator
│   │   │       └── endpoints/
│   │   │           ├── auth.py                  # Register, Login, Me, Logout endpoints
│   │   │           ├── health.py                # Health & DB inspection APIs
│   │   │           ├── pricing.py               # Tariffs, pricing rules & dynamic quotes
│   │   │           ├── reservations.py          # Slot booking & availability search
│   │   │           ├── sessions.py              # Charging session lifecycle & metering APIs
│   │   │           ├── stations.py              # Station & charger APIs with GPS radius search
│   │   │           ├── users.py                 # Profile & Admin user management APIs
│   │   │           └── vehicles.py              # EV specs & connector management APIs
│   │   ├── core/
│   │   │   ├── config.py                        # Pydantic v2 application settings
│   │   │   ├── database.py                      # SQLAlchemy 2.x + psycopg 3 engine & pooling
│   │   │   └── security.py                      # Argon2 password hashing (pwdlib) & JWT tokens
│   │   ├── models/                              # 14 SQLAlchemy Declarative Models
│   │   │   ├── __init__.py                      # Model registry
│   │   │   ├── billing.py                       # Invoice & Payment models
│   │   │   ├── maintenance.py                   # MaintenanceRecord & ChargerStatusHistory
│   │   │   ├── reservation.py                   # Reservation model
│   │   │   ├── session.py                       # ChargingSession model
│   │   │   ├── station.py                       # Station & Charger models
│   │   │   ├── tariff.py                        # Tariff & PricingRule models
│   │   │   ├── user.py                          # User model
│   │   │   └── vehicle.py                       # Vehicle, ConnectorType models
│   │   └── schemas/                             # Pydantic v2 request/response schemas
│   │       ├── __init__.py
│   │       ├── auth.py                          # Login, Register, Token schemas
│   │       ├── billing.py
│   │       ├── common.py                        # Common API & Health check schemas
│   │       ├── maintenance.py
│   │       ├── reservation.py
│   │       ├── session.py
│   │       ├── station.py
│   │       ├── tariff.py
│   │       ├── user.py                          # User profile & status schemas
│   │       └── vehicle.py
│   ├── tests/                                   # Backend automated test suite
│   │   ├── conftest.py                          # Isolated SQLite in-memory test fixtures
│   │   ├── test_auth_module3.py                 # Module 3 authentication & RBAC tests (17 tests)
│   │   ├── test_database_core.py                # Engine, connection & model query tests (5 tests)
│   │   └── test_health_endpoints.py             # Health API endpoint tests (3 tests)
│   ├── pyproject.toml                           # Python project configuration
│   └── requirements.txt                         # Dependency specification
├── frontend/                                     # React 18 + TypeScript + Vite
│   ├── public/                                  # Static public assets
│   ├── src/
│   │   ├── assets/                              # App assets
│   │   ├── components/                          # Navbar, ProtectedRoute, Map, Filters, Badges, Session cards
│   │   │   ├── ChargerStatusBadge.tsx           # Operational status indicator badge
│   │   │   ├── ConnectorSelector.tsx            # Multi-select port compatibility selector
│   │   │   ├── CompleteSessionForm.tsx          # Session completion & meter input form
│   │   │   ├── EnergyConsumptionCard.tsx        # Real-time energy, meter & duration visualizer
│   │   │   ├── Navbar.tsx                       # Navigation bar with role badges & links
│   │   │   ├── ProtectedRoute.tsx               # Auth guard component
│   │   │   ├── StationFilters.tsx               # City, connector, power & status filter toolbar
│   │   │   └── StationMap.tsx                   # OpenStreetMap Leaflet map with live markers
│   │   ├── context/
│   │   │   └── AuthContext.tsx                  # Global authentication state
│   │   ├── pages/                               # Dashboards, Vehicles, Stations, Sessions, Pricing
│   │   │   ├── ActiveSessionsPage.tsx           # Live charging monitoring dashboard
│   │   │   ├── AddChargerPage.tsx               # Charger bay commissioning form
│   │   │   ├── AddPricingRulePage.tsx           # Dynamic pricing rule creation form
│   │   │   ├── AddStationPage.tsx               # Station creation form with GPS coordinates
│   │   │   ├── AddTariffPage.tsx                # Station & connector tariff creation form
│   │   │   ├── AddVehiclePage.tsx               # EV registration form & connector selector
│   │   │   ├── AdminDashboard.tsx               # Admin user management console
│   │   │   ├── ChargersPage.tsx                 # Network-wide charger bay inventory
│   │   │   ├── ChargingSessionPage.tsx          # Session dashboard hub
│   │   │   ├── CustomerDashboard.tsx            # Customer EV dashboard & quick actions
│   │   │   ├── EditStationPage.tsx              # Station specifications editor
│   │   │   ├── EditVehiclePage.tsx              # Vehicle specs & connector port editor
│   │   │   ├── LoginPage.tsx                    # Modern EV charging login with demo quick-fills
│   │   │   ├── OperatorDashboard.tsx            # Station operator control panel
│   │   │   ├── PricingCalculatorPage.tsx        # Interactive dynamic pricing estimator page
│   │   │   ├── PricingRulesPage.tsx             # Peak/off-peak & demand rules console
│   │   │   ├── ProfilePage.tsx                  # User profile self-service
│   │   │   ├── RegisterPage.tsx                 # Customer registration
│   │   │   ├── SessionDetailsPage.tsx           # Detailed session audit & breakdown view
│   │   │   ├── SessionHistoryPage.tsx           # Completed/interrupted session history table
│   │   │   ├── StartSessionPage.tsx             # Interactive session start wizard (walk-in/reservation)
│   │   │   ├── StationDetailsPage.tsx           # Station overview with installed charger bays
│   │   │   ├── StationsPage.tsx                 # Interactive map & station directory
│   │   │   ├── TariffManagementPage.tsx         # Station tariffs & rates manager
│   │   │   ├── VehicleDetailsPage.tsx           # Vehicle specifications & compatibility view
│   │   │   └── VehiclesPage.tsx                 # My Vehicles & Fleet management dashboard
│   │   ├── services/
│   │   │   ├── api.ts                           # Fetch client with token interceptor
│   │   │   ├── auth.ts                          # Auth API client
│   │   │   ├── pricing.ts                       # Dynamic pricing, tariffs & quotes client
│   │   │   ├── reservation.ts                   # Slot reservation & availability client
│   │   │   ├── session.ts                       # Charging session & metering API client
│   │   │   ├── station.ts                       # Station & charger API client
│   │   │   └── vehicle.ts                       # Vehicle & connector API client
│   │   ├── styles/
│   │   │   └── theme.css                        # Modern EV charging dark palette
│   │   ├── types/
│   │   │   ├── auth.ts                          # TypeScript user & auth interfaces
│   │   │   ├── reservation.ts                   # TypeScript reservation & availability interfaces
│   │   │   ├── session.ts                       # TypeScript session & meter interfaces
│   │   │   ├── station.ts                       # TypeScript station & charger interfaces
│   │   │   ├── tariff.ts                        # TypeScript tariff, rule & quote interfaces
│   │   │   └── vehicle.ts                       # TypeScript vehicle & connector interfaces
│   │   ├── App.tsx                              # App router & role dispatch
│   │   ├── router.tsx                           # Zero-dependency browser router
│   │   └── main.tsx                             # React entrypoint
│   ├── index.html                               # HTML template with Leaflet styles
│   ├── package.json                             # Node dependencies
│   ├── tsconfig.json                            # TypeScript configuration
│   └── vite.config.ts                           # Vite configuration with API proxy
├── database/                                     # Database scripts & tools
│   ├── inspector/
│   │   └── db_inspector.py                      # READ-ONLY PostgreSQL inspector
│   ├── reports/
│   │   ├── database_inspection_report.json      # Structured inspection audit data
│   │   └── database_inspection_report.md        # Formatted markdown inspection report
│   ├── schema/
│   │   ├── EV_Charging_Create_Tables.sql        # Reference schema DDL
│   │   ├── proposed_reservation_exclusion_constraint.sql # Module 7 exclusion constraint proposal
│   │   ├── proposed_session_tariff_extension.sql # Module 6 session tariff snapshot proposal
│   │   ├── revised_session_tariff_extension.sql # Module 8 revised session tariff proposal
│   │   └── proposed_invoicing_billing_extension.sql # Module 9 proposed invoicing & billing extension
│   └── seed/
│       └── EV_Charging_Insert_Dummy_Data.sql    # Reference seed DML (54 rows)
├── docs/                                         # Technical documentation
│   ├── DATABASE_SCHEMA.md                       # Comprehensive schema specifications
│   ├── ER_DIAGRAM_COMPARISON.md                 # ER model vs relational schema analysis
│   ├── MODULE_PLAN.md                           # Step-by-step modular roadmap
│   ├── MODULE_2_REPORT.md                       # Module 2 completion & verification report
│   ├── MODULE_3_REPORT.md                       # Module 3 authentication & RBAC report
│   ├── MODULE_4_REPORT.md                       # Module 4 vehicle & connector management report
│   ├── MODULE_5_REPORT.md                       # Module 5 station & charger management report
│   ├── MODULE_6_REPORT.md                       # Module 6 tariffs & dynamic pricing report
│   ├── MODULE_7_REPORT.md                       # Module 7 reservations & slot conflict engine report
│   ├── MODULE_8_REPORT.md                       # Module 8 charging session & energy metering report
│   └── MODULE_9_REPORT.md                       # Module 9 invoicing & payment reconciliation report
├── results/                                      # Test evidence outputs
│   └── test_results/
│       ├── module2_test_results.log             # Module 2 test log
│       ├── module3_test_results.log             # Module 3 test log
│       ├── module4_test_results.log             # Module 4 test log
│       ├── module5_test_results.log             # Module 5 test log
│       ├── module6_test_results.log             # Module 6 test log
│       ├── module7_test_results.log             # Module 7 test log
│       ├── module8_test_results.log             # Module 8 test log
│       └── module9_test_results.log             # Module 9 test log
└── tests/                                        # Verification test suite
    ├── run_module2_tests.py                     # Module 2 automated test runner
    ├── run_module3_tests.py                     # Module 3 automated test runner
    ├── run_module4_tests.py                     # Module 4 automated test runner
    ├── run_module5_tests.py                     # Module 5 automated test runner
    ├── run_module6_tests.py                     # Module 6 automated test runner
    ├── run_module7_tests.py                     # Module 7 automated test runner
    ├── run_module8_tests.py                     # Module 8 automated test runner
    ├── run_module9_tests.py                     # Module 9 automated test runner
    ├── test_database_verification.py            # Read-only database schema verifier
    └── test_results/
        ├── database_verification.log            # Module 1 test log
        ├── module2_test_results.log             # Module 2 test log
        ├── module3_test_results.log             # Module 3 test log
        ├── module4_test_results.log             # Module 4 test log
        ├── module5_test_results.log             # Module 5 test log
        ├── module6_test_results.log             # Module 6 test log
        └── module7_test_results.log             # Module 7 test log
```

---

## 4. Running the Application Locally

Copy `.env.example` to `.env`, configure PostgreSQL and set a unique, random
`SECRET_KEY`. Install backend dependencies with `python -m pip install -r
backend/requirements.txt` from the repository root.

The sample seed data contains placeholder passwords. Demo logins are disabled
by default; to use the login page's demo buttons with a local test database, set
`ALLOW_DEMO_PASSWORDS=true` in `.env` and restart the backend. Never enable this
option for a public or production deployment. Real users should use accounts
with properly hashed passwords.

### 1. Run the FastAPI Backend Server
```powershell
# From the mh_dbms workspace root:
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger Documentation: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)

### 2. Run the React Frontend Development Server
```powershell
# In a separate terminal inside frontend/:
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 5. Verification & Automated Testing

### Running Module 6 Test Suite
```powershell
python tests/run_module6_tests.py
```
This runs 19 automated tests covering tariff CRUD, connector precedence, overlap collision prevention, peak-hour surges, off-peak night discounts, high-demand multipliers, priority resolution, deterministic collision rejection (HTTP 409), and pure mathematical price quote breakdowns.

### Running Module 7 Test Suite
```powershell
python tests/run_module7_tests.py
```
This runs 17 automated tests covering charger availability search, EV connector compatibility, operating hours checks, transactional booking with row-level locking (`with_for_update()`), double-booking conflict rejection (HTTP 409), adjacent booking acceptance, slot release on cancellation, and RBAC isolation.

### Running Module 8 Test Suite
```powershell
python tests/run_module8_tests.py
```
This runs 17 automated tests covering reserved and walk-in session creation, connector compatibility, meter validation (`meter_end >= meter_start`), single active session bay enforcement, graceful and abrupt interruption, pricing engine tariff snapshotting, concurrent session start prevention, and customer/operator data isolation.

### Running Module 9 Test Suite
```powershell
python tests/run_module9_tests.py
```
This runs 22 automated tests covering invoice generation from completed sessions, meter calculations, financial rounding (`ROUND_HALF_UP`), locked tariff preservation, duplicate invoice prevention, simulated DEMO payment processing, failed attempt preservation, payment retries, overpayment prevention, customer invoice isolation, executive revenue reports, and authorized refund reconciliation.

### Running Module 10 Test Suite
```powershell
python tests/run_module10_tests.py
```
This runs 22 automated tests covering maintenance work order submission, status defaults, non-existent charger rejection, priority validation, technician role validation, customer isolation, operator and admin RBAC scoping, multi-criteria filtering, technician assignment, bay locking and conflict detection (409 Conflict on active sessions or upcoming reservations), atomic status changes, status history audit logging, MTTR resolution time and cost tracking, operator safety clearance protocol, and SQL aggregation analytics.

### Running Final End-to-End Integration Suite
```powershell
python tests/run_final_e2e_tests.py
```
This runs 8 comprehensive end-to-end integration workflows covering:
- **Workflow A:** Customer Full Lifecycle (15-step chain: register, login, EV registration, connector pairing, station discovery, compatible charger check, dynamic price quote, slot reservation, session start, meter simulation, session completion, invoice generation, DEMO checkout, receipt generation, history verification).
- **Workflow B:** Payment failure preservation (`UNPAID`), payment retry, transaction success (`PAID`), multi-attempt audit logging.
- **Workflow C:** Maintenance fault ticketing, technician assignment, bay locking to `MAINTENANCE`, conflict blocking, resolution with repair cost, operator safety clearance protocol, return to `ONLINE`.
- **Workflow D:** Reservation conflict prevention (half-open range `[start, end)` collision rejection HTTP 409, adjacent slot acceptance).
- **Security & RBAC:** Password hash exclusion, cross-tenant customer data isolation, operator scoping, admin role boundary.

### Running Full Automated Regression Test Suite (All 10 Modules)
```powershell
python -m pytest backend/tests/ -q
```
**Total:** **164 passed, 0 failed in 250.45s (100% success rate)** across all 11 test suites.

### Running the READ-ONLY Database Inspector
```powershell
python database/inspector/db_inspector.py
```
Verifies 14/14 tables and 54/54 original seed records remain 100% intact.

---

## 6. Implementation Roadmap & Certified Project Status

- [x] **Module 1 (COMPLETED):** Project Structure Setup, READ-ONLY Database Inspection & ER Analysis.
- [x] **Module 2 (COMPLETED):** Backend Core, Database Connection Pool (SQLAlchemy 2.x + psycopg 3), 14 ORM Models, Pydantic v2 Schemas, Health APIs.
- [x] **Module 3 (COMPLETED):** Argon2 Password Security, JWT Authentication, Customer Self-Service Profile, Admin User Management, React Auth & Role-Based Dashboards.
- [x] **Module 4 (COMPLETED):** Vehicle Registration & Specification APIs, Connector Standard Compatibility (CCS-2, Type 2, etc.), Atomic Profile Replacement Transactions, Customer Isolation & Ownership Validation, React EV Management Dashboard.
- [x] **Module 5 (COMPLETED):** Station & Charger Management APIs, Haversine Spherical Geolocation & Radius Search, Atomic Status Transition Audit Logging (`charger_status_history`), Leaflet + OpenStreetMap Interactive Map & Filter Toolbar.
- [x] **Module 6 (COMPLETED):** Tariffs & Dynamic Pricing Calculation Engine, Time-of-Use & Demand Rules, Pure Read-Only Quote Calculator, Conflict & Collision Detection, Interactive React Pricing Estimator & Tariffs Dashboard.
- [x] **Module 7 (COMPLETED):** Reservations & Slot Conflict Engine, Half-Open Time Range Semantics, PostgreSQL GiST Exclusion Constraint Design, Vehicle Compatibility Verification, Dynamic Pricing Integration, Interactive React Booking Wizard & History Dashboard.
- [x] **Module 8 (COMPLETED):** Charging Session Management & Energy Metering, Concurrency Row-Locking Audit & Fix, Reservation-Backed & Walk-In Sessions, Dynamic Tariff Snapshotting, State Transitions & Check Constraints, React Telemetry & Session Management Console.
- [x] **Module 9 (COMPLETED):** Invoicing and Payment Reconciliation, Immutable Financial Snapshots, Gateway Provider Abstraction & DEMO Simulation, Row-Level Lock Payment Serialization, Overpayment Prevention, Multi-Attempt Audit History, Authorized Refunds, React Billing & Checkout Suite.
- [x] **Module 10 (COMPLETED):** Maintenance Work Orders & Charger Status Audit Trail, Technician Assignments, Row-Locking Bay Conflict Interlocks, Operational Status State Machine, Chronological Transition Audit Trail, MTTR & Downtime Analytics, React Maintenance Management Suite.
- [x] **Final Phase (COMPLETED):** Full System Integration, End-to-End Automated Workflows (A–D), Comprehensive Security Audit, Frontend Production Build, Master Project Documentation & Certified Delivery.

---

## 7. Master System Documentation Library

Comprehensive technical documentation, specifications, and manuals are available in [`docs/`](docs/):

1. **[Final System Validation Report](docs/FINAL_SYSTEM_VALIDATION_REPORT.md):** Formal audit report with test results, database integrity verification, and security analysis.
2. **[Master Project Documentation](docs/FINAL_PROJECT_DOCUMENTATION.md):** Complete architectural specifications, 1NF–BCNF relational normalization, ER diagrams, module deep-dives, and advanced DBMS concepts.
3. **[REST API Reference](docs/API_REFERENCE.md):** Full technical contract for all 15 API routers under `/api/v1` with JSON request/response schemas, status codes, and RBAC rules.
4. **[End-User Manual](docs/USER_MANUAL.md):** Step-by-step operational guide for EV Drivers (Customers), Station Operators, and System Administrators.
5. **[Production Deployment Guide](docs/DEPLOYMENT_GUIDE.md):** Production setup instructions for PostgreSQL 18, Uvicorn/Gunicorn, Nginx reverse proxy, Docker orchestration, and zero-downtime migration procedures.
6. **[Database Schema Reference](docs/DATABASE_SCHEMA.md):** Detailed catalog specifications for all 14 database tables and foreign key relationships.
7. **[ER Diagram & Model Comparison](docs/ER_DIAGRAM_COMPARISON.md):** Structural analysis comparing the conceptual ER model with the physical relational schema.
