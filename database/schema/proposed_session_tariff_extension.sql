-- ============================================================================
-- PROPOSED DATABASE MIGRATION SCRIPT (NON-DESTRUCTIVE EXTENSION PROPOSAL)
-- EV Charging Network Management System
-- Module 6: Historical Price Integrity Extension
--
-- IMPORTANT SAFETY NOTICE:
-- DO NOT EXECUTE THIS SCRIPT ON THE ACTIVE POSTGRESQL 18 PRODUCTION DATABASE.
-- This script serves as an architectural blueprint and formal change proposal
-- for future database releases to preserve historical price auditability.
-- ============================================================================

/*
ARCHITECTURAL RATIONALE:
1. EXISTING INVOICE INTEGRITY:
   In the current PostgreSQL 18 schema, the `invoices` table already stores:
     - energy_kwh NUMERIC(12, 3)
     - price_per_kwh NUMERIC(10, 2)
     - session_fee NUMERIC(10, 2)
     - tax_rate_percent NUMERIC(5, 2)
     - energy_charge NUMERIC(12, 2)
     - tax_amount NUMERIC(12, 2)
     - total_amount NUMERIC(12, 2)
   This ensures that once an invoice is issued, financial figures are completely
   locked and immune to any subsequent tariff modifications.

2. PRE-INVOICING SESSION PRICING GAP:
   The `charging_sessions` table currently contains:
     - session_id, reservation_id, user_id, vehicle_id, charger_id, tariff_id,
       started_at, ended_at, meter_start_kwh, meter_end_kwh, status
   However, between the moment a user begins charging (or accepts a pricing quote)
   and when the final invoice is generated, the underlying tariff rate or
   dynamic pricing rules (e.g., peak hour multiplier transition) could change.
   
3. PROPOSED SOLUTION:
   Add explicit snapshot columns to `charging_sessions` that record the locked
   financial conditions at the precise instant the charging session commenced:
     - applied_rate_per_kwh: Effective rate (base_price * multiplier)
     - applied_rule_id: Reference to the dynamic rule in effect
     - locked_session_fee: Session fee at start time
     - locked_tax_rate_percent: Applicable tax rate at start time
*/

-- Step 1: Add pricing snapshot columns to charging_sessions
ALTER TABLE charging_sessions
    ADD COLUMN IF NOT EXISTS applied_rate_per_kwh NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS applied_rule_id BIGINT REFERENCES pricing_rules(rule_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS locked_session_fee NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS locked_tax_rate_percent NUMERIC(5, 2) DEFAULT 0.00;

-- Step 2: Add validation constraints ensuring non-negative values
ALTER TABLE charging_sessions
    ADD CONSTRAINT chk_sessions_applied_rate CHECK (applied_rate_per_kwh IS NULL OR applied_rate_per_kwh >= 0),
    ADD CONSTRAINT chk_sessions_locked_fee CHECK (locked_session_fee >= 0),
    ADD CONSTRAINT chk_sessions_locked_tax CHECK (locked_tax_rate_percent BETWEEN 0 AND 100);

-- Step 3: Create index for audit reporting and financial reconciliation
CREATE INDEX IF NOT EXISTS idx_charging_sessions_applied_rule
    ON charging_sessions (applied_rule_id);

COMMENT ON COLUMN charging_sessions.applied_rate_per_kwh IS 
    'Snapshot of the effective kWh rate (base tariff * dynamic multiplier) locked when charging initiated.';

COMMENT ON COLUMN charging_sessions.applied_rule_id IS 
    'Reference to the specific dynamic pricing rule active at session initiation, or NULL if standard base rate.';

COMMENT ON COLUMN charging_sessions.locked_session_fee IS 
    'Snapshot of the tariff session fee locked when charging initiated.';

COMMENT ON COLUMN charging_sessions.locked_tax_rate_percent IS 
    'Snapshot of the tax rate percentage locked when charging initiated.';

-- ============================================================================
-- ROLLBACK SCRIPT (FOR REFERENCE ONLY)
-- ============================================================================
/*
ALTER TABLE charging_sessions
    DROP CONSTRAINT IF EXISTS chk_sessions_applied_rate,
    DROP CONSTRAINT IF EXISTS chk_sessions_locked_fee,
    DROP CONSTRAINT IF EXISTS chk_sessions_locked_tax;

DROP INDEX IF EXISTS idx_charging_sessions_applied_rule;

ALTER TABLE charging_sessions
    DROP COLUMN IF EXISTS applied_rate_per_kwh,
    DROP COLUMN IF EXISTS applied_rule_id,
    DROP COLUMN IF EXISTS locked_session_fee,
    DROP COLUMN IF EXISTS locked_tax_rate_percent;
*/

