-- ============================================================================
-- REVISED DATABASE MIGRATION SCRIPT (CHARGING SESSIONS PRICING INTEGRATION)
-- EV Charging Network Management System
-- Module 8: Session Tariff Snapshotting & Interruption Audit Trail
--
-- IMPORTANT SAFETY NOTICE:
-- DO NOT EXECUTE THIS SCRIPT ON THE ACTIVE POSTGRESQL 18 PRODUCTION DATABASE.
-- This script serves as a formal architectural blueprint and proposed schema
-- enhancement for future releases to ensure end-to-end financial immutability.
-- ============================================================================

/*
==============================================================================
ARCHITECTURAL RATIONALE & JUSTIFICATION:
==============================================================================
1. THE PRE-INVOICING AUDIT GAP:
   In the existing PostgreSQL 18 schema:
   - `invoices` stores finalized billing figures (energy_charge, tax_amount, total_amount).
   - However, `charging_sessions` only links to `tariff_id` via foreign key.
   - Tariffs are dynamic: base rates, session fees, and active pricing rules
     (peak hours, off-peak night discounts, high demand surge) fluctuate over time.
   - If a charging session starts at 10:30 PM under an off-peak discount (0.8x)
     and ends at 11:30 PM, or if the station operator modifies the tariff schedule
     before the invoice is generated, re-evaluating the session's pricing from
     the `tariffs` table leads to financial drift and customer billing disputes.

2. WHY THESE EXTENSIONS ARE REQUIRED:
   - `applied_rate_per_kwh`: Snapshot of the effective rate (base_price * multiplier)
     locked at the exact moment charging begins.
   - `applied_multiplier`: Snapshot of the dynamic multiplier (e.g. 1.25x peak, 0.80x off-peak).
   - `applied_rule_id`: Foreign key reference to the specific pricing rule triggered.
   - `locked_session_fee`: Fixed session connection fee locked from the active tariff.
   - `locked_tax_rate_percent`: Applicable GST / sales tax rate locked at start.
   - `interruption_reason`: Captures the telemetry, fault, or user reason when a session
     transitions to 'INTERRUPTED' (e.g., "Emergency stop button pressed", "Vehicle decoupled").

3. SAFETY & ROLLBACK GUARANTEES:
   - Uses `ADD COLUMN IF NOT EXISTS` so it can be re-run safely.
   - Backward compatible: Existing sessions will have NULL snapshot columns without breaking
     historical reports.
   - No table recreations, no truncation, and zero data loss.
==============================================================================
*/

BEGIN;

-- Step 1: Add pricing snapshot and interruption audit columns to charging_sessions
ALTER TABLE charging_sessions
    ADD COLUMN IF NOT EXISTS applied_rate_per_kwh    NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS applied_multiplier      NUMERIC(5, 2) DEFAULT 1.00,
    ADD COLUMN IF NOT EXISTS applied_rule_id         BIGINT REFERENCES pricing_rules(rule_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS locked_session_fee      NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS locked_tax_rate_percent NUMERIC(5, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS interruption_reason     TEXT;

-- Step 2: Add validation check constraints ensuring domain validity
ALTER TABLE charging_sessions
    ADD CONSTRAINT chk_sessions_applied_rate
        CHECK (applied_rate_per_kwh IS NULL OR applied_rate_per_kwh >= 0),
    ADD CONSTRAINT chk_sessions_applied_multiplier
        CHECK (applied_multiplier IS NULL OR applied_multiplier > 0),
    ADD CONSTRAINT chk_sessions_locked_fee
        CHECK (locked_session_fee IS NULL OR locked_session_fee >= 0),
    ADD CONSTRAINT chk_sessions_locked_tax
        CHECK (locked_tax_rate_percent IS NULL OR (locked_tax_rate_percent BETWEEN 0 AND 100));

-- Step 3: Create index for pricing rule aggregation and revenue reconciliation
CREATE INDEX IF NOT EXISTS idx_charging_sessions_applied_rule
    ON charging_sessions (applied_rule_id);

CREATE INDEX IF NOT EXISTS idx_charging_sessions_status_started
    ON charging_sessions (status, started_at DESC);

-- Step 4: Documentation comments
COMMENT ON COLUMN charging_sessions.applied_rate_per_kwh IS
    'Effective per-kWh rate (base_price * multiplier) locked at session start time.';
COMMENT ON COLUMN charging_sessions.applied_multiplier IS
    'Pricing rule multiplier applied (e.g., 1.25 for peak, 0.80 for off-peak).';
COMMENT ON COLUMN charging_sessions.applied_rule_id IS
    'Pricing rule ID active when this session started.';
COMMENT ON COLUMN charging_sessions.locked_session_fee IS
    'Session connection fee locked from active tariff at start time.';
COMMENT ON COLUMN charging_sessions.locked_tax_rate_percent IS
    'Tax percentage locked from active tariff at start time.';
COMMENT ON COLUMN charging_sessions.interruption_reason IS
    'Telemetry fault code, user reason, or disconnection event for interrupted sessions.';

COMMIT;

