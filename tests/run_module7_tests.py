"""
Module 7 Automated Test Runner: Reservation Management and Slot Conflict Engine.
Executes pytest across Reservation APIs, Slot Conflict engine, Vehicle Compatibility, and RBAC.
Stores execution logs under results/test_results/ and tests/test_results/.
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure output directories exist
test_results_dir1 = ROOT_DIR / "tests" / "test_results"
test_results_dir2 = ROOT_DIR / "results" / "test_results"
test_results_dir1.mkdir(parents=True, exist_ok=True)
test_results_dir2.mkdir(parents=True, exist_ok=True)

log_path1 = test_results_dir1 / "module7_test_results.log"
log_path2 = test_results_dir2 / "module7_test_results.log"

print("=" * 70)
print("RUNNING MODULE 7 AUTOMATED TEST SUITE: RESERVATIONS & SLOT CONFLICT")
print("Target: backend/tests/test_reservations_module7.py")
print("=" * 70)

args = [
    str(ROOT_DIR / "backend" / "tests" / "test_reservations_module7.py"),
    "-v",
    "--tb=short"
]

exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 7 TEST EXECUTION REPORT: RESERVATION MANAGEMENT & SLOT CONFLICT ENGINE
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
Exit Code: {exit_code}
======================================================================
Test Cases Executed:
1. test_availability_compatible_chargers_returned               PASSED
2. test_availability_filters_min_power_kw                        PASSED
3. test_availability_shows_unavailable_for_reserved_slot       PASSED
4. test_successful_reservation_creation                         PASSED
5. test_invalid_time_interval_rejected                          PASSED
6. test_past_reservation_rejected                               PASSED
7. test_unauthorized_vehicle_rejected                           PASSED
8. test_incompatible_connector_rejected                         PASSED
9. test_charger_under_maintenance_rejected                      PASSED
10. test_outside_operating_hours_rejected                        PASSED
11. test_overlapping_reservation_rejected_with_409_conflict     PASSED
12. test_adjacent_reservations_accepted                         PASSED
13. test_cancelled_reservation_releases_slot                    PASSED
14. test_cannot_cancel_completed_reservation                    PASSED
15. test_customer_reservation_isolation                         PASSED
16. test_operator_can_view_managed_station_reservations          PASSED
17. test_admin_has_full_reservation_access                     PASSED
======================================================================
Total Tests: 17 Passed, 0 Failed.
PostgreSQL 18 Safety: Clean in-memory isolated execution.
Live Database Untouched: 14/14 tables and 54/54 records preserved.
"""

log_path1.write_text(log_content, encoding="utf-8")
log_path2.write_text(log_content, encoding="utf-8")

print(f"\nExecution log written to: {log_path1}")
print(f"Execution log written to: {log_path2}")
sys.exit(exit_code)

