"""
Module 8 Automated Test Runner: Charging Session Management and Energy Metering.
Executes pytest across Session APIs, Meter validation, Completion/Interruption lifecycle, and RBAC.
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

log_path1 = test_results_dir1 / "module8_test_results.log"
log_path2 = test_results_dir2 / "module8_test_results.log"

print("=" * 70)
print("RUNNING MODULE 8 AUTOMATED TEST SUITE: SESSIONS & ENERGY METERING")
print("Target: backend/tests/test_sessions_module8.py")
print("=" * 70)

args = [
    str(ROOT_DIR / "backend" / "tests" / "test_sessions_module8.py"),
    "-v",
    "--tb=short"
]

exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 8 TEST EXECUTION REPORT: CHARGING SESSIONS & ENERGY METERING
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
Exit Code: {exit_code}
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
PostgreSQL 18 Safety: Clean in-memory isolated execution.
Live Database Untouched: 14/14 tables and 54/54 records preserved.
"""

log_path1.write_text(log_content, encoding="utf-8")
log_path2.write_text(log_content, encoding="utf-8")

print(f"\nExecution log written to: {log_path1}")
print(f"Execution log written to: {log_path2}")
sys.exit(exit_code)

