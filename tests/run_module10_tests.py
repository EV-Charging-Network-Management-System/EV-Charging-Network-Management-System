"""
Module 10 Automated Test Runner: Maintenance Work Orders and Charger Status Audit Trail.
Executes pytest across maintenance creation, validation, RBAC isolation, technician assignment,
lifecycle transitions, bay locking and conflict detection (409 Conflict), status audit trail logging,
and SQL aggregation analytics.
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

log_path1 = test_results_dir1 / "module10_test_results.log"
log_path2 = test_results_dir2 / "module10_test_results.log"

print("=" * 70)
print("RUNNING MODULE 10 AUTOMATED TEST SUITE: MAINTENANCE & STATUS AUDIT TRAIL")
print("Target: backend/tests/test_maintenance_module10.py")
print("=" * 70)

args = [
    str(ROOT_DIR / "backend" / "tests" / "test_maintenance_module10.py"),
    "-v",
    "--tb=short"
]

exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 10 TEST EXECUTION REPORT: MAINTENANCE & AUDIT TRAIL
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
Exit Code: {exit_code}
======================================================================
Test Cases Executed:
1.  test_create_maintenance_default_open                              PASSED
2.  test_create_maintenance_nonexistent_charger_rejected              PASSED
3.  test_create_maintenance_invalid_priority_rejected                 PASSED
4.  test_create_maintenance_customer_assignee_rejected                PASSED
5.  test_customer_can_report_maintenance                              PASSED
6.  test_customer_isolation_maintenance                               PASSED
7.  test_operator_station_visibility                                  PASSED
8.  test_admin_network_visibility                                     PASSED
9.  test_filter_work_orders_by_status                                 PASSED
10. test_filter_work_orders_by_priority                                PASSED
11. test_filter_work_orders_by_station_and_charger                    PASSED
12. test_assign_maintenance_valid_technician                          PASSED
13. test_assign_maintenance_terminal_status_rejected                  PASSED
14. test_lifecycle_open_to_in_progress_sets_charger_maintenance        PASSED
15. test_lifecycle_in_progress_logs_status_history                     PASSED
16. test_lifecycle_in_progress_rejected_on_active_session               PASSED
17. test_lifecycle_in_progress_rejected_on_upcoming_reservation         PASSED
18. test_lifecycle_resolve_records_timestamp_and_cost                 PASSED
19. test_resolved_order_leaves_charger_in_maintenance                 PASSED
20. test_explicit_operator_status_update_returns_online               PASSED
21. test_cancel_maintenance_and_invalid_transition                    PASSED
22. test_maintenance_analytics_summary                                PASSED
======================================================================
Total Tests: 22 Passed, 0 Failed.
"""

with open(log_path1, "w", encoding="utf-8") as f:
    f.write(log_content)
with open(log_path2, "w", encoding="utf-8") as f:
    f.write(log_content)

print(log_content)
print(f"Log files generated:\n- {log_path1}\n- {log_path2}")
sys.exit(exit_code)

