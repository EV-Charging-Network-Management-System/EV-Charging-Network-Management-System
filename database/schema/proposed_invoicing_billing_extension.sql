-- ============================================================================
-- PROPOSED DATABASE MIGRATION SCRIPT: INVOICING & PAYMENT EXTENSIONS
-- EV Charging Network Management System
-- Module 9: Invoicing & Payment Reconciliation
--
-- IMPORTANT SAFETY NOTICE:
-- DO NOT EXECUTE THIS SCRIPT ON THE ACTIVE POSTGRESQL 18 PRODUCTION DATABASE.
-- Per database safety rules, this script serves as a formal architectural proposal
-- and future release migration blueprint. No schema changes will be applied
-- without explicit administrative authorization.
-- ============================================================================

/*
==============================================================================
ARCHITECTURAL RATIONALE & JUSTIFICATION:
==============================================================================
1. THE PRE-INVOICING AUDIT GAP:
   - In the live PostgreSQL 18 database, table `charging_sessions` holds:
     `session_id`, `reservation_id`, `user_id`, `vehicle_id`, `charger_id`,
     `tariff_id`, `started_at`, `ended_at`, `meter_start_kwh`, `meter_end_kwh`, `status`.
   - The pricing snapshot columns (`applied_rate_per_kwh`, `applied_multiplier`,
     `applied_rule_id`, `locked_session_fee`, `locked_tax_rate_percent`) do not
     physically exist in the live PostgreSQL `charging_sessions` table.
   - While `session.tariff_id` identifies the baseline tariff assigned at start,
     dynamic rules (peak-hour surges, off-peak night discounts, demand pricing)
     must be evaluated deterministically for the historical `started_at` timestamp.
   - Storing these snapshot columns directly on `charging_sessions` at session start
     locks the pricing agreement in place before the session even ends or invoices are generated.

2. PAYMENT RECONCILIATION & REFUND AUDIT:
   - In the live PostgreSQL 18 database, table `payments` holds:
     `payment_id`, `invoice_id`, `amount`, `payment_method`,
     `transaction_reference`, `status`, `created_at`, `paid_at`.
   - The check constraint `payments_status_check` permits:
     `'PENDING', 'SUCCESS', 'FAILED', 'REFUNDED'`.
   - However, when a payment transitions to 'REFUNDED', there are no dedicated
     columns to store:
     a) `refund_reference`: A distinct external bank/gateway reversal identifier.
     b) `refunded_at`: The exact UTC timestamp when the refund was processed.
     c) `refund_reason`: An operator/system audit description for the reversal.
   - Adding these columns enables complete financial reconciliation without
     mutating the original payment's `paid_at` or `transaction_reference`.

3. HISTORICAL DATA IMPLICATIONS & BACKWARD COMPATIBILITY:
   - All proposed columns are strictly nullable (`DEFAULT NULL`) or carry safe defaults.
   - Adding these columns via `ADD COLUMN IF NOT EXISTS` is 100% non-destructive:
     no existing tables are dropped, no rows are deleted or modified, and all
     54 original seed records remain fully valid.
   - Historical completed sessions that lack snapshot columns continue to be
     reconciled via their historical `tariff_id` and timestamp without error.
==============================================================================
*/

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. Charging Sessions: Add Pricing Snapshot & Interruption Audit Columns
-- ----------------------------------------------------------------------------
ALTER TABLE charging_sessions
    ADD COLUMN IF NOT EXISTS applied_rate_per_kwh    NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS applied_multiplier      NUMERIC(5, 3) DEFAULT 1.000,
    ADD COLUMN IF NOT EXISTS applied_rule_id         BIGINT REFERENCES pricing_rules(rule_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS locked_session_fee      NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS locked_tax_rate_percent NUMERIC(5, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS interruption_reason     TEXT;

-- ----------------------------------------------------------------------------
-- 2. Payments: Add Refund Audit Columns & Idempotency Key
-- ----------------------------------------------------------------------------
ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS refund_reference        VARCHAR(120) UNIQUE,
    ADD COLUMN IF NOT EXISTS refunded_at             TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS refund_reason           TEXT;

-- ----------------------------------------------------------------------------
-- 3. Constraints: Ensure Non-Negative Financial Values
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_sessions_applied_rate') THEN
        ALTER TABLE charging_sessions
            ADD CONSTRAINT chk_sessions_applied_rate
                CHECK (applied_rate_per_kwh IS NULL OR applied_rate_per_kwh >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_sessions_applied_multiplier') THEN
        ALTER TABLE charging_sessions
            ADD CONSTRAINT chk_sessions_applied_multiplier
                CHECK (applied_multiplier IS NULL OR applied_multiplier > 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_payments_refund_timing') THEN
        ALTER TABLE payments
            ADD CONSTRAINT chk_payments_refund_timing
                CHECK (refunded_at IS NULL OR refunded_at >= created_at);
    END IF;
END $$;

COMMIT;

