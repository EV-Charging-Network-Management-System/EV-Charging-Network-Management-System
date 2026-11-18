-- ============================================================================
-- EV CHARGING NETWORK MANAGEMENT SYSTEM
-- Step 4: Insert demonstration records into the 14 tables already created.
-- IMPORTANT: Run this file in the ev_charging_network database, once only.
-- All names, vehicle registrations, phone numbers and payments are fictional.
-- Password values are placeholders; this dataset is for database demonstration,
-- not for authenticating into the future application.
-- ============================================================================

BEGIN;

-- 1. USERS
INSERT INTO users
    (user_id, full_name, email, phone, password_hash, role, is_active, created_at)
VALUES
    (1, 'Ananya Rao', 'ananya.demo@example.com', '9000000001', 'demo_placeholder_1', 'CUSTOMER', TRUE, '2026-11-01 09:00:00+05:30'),
    (2, 'Karan Shah', 'karan.demo@example.com', '9000000002', 'demo_placeholder_2', 'CUSTOMER', TRUE, '2026-11-02 10:00:00+05:30'),
    (3, 'Priya Nair', 'priya.operator@example.com', '9000000003', 'demo_placeholder_3', 'OPERATOR', TRUE, '2026-10-20 09:00:00+05:30'),
    (4, 'System Admin', 'admin.demo@example.com', '9000000004', 'demo_placeholder_4', 'ADMIN', TRUE, '2026-10-15 09:00:00+05:30'),
    (5, 'Arjun Shetty', 'arjun.demo@example.com', '9000000005', 'demo_placeholder_5', 'CUSTOMER', TRUE, '2026-11-03 11:00:00+05:30');

-- 2. CONNECTOR_TYPES
INSERT INTO connector_types (connector_type_id, type_name, description)
VALUES
    (1, 'CCS2', 'Combined Charging System Type 2 DC connector'),
    (2, 'TYPE2', 'Type 2 AC charging connector'),
    (3, 'CHADEMO', 'CHAdeMO DC fast charging connector'),
    (4, 'GB_T', 'GB/T charging connector standard');

-- 3. VEHICLES
INSERT INTO vehicles
    (vehicle_id, owner_user_id, registration_number, make, model, battery_capacity_kwh, created_at)
VALUES
    (1, 1, 'KA03EV1001', 'Tata', 'Nexon EV', 40.50, '2026-11-01 09:30:00+05:30'),
    (2, 2, 'KA05EV2002', 'MG', 'ZS EV', 50.30, '2026-11-02 10:30:00+05:30'),
    (3, 5, 'KA01EV3003', 'Nissan', 'Leaf', 40.00, '2026-11-03 11:30:00+05:30');

-- 4. VEHICLE_CONNECTOR_TYPES (junction table)
INSERT INTO vehicle_connector_types (vehicle_id, connector_type_id)
VALUES
    (1, 1), (1, 2),
    (2, 1), (2, 2),
    (3, 2), (3, 3);

-- 5. STATIONS
INSERT INTO stations
    (station_id, operator_id, station_name, address, city, latitude, longitude,
     opening_time, closing_time, status)
VALUES
    (1, 3, 'GreenCharge Koramangala', '80 Feet Road, Koramangala, Bengaluru', 'Bengaluru', 12.9352000, 77.6245000, '06:00', '23:00', 'ACTIVE'),
    (2, 3, 'GreenCharge Whitefield', 'ITPL Main Road, Whitefield, Bengaluru', 'Bengaluru', 12.9698000, 77.7500000, '00:00', '23:59', 'ACTIVE'),
    (3, 3, 'GreenCharge Mysuru Road', 'Nayandahalli, Bengaluru', 'Bengaluru', 12.9447000, 77.5250000, '07:00', '22:00', 'ACTIVE');

-- 6. CHARGERS
INSERT INTO chargers
    (charger_id, station_id, connector_type_id, charger_code, power_kw, operational_status)
VALUES
    (1, 1, 1, 'KOR-CCS-01', 60.00, 'ONLINE'),
    (2, 1, 2, 'KOR-T2-02', 22.00, 'ONLINE'),
    (3, 2, 1, 'WFD-CCS-01', 120.00, 'ONLINE'),
    (4, 2, 3, 'WFD-CHA-02', 50.00, 'MAINTENANCE'),
    (5, 3, 3, 'MYS-CHA-01', 50.00, 'ONLINE');

-- 7. TARIFFS
INSERT INTO tariffs
    (tariff_id, station_id, connector_type_id, base_price_per_kwh,
     session_fee, tax_rate_percent, valid_from, valid_to)
