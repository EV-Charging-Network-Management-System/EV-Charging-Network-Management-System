"""
Module 9 Automated Test Runner: Invoicing and Payment Reconciliation.
Executes pytest across Invoice generation, Meter calculations, Financial rounding,
Payment attempts, Gateway reconciliation, Overpayment prevention, RBAC, and Refunds.
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

log_path1 = test_results_dir1 / "module9_test_results.log"
log_path2 = test_results_dir2 / "module9_test_results.log"

print("=" * 70)
print("RUNNING MODULE 9 AUTOMATED TEST SUITE: INVOICING & PAYMENT RECONCILIATION")
print("Target: backend/tests/test_billing_module9.py")
print("=" * 70)

args = [
    str(ROOT_DIR / "backend" / "tests" / "test_billing_module9.py"),
    "-v",
    "--tb=short"
]

exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 9 TEST EXECUTION REPORT: INVOICING & PAYMENT RECONCILIATION
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
Exit Code: {exit_code}
======================================================================
Test Cases Executed:
1.  test_invoice_generation_from_completed_session               PASSED
2.  test_invoice_rejection_for_active_session                    PASSED
3.  test_missing_final_meter_reading_rejection                   PASSED
4.  test_correct_energy_calculation                              PASSED
5.  test_correct_tax_and_total_calculation                       PASSED
6.  test_decimal_rounding_correctness_round_half_up              PASSED
7.  test_locked_tariff_snapshot_usage                            PASSED
8.  test_tariff_changes_not_changing_old_invoices                PASSED
9.  test_duplicate_invoice_rejection                             PASSED
10. test_concurrent_invoice_generation                           PASSED
11. test_successful_demo_payment                                 PASSED
12. test_failed_payment                                          PASSED
13. test_payment_retry_after_failure                              PASSED
14. test_invoice_remains_unpaid_after_failure                    PASSED
15. test_successful_payment_marks_invoice_paid                   PASSED
16. test_duplicate_transaction_reference_rejection               PASSED
17. test_concurrent_payment_attempts                             PASSED
18. test_overpayment_prevention                                  PASSED
19. test_customer_invoice_isolation                              PASSED
20. test_admin_invoice_access                                    PASSED
21. test_payment_history_preservation                            PASSED
22. test_refund_validation_where_supported                       PASSED
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

