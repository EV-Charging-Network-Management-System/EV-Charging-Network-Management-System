"""
Automated Test Suite: Database Schema & Dummy Data Verification
Enforces the safety rule: NEVER modify or recreate database tables or dummy data.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from database.inspector.db_inspector import (
    inspect_database,
    EXPECTED_14_TABLES,
    EXPECTED_DUMMY_ROW_COUNTS,
    EXPECTED_TOTAL_ROWS
)


def test_database_verification():
    """Verify that all 14 tables and 54 dummy records exist in PostgreSQL."""
    report = inspect_database()

    # 1. Assert read-only session
    assert report["transaction_read_only"] == "on", "Session must be READ ONLY."

    # 2. Assert 14 tables
    found = report["found_tables"]
    missing = [t for t in EXPECTED_14_TABLES if t not in found]
    assert len(missing) == 0, f"Missing tables: {missing}"
    assert len(found) == 14, f"Expected 14 tables, found {len(found)}: {found}"

    # 3. Assert row counts per table
    for table, expected_cnt in EXPECTED_DUMMY_ROW_COUNTS.items():
        actual_cnt = report["tables"][table]["row_count"]
        assert actual_cnt == expected_cnt, (
            f"Table '{table}' count mismatch: expected {expected_cnt}, found {actual_cnt}"
        )

    # 4. Assert total records
    total_found = report["summary"]["total_records_found"]
    assert total_found == EXPECTED_TOTAL_ROWS, (
        f"Total records mismatch: expected {EXPECTED_TOTAL_ROWS}, found {total_found}"
    )

    print(f"PASS: All {len(found)} tables and all {total_found} dummy records verified!")


if __name__ == "__main__":
    results_dir = root_dir / "tests" / "test_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "database_verification.log"

    try:
        test_database_verification()
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("TEST: test_database_verification\nSTATUS: PASSED\n")
            f.write("DETAILS: 14/14 tables verified, 54/54 dummy rows verified, READ-ONLY enforced.\n")
        print(f"Test log written to {log_file}")
    except Exception as e:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"TEST: test_database_verification\nSTATUS: FAILED\nERROR: {e}\n")
        print(f"FAIL: {e}")
        sys.exit(1)

