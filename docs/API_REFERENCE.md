# REST API Reference: EV Charging Network Management System

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Interactive Swagger UI:** [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)  
**Authentication:** HTTP Bearer Token (`Authorization: Bearer <JWT_ACCESS_TOKEN>`)  
**Data Format:** JSON (`Content-Type: application/json`)  

---

## Table of Contents
1. [Authentication Endpoints (`/auth`)](#1-authentication-endpoints-auth)
2. [User Management Endpoints (`/users`)](#2-user-management-endpoints-users)
3. [Vehicle & Connector Endpoints (`/vehicles`, `/connector-types`)](#3-vehicle--connector-endpoints-vehicles-connector-types)
4. [Station & Charger Endpoints (`/stations`, `/chargers`)](#4-station--charger-endpoints-stations-chargers)
5. [Tariffs & Dynamic Pricing Endpoints (`/pricing`)](#5-tariffs--dynamic-pricing-endpoints-pricing)
6. [Reservation & Availability Endpoints (`/reservations`)](#6-reservation--availability-endpoints-reservations)
7. [Charging Session & Metering Endpoints (`/sessions`)](#7-charging-session--metering-endpoints-sessions)
8. [Invoicing Endpoints (`/invoices`)](#8-invoicing-endpoints-invoices)
9. [Payment & Refund Endpoints (`/payments`)](#9-payment--refund-endpoints-payments)
10. [Revenue Reporting Endpoints (`/reports`)](#10-revenue-reporting-endpoints-reports)
11. [Maintenance Work Orders (`/maintenance`)](#11-maintenance-work-orders-maintenance)
12. [Operational Status Audit Trail (`/charger-status-history`)](#12-operational-status-audit-trail-charger-status-history)
13. [Health & System Inspection (`/health`)](#13-health--system-inspection-health)

---

## 1. Authentication Endpoints (`/auth`)

### `POST /auth/register`
Register a new customer account.
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "customer@example.com",
    "password": "SecurePassword123!",
    "phone": "+919876543210",
    "first_name": "Rahul",
    "last_name": "Sharma"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "user_id": 6,
    "email": "customer@example.com",
    "phone": "+919876543210",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "role": "CUSTOMER",
    "status": "ACTIVE",
    "created_at": "2026-11-17T11:00:00Z"
  }
  ```

### `POST /auth/login`
Authenticate with email and password to receive a JWT access token.
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "customer@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "user_id": 6,
      "email": "customer@example.com",
      "role": "CUSTOMER"
    }
  }
  ```

### `GET /auth/me`
Retrieve profile of currently authenticated user.
- **Access:** Authenticated (Any active role)
- **Response (200 OK):**
  ```json
  {
    "user_id": 6,
    "email": "customer@example.com",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "role": "CUSTOMER",
    "status": "ACTIVE"
  }
  ```

---

## 2. User Management Endpoints (`/users`)

### `GET /users/profile`
Retrieve self user profile.
- **Access:** Authenticated User

### `PUT /users/profile`
Update self user profile (first name, last name, phone).
- **Access:** Authenticated User

### `GET /users`
List all users across the platform with optional role and status filters.
- **Access:** `ADMIN`
- **Query Parameters:** `role` (optional), `status` (optional), `limit` (default 50), `offset` (default 0)

### `PUT /users/{id}/role`
Promote or change user role.
- **Access:** `ADMIN`
- **Request Body:** `{ "role": "OPERATOR" }`

### `PUT /users/{id}/status`
Update user account status (`ACTIVE`, `SUSPENDED`, `DEACTIVATED`).
- **Access:** `ADMIN`

---

## 3. Vehicle & Connector Endpoints (`/vehicles`, `/connector-types`)

### `GET /vehicles`
List vehicles belonging to the authenticated customer (or all vehicles if Admin).
- **Access:** `CUSTOMER`, `ADMIN`

### `POST /vehicles`
Register a new electric vehicle.
- **Access:** `CUSTOMER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "make": "Tata",
    "model": "Nexon EV",
    "year": 2024,
    "license_plate": "KA-01-EQ-9988",
    "battery_capacity_kwh": 40.5
  }
  ```

### `GET /vehicles/{id}`
Retrieve vehicle details and supported connector standards.
- **Access:** Vehicle Owner or `ADMIN`

### `PUT /vehicles/{id}/connectors`
Atomically configure supported charging connector ports for a vehicle.
- **Access:** Vehicle Owner or `ADMIN`
- **Request Body:**
  ```json
  {
    "connector_type_ids": [1, 2]
  }
  ```

### `GET /connector-types`
List all recognized charging connector standards.
- **Access:** Public / Authenticated
- **Response (200 OK):**
  ```json
  [
    { "connector_type_id": 1, "name": "CCS-2", "current_type": "DC", "max_power_kw": 350.0 },
    { "connector_type_id": 2, "name": "Type 2 AC", "current_type": "AC", "max_power_kw": 22.0 },
    { "connector_type_id": 3, "name": "CHAdeMO", "current_type": "DC", "max_power_kw": 62.5 },
    { "connector_type_id": 4, "name": "GB/T", "current_type": "DC", "max_power_kw": 237.5 }
  ]
  ```

---

## 4. Station & Charger Endpoints (`/stations`, `/chargers`)

### `GET /stations`
List charging stations with filters by city, status, and connector availability.
- **Access:** Public / Authenticated

### `GET /stations/search/nearby`
Search stations within a geographic radius using Haversine spherical distance calculation.
- **Access:** Public / Authenticated
- **Query Parameters:**
  - `lat` (float, required): User latitude (e.g. `12.9716`)
  - `lon` (float, required): User longitude (e.g. `77.5946`)
  - `radius_km` (float, optional, default `10.0`): Search radius in kilometers
- **Response (200 OK):**
  ```json
  [
    {
      "station_id": 1,
      "station_name": "MG Road Supercharger Hub",
      "city": "Bengaluru",
      "latitude": 12.975000,
      "longitude": 77.605000,
      "distance_km": 1.21,
      "status": "ACTIVE"
    }
  ]
  ```

### `POST /stations`
Create a new charging station.
- **Access:** `OPERATOR`, `ADMIN`

### `GET /chargers`
List charger bays with filters by `station_id`, `status`, and `connector_type_id`.
- **Access:** Public / Authenticated

### `POST /chargers`
Commission a new charger bay at a station.
- **Access:** `OPERATOR`, `ADMIN`

### `PUT /chargers/{id}/status`
Transition charger operational status (`ONLINE`, `MAINTENANCE`, `OFFLINE`).
- **Access:** `OPERATOR`, `ADMIN`
- **Request Body:**
  ```json
  {
    "new_status": "MAINTENANCE",
    "reason": "Cable insulation damage reported"
  }
  ```
- **Side Effect:** Automatically appends entry to `charger_status_history`.

---

## 5. Tariffs & Dynamic Pricing Endpoints (`/pricing`)

### `GET /pricing/quote`
Compute dynamic, pure read-only price quotation for estimated energy and time.
- **Access:** Public / Authenticated
- **Query Parameters:**
  - `charger_id` (int, required)
  - `estimated_energy_kwh` (float, required)
  - `start_time` (ISO datetime string, optional)
- **Response (200 OK):**
  ```json
  {
    "charger_id": 1,
    "estimated_energy_kwh": 30.0,
    "base_rate_per_kwh": 18.50,
    "applied_multiplier": 1.25,
    "effective_rate_per_kwh": 23.125,
    "energy_cost": 693.75,
    "session_fee": 25.00,
    "tax_gst_amount": 129.38,
    "total_amount": 848.13,
    "applied_rules": ["PEAK_HOUR (1.25x)"]
  }
  ```

### `GET /pricing/tariffs` & `POST /pricing/tariffs`
Query active tariffs or create new base tariff schedules.
- **Access:** `ADMIN` (POST), Authenticated (GET)

### `GET /pricing/rules` & `POST /pricing/rules`
Query dynamic pricing rules or configure peak surge / off-peak discounts.
- **Access:** `ADMIN` (POST), Authenticated (GET)

---

## 6. Reservation & Availability Endpoints (`/reservations`)

### `GET /reservations/availability/search`
Find available charger slots within a time range for a specific vehicle connector.
- **Access:** Public / Authenticated
- **Query Parameters:** `station_id`, `start_at`, `end_at`, `vehicle_id`

### `POST /reservations`
Book a collision-free charging slot.
- **Access:** `CUSTOMER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "charger_id": 1,
    "vehicle_id": 2,
    "start_at": "2026-11-17T14:00:00Z",
    "end_at": "2026-11-17T15:00:00Z"
  }
  ```
- **Error Responses:**
  - `409 Conflict`: Slot overlaps an existing booking.
  - `422 Unprocessable Content`: Incompatible connector standard between vehicle and charger.

### `PUT /reservations/{id}/cancel`
Cancel an upcoming reservation.
- **Access:** Reservation Owner or `ADMIN`

---

## 7. Charging Session & Metering Endpoints (`/sessions`)

### `POST /sessions/start`
Initiate a charging session (walk-in or check-in with reservation).
- **Access:** `CUSTOMER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "charger_id": 1,
    "vehicle_id": 2,
    "reservation_id": 4,
    "meter_start_kwh": 150.20
  }
  ```

### `PUT /sessions/{id}/complete`
End a charging session and record final meter reading.
- **Access:** Session Owner, `OPERATOR`, `ADMIN`
- **Request Body:**
  ```json
  {
    "meter_end_kwh": 178.70
  }
  ```
- **Side Effect:** Computes `total_energy_kwh = 28.50`, updates status to `COMPLETED`, releases charger to `ONLINE`, and snapshots billable data.

### `PUT /sessions/{id}/interrupt`
Abruptly terminate an active session (emergency stop or hardware trip).
- **Access:** Session Owner, `OPERATOR`, `ADMIN`
- **Request Body:** `{ "interruption_reason": "Emergency disconnect pulled" }`

---

## 8. Invoicing Endpoints (`/invoices`)

### `POST /invoices/generate/{session_id}`
Generate an immutable financial invoice for a completed charging session.
- **Access:** Session Owner, `OPERATOR`, `ADMIN`
- **Response (201 Created):**
  ```json
  {
    "invoice_id": 5,
    "session_id": 3,
    "user_id": 6,
    "base_amount": 684.50,
    "tax_amount": 123.21,
    "total_amount": 807.71,
    "status": "UNPAID",
    "issued_at": "2026-11-17T12:00:00Z"
  }
  ```

### `GET /invoices`
List invoices with status filter (`UNPAID`, `PAID`, `CANCELLED`).
- **Access:** Scoped to Customer; `ADMIN` sees all.

### `GET /invoices/{id}`
Retrieve full invoice details with itemized charges.
- **Access:** Invoice Owner or `ADMIN`

---

## 9. Payment & Refund Endpoints (`/payments`)

### `POST /payments/process`
Process a payment transaction against an unpaid invoice.
- **Access:** `CUSTOMER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "invoice_id": 5,
    "amount": 807.71,
    "payment_method": "DEMO",
    "simulate_failure": false
  }
  ```
- **Behavior:**
  - If `simulate_failure=true`: Payment record created with status `FAILED`, invoice remains `UNPAID`.
  - If successful: Payment record created with status `SUCCESS`, invoice transitions to `PAID`.

### `GET /payments/history/invoice/{invoice_id}`
Retrieve all payment attempts (failed, pending, successful) for an invoice.
- **Access:** Invoice Owner or `ADMIN`

### `POST /payments/{id}/refund`
Initiate an authorized refund for a completed payment.
- **Access:** `ADMIN`

---

## 10. Revenue Reporting Endpoints (`/reports`)

### `GET /reports/revenue/summary`
Executive financial revenue overview.
- **Access:** `ADMIN`
- **Response (200 OK):**
  ```json
  {
    "total_revenue": 142500.50,
    "total_energy_delivered_kwh": 6580.20,
    "paid_invoices_count": 482,
    "unpaid_invoices_count": 18
  }
  ```

### `GET /reports/revenue/station-breakdown`
Aggregated revenue, sessions, and energy delivery grouped by station.
- **Access:** `ADMIN`

---

## 11. Maintenance Work Orders (`/maintenance`)

### `POST /maintenance/records`
Report a physical equipment fault and generate a work order ticket.
- **Access:** `OPERATOR`, `ADMIN`
- **Request Body:**
  ```json
  {
    "charger_id": 2,
    "description": "DC connector latch failure",
    "priority": "HIGH"
  }
  ```

### `PUT /maintenance/records/{id}/assign`
Assign a certified technician to an open work order.
- **Access:** `OPERATOR`, `ADMIN`
- **Side Effect:** Automatically transitions charger status to `MAINTENANCE` and locks bay.

### `PUT /maintenance/records/{id}/resolve`
Resolve a work order with technician resolution notes and repair costs.
- **Access:** `OPERATOR`, `ADMIN`
- **Request Body:**
  ```json
  {
    "resolution_notes": "Replaced CCS-2 contact pins and latch spring",
    "cost": 185.00
  }
  ```

### `GET /maintenance/analytics/mttr`
Compute network-wide Mean Time to Repair (MTTR) analytics.
- **Access:** `OPERATOR`, `ADMIN`

---

## 12. Operational Status Audit Trail (`/charger-status-history`)

### `GET /charger-status-history`
Query chronological, tamper-evident audit history of charger transitions.
- **Access:** `OPERATOR`, `ADMIN`
- **Query Parameters:** `charger_id` (optional), `limit` (default 50), `offset` (default 0)

---

## 13. Health & System Inspection (`/health`)

### `GET /health`
Basic service ping returning operational status.
- **Access:** Public

### `GET /health/db-check`
Performs read-only connection check against PostgreSQL 18.
- **Access:** Public
- **Response (200 OK):**
  ```json
  {
    "database": "connected",
    "dialect": "postgresql",
    "version": "PostgreSQL 18.0",
    "read_only": true
  }
  ```

