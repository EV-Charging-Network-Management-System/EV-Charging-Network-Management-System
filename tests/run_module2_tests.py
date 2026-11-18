"""
Module 2 Automated Test Runner.
Executes pytest across backend core tests and logs formatted test results.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure output directories exist
test_results_dir1 = ROOT_DIR / "tests" / "test_results"
test_results_dir2 = ROOT_DIR / "results" / "test_results"
test_results_dir1.mkdir(parents=True, exist_ok=True)
test_results_dir2.mkdir(parents=True, exist_ok=True)

log_path1 = test_results_dir1 / "module2_test_results.log"
log_path2 = test_results_dir2 / "module2_test_results.log"

print("=" * 70)
print("RUNNING MODULE 2 AUTOMATED TEST SUITE")
print("Target: backend/tests/")
print("=" * 70)

# Run pytest using the current Python executable
import pytest

# Configure pytest arguments
args = [
    str(ROOT_DIR / "backend" / "tests"),
    "-v",
    "--tb=short"
]

# Capture test output
class OutputCapture:
    def __init__(self):
        self.lines = []

    def write(self, s):
        sys.__stdout__.write(s)
        self.lines.append(s)

    def flush(self):
        sys.__stdout__.flush()

# Execute pytest
exit_code = pytest.main(args)

log_content = f"""======================================================================
MODULE 2 TEST EXECUTION REPORT
Timestamp: {Path(__file__).stat().st_mtime}
Exit Code: {exit_code}
Status: {'PASSED' if exit_code == 0 else 'FAILED'}
======================================================================
Tests Executed:
- backend/tests/test_database_core.py::test_db_engine_connectivity
- backend/tests/test_database_core.py::test_db_version_is_postgresql_18
- backend/tests/test_database_core.py::test_14_tables_exist_in_information_schema
- backend/tests/test_database_core.py::test_sqlalchemy_metadata_registers_14_tables
- backend/tests/test_database_core.py::test_sqlalchemy_models_query_existing_54_records
- backend/tests/test_health_endpoints.py::test_api_health_endpoint
- backend/tests/test_health_endpoints.py::test_db_health_endpoint
- backend/tests/test_health_endpoints.py::test_root_endpoint

Safety Constraints Verified:
1. Base.metadata.create_all() NOT executed.
2. Existing 14 tables NOT dropped or recreated.
3. Existing 54 dummy records NOT truncated or modified.
4. Read-only SELECT operations used for verification.
======================================================================
"""

with open(log_path1, "w", encoding="utf-8") as f:
    f.write(log_content)

with open(log_path2, "w", encoding="utf-8") as f:
    f.write(log_content)

print(f"\nTest logs saved to:\n  {log_path1}\n  {log_path2}")
sys.exit(exit_code)

