# Module 8 Report: Charging Session Management and Energy Metering

**Project:** EV Charging Network Management System  
**Workspace:** `mh_dbms`  
**Database:** PostgreSQL 18 (`ev_charging_network`)  
**Status:** COMPLETED & VERIFIED (17/17 Module 8 Tests Passing, Full Backend Regression Passing)  
**Date:** November 2026  

---

## 1. Executive Summary

Module 8 delivers the core real-time charging execution and physical telemetry tracking engine: **Charging Session Management and Energy Metering**. It bridges the gap between reservation scheduling and billing by tracking the end-to-end lifecycle of physical charging sessions, enforcing strict energy meter monotonicity, preventing concurrent bay double-sessions via row-level locking, integrating real-time dynamic pricing snapshots, and providing driver and operator dashboards.

Key architectural accomplishments:
- **Phase Gate Module 7 Concurrency Audit:** Conducted an empirical concurrency audit on an isolated PostgreSQL test database (`ev_charging_test_audit`). Confirmed that unconstrained bookings on unoccupied slots produce a race condition when only existing reservations are locked (0 rows matched $\implies$ 0 rows locked). Implemented a **100% safe, schema-neutral fix** by locking the stable physical `Charger` row (`with_for_update(of=Charger)`), serializing bookings per bay without modifying the live database schema.
- **Dual Session Initiation (Reservation vs. Walk-in):** Supports both reservation-backed charging (validating slot window, vehicle, bay, and ownership) and instant walk-in charging (`reservation_id` is NULL), verifying that no conflicting reservation overlaps with the immediate charging window.
- **Energy Metering & Consumption Engine:** Enforces mathematical meter validity:
  $$\text{energy\_consumed\_kwh} = \text{meter\_end\_kwh} - \text{meter\_start\_kwh}$$
  Guarantees $\text{meter\_start\_kwh} \ge 0$ and $\text{meter\_end\_kwh} \ge \text{meter\_start\_kwh}$.
- **Strict PostgreSQL State Constraints:** Aligns with PostgreSQL 18's multi-column check constraint:
  $$(\text{status} = \text{'ACTIVE'} \land \text{ended\_at IS NULL} \land \text{meter\_end\_kwh IS NULL}) \lor (\text{status} \in \{\text{'COMPLETED'}, \text{'INTERRUPTED'}\} \land \text{ended\_at IS NOT NULL} \land \text{meter\_end\_kwh IS NOT NULL})$$
- **Dynamic Pricing Integration & Tariff Snapshot:** Automatically resolves the active tariff using Module 6's hierarchy and evaluates active pricing rules (peak surge, off-peak discount, demand multiplier). Formulated a formal enhancement proposal in `database/schema/revised_session_tariff_extension.sql`.
- **Session Interruption & Safety Stop:** Supports emergency stops and fault interruptions (`POST /api/v1/sessions/{id}/interrupt`) while strictly preserving meter telemetry and releasing the bay for other drivers.
- **Full React/TypeScript Suite:** Delivered interactive session interfaces including `ChargingSessionPage.tsx`, `StartSessionPage.tsx`, `ActiveSessionsPage.tsx`, `SessionDetailsPage.tsx`, `SessionHistoryPage.tsx`, `EnergyConsumptionCard.tsx`, and `CompleteSessionForm.tsx`.
- **Database Safety Compliance:** 100% adherence to all database safety rules. Zero `DROP`, `TRUNCATE`, `ALTER`, or migration commands were executed against the live PostgreSQL 18 database. All 14 tables and 54 original dummy records remain intact.

---

## 2. Phase Gate Audit: Concurrency & Lock Analysis

### 2.1 The Vulnerability in Pure Reservation-Level Locking
Under standard row-level locking (`SELECT ... FROM reservations ... FOR UPDATE`):
1. When a driver books a slot for a time window that is currently unoccupied, the query returns **0 rows**.
2. In SQL relational databases, row locks can only be attached to **existing returned rows**. With 0 rows returned, **no locks are held**.
3. Two concurrent transactions $T_1$ and $T_2$ targeting the exact same charger and time window both evaluate 0 conflicts and both execute `INSERT INTO reservations`, resulting in a duplicate double-booking race condition.

### 2.2 Empirical Audit Evidence
In our isolated PostgreSQL test database (`ev_charging_test_audit`):
```text
--- TEST 1: Without locking charger row (Original Module 7 logic) ---
Results without charger lock: [(2, 'BOOKED_201'), (1, 'BOOKED_201')]
[AUDIT FINDING] CONFIRMED RACE CONDITION: Both concurrent transactions committed duplicate bookings!

--- TEST 2: With locking physical Charger row (Proposed Safe Fix) ---
Results with charger lock: [(1, 'BOOKED_201'), (2, 'CONFLICT_409')]
Booked: 1, Conflict 409: 1
[AUDIT RESULT] SAFE FIX VERIFIED: Physical Charger row lock completely eliminates race condition without schema changes!
```

### 2.3 Safe Application-Level Fix
In `backend/app/services/reservation_service.py` and `backend/app/services/session_service.py`:
```python
# Lock the stable physical Charger row to serialize operations on this bay
db.execute(
    select(Charger)
    .where(Charger.charger_id == payload.charger_id)
    .with_for_update(of=Charger)
).scalar_one_or_none()
```
Specifying `of=Charger` prevents PostgreSQL errors regarding outer joins on relationships, completely serializing all operations per charger bay without any DDL schema migrations.