VALUES
    (1, 1, 1, 12.50, 10.00, 5.00, '2026-01-01 00:00:00+05:30', NULL),
    (2, 1, 2, 10.00,  5.00, 5.00, '2026-01-01 00:00:00+05:30', NULL),
    (3, 2, 1, 14.00, 15.00, 5.00, '2026-01-01 00:00:00+05:30', NULL),
    (4, 3, 3, 11.50,  8.00, 5.00, '2026-01-01 00:00:00+05:30', NULL);

-- 8. PRICING_RULES
-- rule_type values intentionally match the CHECK constraint in Step 3 schema.
INSERT INTO pricing_rules
    (rule_id, tariff_id, rule_type, start_time, end_time,
     demand_threshold_percent, price_multiplier, priority, is_active)
VALUES
    (1, 1, 'PEAK_HOUR', '17:00', '21:00', NULL, 1.200, 1, TRUE),
    (2, 3, 'HIGH_DEMAND', NULL, NULL, 75.00, 1.300, 1, TRUE),
    (3, 2, 'OFF_PEAK', '00:00', '06:00', NULL, 0.900, 2, TRUE);

-- 9. RESERVATIONS
-- Past completed/cancelled/no-show examples plus future reservations.
INSERT INTO reservations
    (reservation_id, user_id, vehicle_id, charger_id, start_at, end_at, status, created_at)
VALUES
    (1, 1, 1, 1, '2026-11-10 10:00:00+05:30', '2026-11-10 11:00:00+05:30', 'COMPLETED', '2026-11-09 09:15:00+05:30'),
    (2, 2, 2, 3, '2026-11-11 15:00:00+05:30', '2026-11-11 16:00:00+05:30', 'COMPLETED', '2026-11-10 10:20:00+05:30'),
    (3, 1, 1, 1, '2026-11-13 10:00:00+05:30', '2026-11-13 11:00:00+05:30', 'CONFIRMED', '2026-11-12 09:15:00+05:30'),
    (4, 5, 3, 5, '2026-11-13 09:00:00+05:30', '2026-11-13 10:00:00+05:30', 'CONFIRMED', '2026-11-12 08:30:00+05:30'),
    (5, 2, 2, 2, '2026-11-13 12:00:00+05:30', '2026-11-13 13:00:00+05:30', 'PENDING', '2026-11-12 10:00:00+05:30'),
    (6, 1, 1, 2, '2026-11-12 09:00:00+05:30', '2026-11-12 10:00:00+05:30', 'CANCELLED', '2026-11-11 10:00:00+05:30'),
    (7, 5, 3, 5, '2026-11-11 18:00:00+05:30', '2026-11-11 19:00:00+05:30', 'NO_SHOW', '2026-11-10 10:00:00+05:30');

-- 10. CHARGING_SESSIONS
-- Two completed sessions and one active walk-in session (reservation_id is NULL).
INSERT INTO charging_sessions
    (session_id, reservation_id, user_id, vehicle_id, charger_id, tariff_id,
     started_at, ended_at, meter_start_kwh, meter_end_kwh, status)
VALUES
    (1, 1, 1, 1, 1, 1, '2026-11-10 10:03:00+05:30', '2026-11-10 10:58:00+05:30', 1200.000, 1214.750, 'COMPLETED'),
    (2, 2, 2, 2, 3, 3, '2026-11-11 15:04:00+05:30', '2026-11-11 15:57:00+05:30', 500.000, 525.500, 'COMPLETED'),
    (3, NULL, 5, 3, 5, 4, CURRENT_TIMESTAMP - INTERVAL '30 minutes', NULL, 780.000, NULL, 'ACTIVE');

-- 11. INVOICES (one invoice per completed session)
INSERT INTO invoices
    (invoice_id, session_id, energy_kwh, price_per_kwh, session_fee,
     tax_rate_percent, energy_charge, tax_amount, total_amount, status, issued_at)
VALUES
    (1, 1, 14.750, 12.50, 10.00, 5.00, 184.38, 9.72, 204.10, 'PAID', '2026-11-10 11:00:00+05:30'),
    (2, 2, 25.500, 14.00, 15.00, 5.00, 357.00, 18.60, 390.60, 'PAID', '2026-11-11 16:00:00+05:30');

-- 12. PAYMENTS (invoice 2 demonstrates failed then successful attempts)
INSERT INTO payments
    (payment_id, invoice_id, amount, payment_method, transaction_reference, status, created_at, paid_at)
VALUES
    (1, 1, 204.10, 'UPI', 'DEMO-TXN-1101', 'SUCCESS', '2026-11-10 11:01:00+05:30', '2026-11-10 11:01:20+05:30'),
    (2, 2, 390.60, 'CARD', 'DEMO-TXN-1102-FAIL', 'FAILED', '2026-11-11 16:01:00+05:30', NULL),
    (3, 2, 390.60, 'UPI', 'DEMO-TXN-1103', 'SUCCESS', '2026-11-11 16:03:00+05:30', '2026-11-11 16:03:15+05:30');

