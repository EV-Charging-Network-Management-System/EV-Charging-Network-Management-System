# EV Charging Network Database Verification Report

- **Generated At:** 2026-11-17T05:59:49.586124+00:00
- **Database Host:** `localhost:5432`
- **Database Name:** `ev_charging_network`
- **Database User:** `postgres` (Password hidden)
- **Server Version:** PostgreSQL 18.7 on x86_64-windows, compiled by msvc-19.44.35229, 64-bit
- **Session Security:** `transaction_read_only = on`
- **Verification Status:** **`PASS`**

---
## 1. Executive Summary

| Metric | Expected | Actual | Status |
| :--- | :--- | :--- | :--- |
| Core Base Tables | 14 | 14 | PASS |
| Total Records Loaded | 54 | 54 | PASS |

## 2. Table-by-Table Verification Matrix

| # | Table Name | Columns | Primary Key | Foreign Keys | Row Count | Expected | Status |
| :-: | :--- | :-: | :--- | :-: | :-: | :-: | :-: |
| 1 | `users` | 8 | `user_id` | 0 | **5** | 5 | PASS |
| 2 | `connector_types` | 3 | `connector_type_id` | 0 | **4** | 4 | PASS |
| 3 | `vehicles` | 7 | `vehicle_id` | 1 | **3** | 3 | PASS |
| 4 | `vehicle_connector_types` | 2 | `connector_type_id, vehicle_id` | 2 | **6** | 6 | PASS |
| 5 | `stations` | 10 | `station_id` | 1 | **3** | 3 | PASS |
| 6 | `chargers` | 6 | `charger_id` | 2 | **5** | 5 | PASS |
| 7 | `tariffs` | 8 | `tariff_id` | 2 | **4** | 4 | PASS |
| 8 | `pricing_rules` | 9 | `rule_id` | 1 | **3** | 3 | PASS |
| 9 | `reservations` | 8 | `reservation_id` | 3 | **7** | 7 | PASS |
| 10 | `charging_sessions` | 11 | `session_id` | 5 | **3** | 3 | PASS |
| 11 | `invoices` | 11 | `invoice_id` | 1 | **2** | 2 | PASS |
| 12 | `payments` | 8 | `payment_id` | 1 | **3** | 3 | PASS |
| 13 | `maintenance_records` | 11 | `maintenance_id` | 3 | **2** | 2 | PASS |
| 14 | `charger_status_history` | 7 | `history_id` | 2 | **4** | 4 | PASS |

---
## 3. Detailed Table Schema Specifications

### Table: `users` (5 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `user_id` | bigint(64,0) | NO | `-` |
| `full_name` | character varying(100) | NO | `-` |
| `email` | character varying(150) | NO | `-` |
| `phone` | character varying(20) | YES | `-` |
| `password_hash` | character varying(255) | NO | `-` |
| `role` | character varying(20) | NO | `'CUSTOMER'::character varying` |
| `is_active` | boolean | NO | `true` |
| `created_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |

**Indexes:**
- `users_email_key`: `CREATE UNIQUE INDEX users_email_key ON public.users USING btree (email)`
- `users_pkey`: `CREATE UNIQUE INDEX users_pkey ON public.users USING btree (user_id)`

### Table: `connector_types` (4 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `connector_type_id` | integer(32,0) | NO | `-` |
| `type_name` | character varying(60) | NO | `-` |
| `description` | character varying(255) | YES | `-` |

**Indexes:**
- `connector_types_pkey`: `CREATE UNIQUE INDEX connector_types_pkey ON public.connector_types USING btree (connector_type_id)`
- `connector_types_type_name_key`: `CREATE UNIQUE INDEX connector_types_type_name_key ON public.connector_types USING btree (type_name)`

### Table: `vehicles` (3 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `vehicle_id` | bigint(64,0) | NO | `-` |
| `owner_user_id` | bigint(64,0) | NO | `-` |
| `registration_number` | character varying(30) | NO | `-` |
| `make` | character varying(60) | NO | `-` |
| `model` | character varying(80) | NO | `-` |
| `battery_capacity_kwh` | numeric(7,2) | YES | `-` |
| `created_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |

**Foreign Keys:**
- `owner_user_id` -> `users(user_id)` (`vehicles_owner_user_id_fkey`)