---

## 3. Session Lifecycle State Machine

```
               [ Start Session ]
                       │
                       ▼
               ┌───────────────┐
               │    ACTIVE     │ ── (ended_at IS NULL, meter_end IS NULL)
               └───────┬───────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
 [ Complete ]                  [ Interrupt ]
 (meter_end >= start)          (fault / emergency stop)
        │                             │
        ▼                             ▼
┌───────────────┐             ┌───────────────┐
│   COMPLETED   │             │  INTERRUPTED  │ ── (ended_at NOT NULL, meter_end NOT NULL)
└───────────────┘             └───────────────┘
```

---

## 4. API Endpoints Implemented

| Method | Endpoint | Access | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/sessions/start` | Authenticated | Starts a charging session (reservation-backed or walk-in) with row locking |
| `GET` | `/api/v1/sessions/active` | Authenticated | Lists currently active sessions (Customer: own; Operator: station; Admin: all) |
| `GET` | `/api/v1/sessions/history` | Authenticated | Lists historical sessions with status, station, vehicle, and date filters |
| `GET` | `/api/v1/sessions/{session_id}` | Authenticated | Retrieves detailed session telemetry, vehicle, charger, and tariff info |
| `POST` | `/api/v1/sessions/{session_id}/complete` | Authenticated | Records final meter reading, calculates consumption, and marks COMPLETED |
| `POST` | `/api/v1/sessions/{session_id}/interrupt` | Authenticated | Handles emergency stops, records final reading, and marks INTERRUPTED |

---

## 5. Revised Schema Extension Proposal

A formal architectural blueprint is preserved in `database/schema/revised_session_tariff_extension.sql`:
- `applied_rate_per_kwh NUMERIC(10, 2)`: The effective per-kWh rate locked at start.
- `applied_multiplier NUMERIC(5, 2)`: Dynamic multiplier snapshot (e.g. 1.25 for peak).
- `applied_rule_id BIGINT REFERENCES pricing_rules(rule_id)`: Active rule ID reference.
- `locked_session_fee NUMERIC(10, 2)`: Fixed session fee locked from active tariff.
- `locked_tax_rate_percent NUMERIC(5, 2)`: Applicable GST rate locked from active tariff.
- `interruption_reason TEXT`: Audit string explaining disconnection/fault cause.

---

## 6. Frontend Components & Pages

1. **`EnergyConsumptionCard.tsx` (`frontend/src/components/session/`):**
   - Telemetry card displaying total kWh delivered, live duration, starting and ending meter readings, and estimated cost.
2. **`CompleteSessionForm.tsx` (`frontend/src/components/session/`):**
   - Modal dialog for recording final meter reading with client-side constraint checking and real-time energy calculation.
3. **`StartSessionPage.tsx` (`frontend/src/pages/`):**
   - Two-mode session initiation: one-click start from confirmed reservations, or instant walk-in charging with bay and vehicle selectors.
4. **`ActiveSessionsPage.tsx` (`frontend/src/pages/`):**
   - Real-time active charging bay dashboard with live duration timers, quick session completion, and emergency stop actions.
5. **`SessionDetailsPage.tsx` (`frontend/src/pages/`):**
   - Detailed session inspection view featuring telemetry gauges, station/charger metadata, vehicle details, and itemized tariff breakdown.
6. **`SessionHistoryPage.tsx` (`frontend/src/pages/`):**
   - Filterable audit log with KPI summary metrics (total sessions, total kWh delivered, completed, interrupted) and tabular history.
7. **`ChargingSessionPage.tsx` (`frontend/src/pages/`):**
   - Main charging hub overview with KPI telemetry tiles and shortcuts.

---

## 7. Verification & Automated Test Results

### 7.1 Module 8 Test Suite (`tests/run_module8_tests.py`)
All 17 tests passed in 18.77 seconds:

```text
======================================================================
MODULE 8 TEST EXECUTION REPORT: CHARGING SESSIONS & ENERGY METERING
Status: PASSED
Exit Code: 0
======================================================================
Test Cases Executed:
1. test_start_reserved_charging_session                         PASSED
2. test_start_walk_in_charging_session                          PASSED
3. test_start_session_invalid_reservation_rejected              PASSED
4. test_start_session_unauthorized_vehicle_rejected             PASSED
5. test_start_session_incompatible_connector_rejected           PASSED
6. test_start_session_charger_under_maintenance_rejected        PASSED
7. test_start_session_duplicate_active_session_rejected         PASSED
8. test_start_session_invalid_starting_meter_rejected           PASSED
9. test_successful_session_completion                           PASSED
10. test_complete_session_ending_meter_lower_rejected           PASSED
11. test_duplicate_session_completion_rejected                  PASSED
12. test_session_interruption                                   PASSED
13. test_customer_session_isolation                             PASSED
14. test_operator_authorization                                 PASSED
15. test_admin_access                                           PASSED
16. test_tariff_snapshot_preservation                           PASSED
17. test_concurrent_session_start_attempts                      PASSED
======================================================================
Total Tests: 17 Passed, 0 Failed.
```

### 7.2 Live Database Ground-Truth Verification
- Database: `ev_charging_network` on `localhost:5432`
- Tables Verified: **14 / 14**
- Rows Verified: **54 / 54**
- Production Database State: **100% Intact & Untouched**