-- 13. MAINTENANCE_RECORDS
INSERT INTO maintenance_records
    (maintenance_id, charger_id, reported_by, assigned_to, issue_description,
     priority, status, reported_at, scheduled_at, resolved_at, maintenance_cost)
VALUES
    (1, 4, 1, 3, 'Charging cable connector overheating; charger temporarily unavailable.',
     'HIGH', 'IN_PROGRESS', '2026-11-12 08:15:00+05:30', '2026-11-13 09:00:00+05:30', NULL, 0.00),
    (2, 2, 2, 3, 'Display panel was not responding; firmware reset completed.',
     'MEDIUM', 'RESOLVED', '2026-11-05 10:00:00+05:30', '2026-11-05 14:00:00+05:30', '2026-11-05 15:30:00+05:30', 750.00);

-- 14. CHARGER_STATUS_HISTORY
INSERT INTO charger_status_history
    (history_id, charger_id, previous_status, new_status, changed_by, reason, changed_at)
VALUES
    (1, 1, NULL, 'ONLINE', 3, 'Charger commissioned and made available.', '2026-10-20 09:00:00+05:30'),
    (2, 2, 'MAINTENANCE', 'ONLINE', 3, 'Display panel issue resolved.', '2026-11-05 15:35:00+05:30'),
    (3, 4, 'ONLINE', 'MAINTENANCE', 3, 'Overheating reported; charger taken out of service.', '2026-11-12 08:20:00+05:30'),
    (4, 5, NULL, 'ONLINE', 3, 'Charger commissioned and made available.', '2026-10-25 10:00:00+05:30');

-- Advance identity sequences because this demo uses explicit IDs.
SELECT setval(pg_get_serial_sequence('users', 'user_id'), (SELECT MAX(user_id) FROM users), TRUE);
SELECT setval(pg_get_serial_sequence('connector_types', 'connector_type_id'), (SELECT MAX(connector_type_id) FROM connector_types), TRUE);
SELECT setval(pg_get_serial_sequence('vehicles', 'vehicle_id'), (SELECT MAX(vehicle_id) FROM vehicles), TRUE);
SELECT setval(pg_get_serial_sequence('stations', 'station_id'), (SELECT MAX(station_id) FROM stations), TRUE);
SELECT setval(pg_get_serial_sequence('chargers', 'charger_id'), (SELECT MAX(charger_id) FROM chargers), TRUE);
SELECT setval(pg_get_serial_sequence('tariffs', 'tariff_id'), (SELECT MAX(tariff_id) FROM tariffs), TRUE);
SELECT setval(pg_get_serial_sequence('pricing_rules', 'rule_id'), (SELECT MAX(rule_id) FROM pricing_rules), TRUE);
SELECT setval(pg_get_serial_sequence('reservations', 'reservation_id'), (SELECT MAX(reservation_id) FROM reservations), TRUE);
SELECT setval(pg_get_serial_sequence('charging_sessions', 'session_id'), (SELECT MAX(session_id) FROM charging_sessions), TRUE);
SELECT setval(pg_get_serial_sequence('invoices', 'invoice_id'), (SELECT MAX(invoice_id) FROM invoices), TRUE);
SELECT setval(pg_get_serial_sequence('payments', 'payment_id'), (SELECT MAX(payment_id) FROM payments), TRUE);
SELECT setval(pg_get_serial_sequence('maintenance_records', 'maintenance_id'), (SELECT MAX(maintenance_id) FROM maintenance_records), TRUE);
SELECT setval(pg_get_serial_sequence('charger_status_history', 'history_id'), (SELECT MAX(history_id) FROM charger_status_history), TRUE);

COMMIT;

-- Verify how many rows were inserted into each table.
SELECT 'users' AS table_name, COUNT(*) AS rows_loaded FROM users
UNION ALL SELECT 'connector_types', COUNT(*) FROM connector_types
UNION ALL SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL SELECT 'vehicle_connector_types', COUNT(*) FROM vehicle_connector_types
UNION ALL SELECT 'stations', COUNT(*) FROM stations
UNION ALL SELECT 'chargers', COUNT(*) FROM chargers
UNION ALL SELECT 'tariffs', COUNT(*) FROM tariffs
UNION ALL SELECT 'pricing_rules', COUNT(*) FROM pricing_rules
UNION ALL SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL SELECT 'charging_sessions', COUNT(*) FROM charging_sessions
UNION ALL SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'maintenance_records', COUNT(*) FROM maintenance_records
UNION ALL SELECT 'charger_status_history', COUNT(*) FROM charger_status_history
ORDER BY table_name;