**Indexes:**
- `idx_vehicles_owner`: `CREATE INDEX idx_vehicles_owner ON public.vehicles USING btree (owner_user_id)`
- `vehicles_pkey`: `CREATE UNIQUE INDEX vehicles_pkey ON public.vehicles USING btree (vehicle_id)`
- `vehicles_registration_number_key`: `CREATE UNIQUE INDEX vehicles_registration_number_key ON public.vehicles USING btree (registration_number)`

### Table: `vehicle_connector_types` (6 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `vehicle_id` | bigint(64,0) | NO | `-` |
| `connector_type_id` | integer(32,0) | NO | `-` |

**Foreign Keys:**
- `vehicle_id` -> `vehicles(vehicle_id)` (`vehicle_connector_types_vehicle_id_fkey`)
- `connector_type_id` -> `connector_types(connector_type_id)` (`vehicle_connector_types_connector_type_id_fkey`)

**Indexes:**
- `vehicle_connector_types_pkey`: `CREATE UNIQUE INDEX vehicle_connector_types_pkey ON public.vehicle_connector_types USING btree (vehicle_id, connector_type_id)`

### Table: `stations` (3 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `station_id` | bigint(64,0) | NO | `-` |
| `operator_id` | bigint(64,0) | YES | `-` |
| `station_name` | character varying(120) | NO | `-` |
| `address` | character varying(255) | NO | `-` |
| `city` | character varying(80) | NO | `-` |
| `latitude` | numeric(10,7) | YES | `-` |
| `longitude` | numeric(10,7) | YES | `-` |
| `opening_time` | time without time zone | YES | `-` |
| `closing_time` | time without time zone | YES | `-` |
| `status` | character varying(20) | NO | `'ACTIVE'::character varying` |

**Foreign Keys:**
- `operator_id` -> `users(user_id)` (`stations_operator_id_fkey`)

**Indexes:**
- `idx_stations_city`: `CREATE INDEX idx_stations_city ON public.stations USING btree (city)`
- `stations_pkey`: `CREATE UNIQUE INDEX stations_pkey ON public.stations USING btree (station_id)`

### Table: `chargers` (5 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `charger_id` | bigint(64,0) | NO | `-` |
| `station_id` | bigint(64,0) | NO | `-` |
| `connector_type_id` | integer(32,0) | NO | `-` |
| `charger_code` | character varying(40) | NO | `-` |
| `power_kw` | numeric(7,2) | NO | `-` |
| `operational_status` | character varying(25) | NO | `'ONLINE'::character varying` |

**Foreign Keys:**
- `station_id` -> `stations(station_id)` (`chargers_station_id_fkey`)
- `connector_type_id` -> `connector_types(connector_type_id)` (`chargers_connector_type_id_fkey`)

**Indexes:**
- `chargers_pkey`: `CREATE UNIQUE INDEX chargers_pkey ON public.chargers USING btree (charger_id)`
- `chargers_station_id_charger_code_key`: `CREATE UNIQUE INDEX chargers_station_id_charger_code_key ON public.chargers USING btree (station_id, charger_code)`
- `idx_chargers_station_status`: `CREATE INDEX idx_chargers_station_status ON public.chargers USING btree (station_id, operational_status)`

### Table: `tariffs` (4 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `tariff_id` | bigint(64,0) | NO | `-` |
| `station_id` | bigint(64,0) | NO | `-` |
| `connector_type_id` | integer(32,0) | YES | `-` |
| `base_price_per_kwh` | numeric(10,2) | NO | `-` |
| `session_fee` | numeric(10,2) | NO | `0` |
| `tax_rate_percent` | numeric(5,2) | NO | `0` |
| `valid_from` | timestamp with time zone | NO | `-` |
| `valid_to` | timestamp with time zone | YES | `-` |

**Foreign Keys:**
- `station_id` -> `stations(station_id)` (`tariffs_station_id_fkey`)
- `connector_type_id` -> `connector_types(connector_type_id)` (`tariffs_connector_type_id_fkey`)

**Indexes:**
- `idx_tariffs_station_validity`: `CREATE INDEX idx_tariffs_station_validity ON public.tariffs USING btree (station_id, valid_from, valid_to)`
- `tariffs_pkey`: `CREATE UNIQUE INDEX tariffs_pkey ON public.tariffs USING btree (tariff_id)`

