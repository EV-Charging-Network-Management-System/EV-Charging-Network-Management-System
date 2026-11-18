-- ============================================================================
-- PROPOSED DATABASE MIGRATION SCRIPT (POSTGRESQL EXCLUSION CONSTRAINT)
-- EV Charging Network Management System
-- Module 7: Slot Double-Booking Prevention Engine
--
-- IMPORTANT SAFETY NOTICE:
-- DO NOT SILENTLY EXECUTE THIS SCRIPT ON THE ACTIVE POSTGRESQL 18 PRODUCTION DATABASE.
-- This script serves as a verified architectural blueprint and production migration
-- proposal to enforce mathematical slot exclusivity at the database engine level.
-- ============================================================================

/*
==============================================================================
ARCHITECTURAL & MATHEMATICAL ANALYSIS:
==============================================================================
1. VERIFIED COLUMN DATA TYPES IN POSTGRESQL 18:
   - reservations.start_at: TIMESTAMP WITH TIME ZONE (NOT NULL)
   - reservations.end_at:   TIMESTAMP WITH TIME ZONE (NOT NULL)
   - reservations.charger_id: BIGINT (NOT NULL, FK to chargers)
   - reservations.status:   VARCHAR(20) (NOT NULL)
   
   Because start_at and end_at are TIMESTAMP WITH TIME ZONE, the PostgreSQL
   range constructor to use is `tstzrange(start_at, end_at, '[)')`.
   The half-open boundary `[)` denotes [start_at <= t < end_at).

2. ADJACENT BOOKINGS BEHAVIOR:
   Under half-open interval semantics:
     Booking A: [2026-11-13 10:00:00+05:30, 2026-11-13 11:00:00+05:30)
     Booking B: [2026-11-13 11:00:00+05:30, 2026-11-13 12:00:00+05:30)
   The intersection A && B is EMPTY (no overlap).
   Therefore, adjacent bookings are ALLOWED by this constraint.

3. OVERLAPPING BOOKINGS BEHAVIOR:
   Under half-open interval semantics:
     Booking A: [2026-11-13 10:00:00+05:30, 2026-11-13 11:00:00+05:30)
     Booking C: [2026-11-13 10:30:00+05:30, 2026-11-13 11:30:00+05:30)
   The intersection A && C is [10:30, 11:00) != EMPTY (overlap detected).
   PostgreSQL raises an exclusion violation error with SQLSTATE 23P01.

4. PARTIAL INDEX FILTER (STATUS EXCLUSION):
   `WHERE (status IN ('PENDING', 'CONFIRMED'))`
   This partial index ensures that:
     - Completed bookings ('COMPLETED')
     - Cancelled bookings ('CANCELLED')
     - No-show bookings ('NO_SHOW')
   do NOT hold reservations on the time slot, releasing the slot for new drivers.

5. PRECONDITIONS:
   - Superuser or database owner privilege to enable extension.
   - `btree_gist` extension must be installed to support equality (=) on BIGINT
     alongside range overlaps (&&) in a GiST index.
   - Zero existing overlapping rows with status 'PENDING' or 'CONFIRMED'.
     (Verified: all 7 existing seed records in PostgreSQL 18 are 100% disjoint).
==============================================================================
*/

-- Step 1: Enable the btree_gist extension (Required for combining bigint and tstzrange in GiST)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Step 2: Add partial exclusion constraint to prevent overlapping active bookings on the same charger
ALTER TABLE reservations
    ADD CONSTRAINT exclude_overlapping_reservations
    EXCLUDE USING gist (
        charger_id WITH =,
        tstzrange(start_at, end_at, '[)') WITH &&
    )
    WHERE (status IN ('PENDING', 'CONFIRMED'));

-- Step 3: Add descriptive comments documenting the constraint
COMMENT ON CONSTRAINT exclude_overlapping_reservations ON reservations IS
    'Enforces mathematical slot exclusivity: prevents concurrent PENDING or CONFIRMED reservations on the same charger while allowing back-to-back adjacent bookings.';

-- ============================================================================
-- APPLICATION ERROR HANDLING SPECIFICATION:
-- ============================================================================
-- When a concurrent race condition or overlapping booking attempts to insert,
-- PostgreSQL triggers error code 23P01 (exclusion_violation).
-- The FastAPI backend catches SQLSTATE 23P01 (or IntegrityError) and translates
-- it to HTTP 409 Conflict with the message:
-- "This charging slot has already been reserved. Please choose another time."
-- ============================================================================

-- ============================================================================
-- ROLLBACK SCRIPT (FOR REFERENCE ONLY)
-- ============================================================================
/*
ALTER TABLE reservations
    DROP CONSTRAINT IF EXISTS exclude_overlapping_reservations;

-- Note: btree_gist extension is left intact if used by other modules.
-- DROP EXTENSION IF EXISTS btree_gist;
*/

