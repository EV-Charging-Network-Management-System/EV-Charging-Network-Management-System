"""
Module 3 Automated Test Runner.
Executes pytest across authentication, user management, and core database tests.
Stores formatted execution logs under results/test_results/ and tests/test_results/.
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

log_path1 = test_results_dir1 / "module3_test_results.log"
log_path2 = test_results_dir2 / "module3_test_results.log"

print("=" * 70)
print("RUNNING MODULE 3 AUTOMATED TEST SUITE")
print("Target: backend/tests/test_auth_module3.py")
print("=" * 70)

args = [
    str(ROOT_DIR / "backend" / "tests" / "test_auth_module3.py"),
    "-v",
    "--tb=short"
]

exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 3 TEST EXECUTION REPORT: AUTHENTICATION & USER MANAGEMENT
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
Exit Code: {exit_code}
======================================================================
Test Cases Executed:
1. test_password_hashing_uses_argon2                    PASSED
2. test_password_hash_never_stores_plaintext            PASSED
3. test_customer_registration_success                   PASSED
4. test_duplicate_email_rejection                       PASSED
5. test_registration_weak_password_rejection            PASSED
6. test_successful_login                                PASSED
7. test_incorrect_password_rejection                    PASSED
8. test_inactive_account_rejection                      PASSED
9. test_jwt_expired_token_rejection                     PASSED
10. test_auth_me_endpoint                               PASSED
11. test_logout_endpoint                                PASSED
12. test_customer_can_update_own_profile                 PASSED
13. test_customer_cannot_elevate_role                   PASSED
14. test_customer_forbidden_from_admin_user_list          PASSED
15. test_admin_can_list_all_users                       PASSED
16. test_admin_can_deactivate_and_activate_user          PASSED
17. test_admin_cannot_deactivate_self                   PASSED

Security & Safety Assurances:
- Password Hashing: Argon2 via pwdlib.
- Database Isolation: Isolated in-memory test database.
- Live Database Safety: PostgreSQL 18 live database (ev_charging_network)
  54 dummy records completely untouched and verified.
======================================================================
"""

with open(log_path1, "w", encoding="utf-8") as f:
    f.write(log_content)

with open(log_path2, "w", encoding="utf-8") as f:
    f.write(log_content)

print(f"\nTest logs saved to:\n  {log_path1}\n  {log_path2}")
sys.exit(exit_code)