### Table: `pricing_rules` (3 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `rule_id` | bigint(64,0) | NO | `-` |
| `tariff_id` | bigint(64,0) | NO | `-` |
| `rule_type` | character varying(30) | NO | `-` |
| `start_time` | time without time zone | YES | `-` |
| `end_time` | time without time zone | YES | `-` |
| `demand_threshold_percent` | numeric(5,2) | YES | `-` |
| `price_multiplier` | numeric(6,3) | NO | `1.000` |
| `priority` | integer(32,0) | NO | `1` |
| `is_active` | boolean | NO | `true` |

**Foreign Keys:**
- `tariff_id` -> `tariffs(tariff_id)` (`pricing_rules_tariff_id_fkey`)

**Indexes:**
- `pricing_rules_pkey`: `CREATE UNIQUE INDEX pricing_rules_pkey ON public.pricing_rules USING btree (rule_id)`

### Table: `reservations` (7 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `reservation_id` | bigint(64,0) | NO | `-` |
| `user_id` | bigint(64,0) | NO | `-` |
| `vehicle_id` | bigint(64,0) | NO | `-` |
| `charger_id` | bigint(64,0) | NO | `-` |
| `start_at` | timestamp with time zone | NO | `-` |
| `end_at` | timestamp with time zone | NO | `-` |
| `status` | character varying(20) | NO | `'CONFIRMED'::character varying` |
| `created_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |

**Foreign Keys:**
- `user_id` -> `users(user_id)` (`reservations_user_id_fkey`)
- `vehicle_id` -> `vehicles(vehicle_id)` (`reservations_vehicle_id_fkey`)
- `charger_id` -> `chargers(charger_id)` (`reservations_charger_id_fkey`)

**Indexes:**
- `idx_reservations_charger_time`: `CREATE INDEX idx_reservations_charger_time ON public.reservations USING btree (charger_id, start_at, end_at)`
- `idx_reservations_user`: `CREATE INDEX idx_reservations_user ON public.reservations USING btree (user_id, start_at DESC)`
- `reservations_pkey`: `CREATE UNIQUE INDEX reservations_pkey ON public.reservations USING btree (reservation_id)`

### Table: `charging_sessions` (3 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `session_id` | bigint(64,0) | NO | `-` |
| `reservation_id` | bigint(64,0) | YES | `-` |
| `user_id` | bigint(64,0) | NO | `-` |
| `vehicle_id` | bigint(64,0) | NO | `-` |
| `charger_id` | bigint(64,0) | NO | `-` |
| `tariff_id` | bigint(64,0) | NO | `-` |
| `started_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |
| `ended_at` | timestamp with time zone | YES | `-` |
| `meter_start_kwh` | numeric(12,3) | NO | `-` |
| `meter_end_kwh` | numeric(12,3) | YES | `-` |
| `status` | character varying(20) | NO | `'ACTIVE'::character varying` |

**Foreign Keys:**
- `reservation_id` -> `reservations(reservation_id)` (`charging_sessions_reservation_id_fkey`)
- `user_id` -> `users(user_id)` (`charging_sessions_user_id_fkey`)
- `vehicle_id` -> `vehicles(vehicle_id)` (`charging_sessions_vehicle_id_fkey`)
- `charger_id` -> `chargers(charger_id)` (`charging_sessions_charger_id_fkey`)
- `tariff_id` -> `tariffs(tariff_id)` (`charging_sessions_tariff_id_fkey`)

**Indexes:**
- `charging_sessions_pkey`: `CREATE UNIQUE INDEX charging_sessions_pkey ON public.charging_sessions USING btree (session_id)`
- `charging_sessions_reservation_id_key`: `CREATE UNIQUE INDEX charging_sessions_reservation_id_key ON public.charging_sessions USING btree (reservation_id)`
- `idx_sessions_charger_status`: `CREATE INDEX idx_sessions_charger_status ON public.charging_sessions USING btree (charger_id, status)`

### Table: `invoices` (2 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `invoice_id` | bigint(64,0) | NO | `-` |
| `session_id` | bigint(64,0) | NO | `-` |
| `energy_kwh` | numeric(12,3) | NO | `-` |
| `price_per_kwh` | numeric(10,2) | NO | `-` |
| `session_fee` | numeric(10,2) | NO | `0` |
| `tax_rate_percent` | numeric(5,2) | NO | `0` |
| `energy_charge` | numeric(12,2) | NO | `-` |
| `tax_amount` | numeric(12,2) | NO | `-` |
| `total_amount` | numeric(12,2) | NO | `-` |
| `status` | character varying(20) | NO | `'UNPAID'::character varying` |
| `issued_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |

**Foreign Keys:**
- `session_id` -> `charging_sessions(session_id)` (`invoices_session_id_fkey`)

**Indexes:**
- `idx_invoices_status`: `CREATE INDEX idx_invoices_status ON public.invoices USING btree (status)`
- `invoices_pkey`: `CREATE UNIQUE INDEX invoices_pkey ON public.invoices USING btree (invoice_id)`
- `invoices_session_id_key`: `CREATE UNIQUE INDEX invoices_session_id_key ON public.invoices USING btree (session_id)`

### Table: `payments` (3 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `payment_id` | bigint(64,0) | NO | `-` |
| `invoice_id` | bigint(64,0) | NO | `-` |
| `amount` | numeric(12,2) | NO | `-` |
| `payment_method` | character varying(20) | NO | `'DEMO'::character varying` |
| `transaction_reference` | character varying(120) | YES | `-` |
| `status` | character varying(20) | NO | `'PENDING'::character varying` |
| `created_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |
| `paid_at` | timestamp with time zone | YES | `-` |

**Foreign Keys:**
- `invoice_id` -> `invoices(invoice_id)` (`payments_invoice_id_fkey`)

**Indexes:**
- `idx_payments_invoice_status`: `CREATE INDEX idx_payments_invoice_status ON public.payments USING btree (invoice_id, status)`
- `payments_pkey`: `CREATE UNIQUE INDEX payments_pkey ON public.payments USING btree (payment_id)`
- `payments_transaction_reference_key`: `CREATE UNIQUE INDEX payments_transaction_reference_key ON public.payments USING btree (transaction_reference)`

### Table: `maintenance_records` (2 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `maintenance_id` | bigint(64,0) | NO | `-` |
| `charger_id` | bigint(64,0) | NO | `-` |
| `reported_by` | bigint(64,0) | NO | `-` |
| `assigned_to` | bigint(64,0) | YES | `-` |
| `issue_description` | text | NO | `-` |
| `priority` | character varying(15) | NO | `'MEDIUM'::character varying` |
| `status` | character varying(20) | NO | `'OPEN'::character varying` |
| `reported_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |
| `scheduled_at` | timestamp with time zone | YES | `-` |
| `resolved_at` | timestamp with time zone | YES | `-` |
| `maintenance_cost` | numeric(12,2) | NO | `0` |

**Foreign Keys:**
- `charger_id` -> `chargers(charger_id)` (`maintenance_records_charger_id_fkey`)
- `reported_by` -> `users(user_id)` (`maintenance_records_reported_by_fkey`)
- `assigned_to` -> `users(user_id)` (`maintenance_records_assigned_to_fkey`)

**Indexes:**
- `idx_maintenance_status`: `CREATE INDEX idx_maintenance_status ON public.maintenance_records USING btree (status, priority)`
- `maintenance_records_pkey`: `CREATE UNIQUE INDEX maintenance_records_pkey ON public.maintenance_records USING btree (maintenance_id)`

### Table: `charger_status_history` (4 rows)

| Column | Data Type | Nullable | Default |
| :--- | :--- | :--- | :--- |
| `history_id` | bigint(64,0) | NO | `-` |
| `charger_id` | bigint(64,0) | NO | `-` |
| `previous_status` | character varying(25) | YES | `-` |
| `new_status` | character varying(25) | NO | `-` |
| `changed_by` | bigint(64,0) | YES | `-` |
| `reason` | text | YES | `-` |
| `changed_at` | timestamp with time zone | NO | `CURRENT_TIMESTAMP` |

**Foreign Keys:**
- `charger_id` -> `chargers(charger_id)` (`charger_status_history_charger_id_fkey`)
- `changed_by` -> `users(user_id)` (`charger_status_history_changed_by_fkey`)

**Indexes:**
- `charger_status_history_pkey`: `CREATE UNIQUE INDEX charger_status_history_pkey ON public.charger_status_history USING btree (history_id)`
- `idx_charger_history_charger_time`: `CREATE INDEX idx_charger_history_charger_time ON public.charger_status_history USING btree (charger_id, changed_at DESC)`
