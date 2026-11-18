"""
EV Charging Network Management System
READ-ONLY PostgreSQL Database Inspection Tool

SAFETY GUARANTEES:
1. Enforces read-only connection (SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY).
2. Uses parameters from .env without hardcoding credentials or exposing passwords in logs.
3. Performs non-destructive queries only (SELECT metadata and COUNTs).
4. Outputs comprehensive structured JSON and Markdown audit reports.
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 is not installed in the active Python environment.")
    print("Please ensure psycopg2-binary is installed.")
    sys.exit(1)


EXPECTED_14_TABLES = [
    "users",
    "connector_types",
    "vehicles",
    "vehicle_connector_types",
    "stations",
    "chargers",
    "tariffs",
    "pricing_rules",
    "reservations",
    "charging_sessions",
    "invoices",
    "payments",
    "maintenance_records",
    "charger_status_history"
]

EXPECTED_DUMMY_ROW_COUNTS = {
    "users": 5,
    "connector_types": 4,
    "vehicles": 3,
    "vehicle_connector_types": 6,
    "stations": 3,
    "chargers": 5,
    "tariffs": 4,
    "pricing_rules": 3,
    "reservations": 7,
    "charging_sessions": 3,
    "invoices": 2,
    "payments": 3,
    "maintenance_records": 2,
    "charger_status_history": 4
}
EXPECTED_TOTAL_ROWS = sum(EXPECTED_DUMMY_ROW_COUNTS.values())  # 54


def load_env(env_path: Path) -> Dict[str, str]:
    """Parse .env file safely without external dependencies."""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip("'\"")
    return env_vars


def get_db_connection():
    """Establish a strictly READ-ONLY connection to PostgreSQL."""
    # Find .env in project root or current working dir
    root_dir = Path(__file__).resolve().parent.parent.parent
    env_file = root_dir / ".env"
    env_vars = load_env(env_file)

    host = env_vars.get("DB_HOST", os.environ.get("DB_HOST", "localhost"))
    port = int(env_vars.get("DB_PORT", os.environ.get("DB_PORT", "5432")))
    dbname = env_vars.get("DB_NAME", os.environ.get("DB_NAME", "ev_charging_network"))
    user = env_vars.get("DB_USER", os.environ.get("DB_USER", "postgres"))
    password = env_vars.get("DB_PASSWORD", os.environ.get("DB_PASSWORD", ""))
    sslmode = env_vars.get("DB_SSLMODE", os.environ.get("DB_SSLMODE", "prefer"))

    if not password:
        raise ValueError("Database password not found in .env or environment variables.")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
        connect_timeout=10
    )

    # STRICT SAFETY: Set session to READ ONLY at database server level
    conn.set_session(readonly=True, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
    
    return conn, {"host": host, "port": port, "dbname": dbname, "user": user}


def inspect_database() -> Dict[str, Any]:
    """Inspect the database schema, tables, rows, constraints, and indexes."""
    conn, conn_info = get_db_connection()
    report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connection": conn_info,
        "database_version": "",
        "tables": {},
        "summary": {},
        "verification": {}
    }

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Server version & read-only check
            cur.execute("SELECT version();")
            report["database_version"] = cur.fetchone()["version"]

            cur.execute("SHOW transaction_read_only;")
            report["transaction_read_only"] = cur.fetchone()["transaction_read_only"]

            # 1. Existing base tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            found_tables = [row["table_name"] for row in cur.fetchall()]
            report["found_tables"] = found_tables

            total_records = 0

            for table in found_tables:
                table_meta: Dict[str, Any] = {}

                # Row count
                cur.execute(sql.SQL("SELECT COUNT(*) AS cnt FROM {}").format(sql.Identifier(table)))
                row_cnt = cur.fetchone()["cnt"]
                table_meta["row_count"] = row_cnt
                total_records += row_cnt

                # Columns
                cur.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable, 
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                table_meta["columns"] = cur.fetchall()

                # Primary key
                cur.execute("""
                    SELECT c.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                      AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                    WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s;
                """, (table,))
                table_meta["primary_key"] = [r["column_name"] for r in cur.fetchall()]

                # Foreign keys
                cur.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
                """, (table,))
                table_meta["foreign_keys"] = cur.fetchall()

                # Indexes
                cur.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public' AND tablename = %s
                    ORDER BY indexname;
                """, (table,))
                table_meta["indexes"] = cur.fetchall()

                report["tables"][table] = table_meta

            # Summary metrics
            report["summary"] = {
                "total_tables_found": len(found_tables),
                "expected_tables_count": len(EXPECTED_14_TABLES),
                "total_records_found": total_records,
                "expected_records_count": EXPECTED_TOTAL_ROWS
            }

            # Verification assertions
            missing_tables = [t for t in EXPECTED_14_TABLES if t not in found_tables]
            unexpected_tables = [t for t in found_tables if t not in EXPECTED_14_TABLES]
            mismatched_counts = {}
            for t, exp_cnt in EXPECTED_DUMMY_ROW_COUNTS.items():
                act_cnt = report["tables"].get(t, {}).get("row_count", 0)
                if act_cnt != exp_cnt:
                    mismatched_counts[t] = {"expected": exp_cnt, "actual": act_cnt}

            report["verification"] = {
                "all_14_tables_present": len(missing_tables) == 0 and len(found_tables) == 14,
                "missing_tables": missing_tables,
                "unexpected_tables": unexpected_tables,
                "exact_54_dummy_records": total_records == EXPECTED_TOTAL_ROWS,
                "mismatched_row_counts": mismatched_counts,
                "status": "PASS" if (len(missing_tables) == 0 and len(found_tables) == 14 and total_records == EXPECTED_TOTAL_ROWS and not mismatched_counts) else "MISMATCH"
            }

    finally:
        conn.close()

    return report


def generate_markdown_report(report: Dict[str, Any]) -> str:
    """Format inspection report into readable Markdown."""
    lines = []
    lines.append("# EV Charging Network Database Verification Report")
    lines.append("")
    lines.append(f"- **Generated At:** {report['timestamp']}")
    lines.append(f"- **Database Host:** `{report['connection']['host']}:{report['connection']['port']}`")
    lines.append(f"- **Database Name:** `{report['connection']['dbname']}`")
    lines.append(f"- **Database User:** `{report['connection']['user']}` (Password hidden)")
    lines.append(f"- **Server Version:** {report['database_version']}")
    lines.append(f"- **Session Security:** `transaction_read_only = {report['transaction_read_only']}`")
    lines.append(f"- **Verification Status:** **`{report['verification']['status']}`**")
    lines.append("")
    lines.append("---")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Expected | Actual | Status |")
    lines.append(f"| :--- | :--- | :--- | :--- |")
    
    t_status = "PASS" if report['verification']['all_14_tables_present'] else "FAIL"
    lines.append(f"| Core Base Tables | {report['summary']['expected_tables_count']} | {report['summary']['total_tables_found']} | {t_status} |")
    
    r_status = "PASS" if report['verification']['exact_54_dummy_records'] else "FAIL"
    lines.append(f"| Total Records Loaded | {report['summary']['expected_records_count']} | {report['summary']['total_records_found']} | {r_status} |")
    lines.append("")

    lines.append("## 2. Table-by-Table Verification Matrix")
    lines.append("")
    lines.append("| # | Table Name | Columns | Primary Key | Foreign Keys | Row Count | Expected | Status |")
    lines.append("| :-: | :--- | :-: | :--- | :-: | :-: | :-: | :-: |")

    for idx, table in enumerate(EXPECTED_14_TABLES, 1):
        tbl_info = report["tables"].get(table)
        if tbl_info:
            col_cnt = len(tbl_info["columns"])
            pk = ", ".join(tbl_info["primary_key"])
            fk_cnt = len(tbl_info["foreign_keys"])
            act_rows = tbl_info["row_count"]
            exp_rows = EXPECTED_DUMMY_ROW_COUNTS.get(table, 0)
            status = "PASS" if act_rows == exp_rows else "MISMATCH"
            lines.append(f"| {idx} | `{table}` | {col_cnt} | `{pk}` | {fk_cnt} | **{act_rows}** | {exp_rows} | {status} |")
        else:
            lines.append(f"| {idx} | `{table}` | - | - | - | 0 | {EXPECTED_DUMMY_ROW_COUNTS.get(table, 0)} | **MISSING** |")

    lines.append("")
    lines.append("---")
    lines.append("## 3. Detailed Table Schema Specifications")
    lines.append("")

    for table in EXPECTED_14_TABLES:
        tbl_info = report["tables"].get(table)
        if not tbl_info:
            continue
        lines.append(f"### Table: `{table}` ({tbl_info['row_count']} rows)")
        lines.append("")
        lines.append("| Column | Data Type | Nullable | Default |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for col in tbl_info["columns"]:
            dt = col["data_type"]
            if col["character_maximum_length"]:
                dt += f"({col['character_maximum_length']})"
            elif col["numeric_precision"]:
                dt += f"({col['numeric_precision']},{col['numeric_scale']})"
            nullable = "YES" if col["is_nullable"] == "YES" else "NO"
            default = col["column_default"] or "-"
            # truncate long default
            if len(str(default)) > 35:
                default = str(default)[:32] + "..."
            lines.append(f"| `{col['column_name']}` | {dt} | {nullable} | `{default}` |")
        
        if tbl_info["foreign_keys"]:
            lines.append("")
            lines.append("**Foreign Keys:**")
            for fk in tbl_info["foreign_keys"]:
                lines.append(f"- `{fk['column_name']}` -> `{fk['foreign_table_name']}({fk['foreign_column_name']})` (`{fk['constraint_name']}`)")

        if tbl_info["indexes"]:
            lines.append("")
            lines.append("**Indexes:**")
            for idx_info in tbl_info["indexes"]:
                lines.append(f"- `{idx_info['indexname']}`: `{idx_info['indexdef']}`")
        
        lines.append("")

    return "\n".join(lines)


def run_inspection():
    """Main execution entry point."""
    print("=" * 70)
    print("EV Charging Network - READ-ONLY Database Inspector")
    print("=" * 70)

    try:
        report = inspect_database()
    except Exception as e:
        print(f"DATABASE INSPECTION FAILED: {e}")
        sys.exit(1)

    root_dir = Path(__file__).resolve().parent.parent.parent
    reports_dir = root_dir / "database" / "reports"
    docs_dir = root_dir / "docs"

    reports_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "database_inspection_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_content = generate_markdown_report(report)
    md_path = reports_dir / "database_inspection_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    docs_schema_path = docs_dir / "DATABASE_SCHEMA.md"
    with open(docs_schema_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Inspection completed successfully.")
    print(f"- Tables Verified: {report['summary']['total_tables_found']}/14")
    print(f"- Total Rows Verified: {report['summary']['total_records_found']}/54")
    print(f"- Verification Status: {report['verification']['status']}")
    print(f"- Reports saved to:")
    print(f"    {json_path}")
    print(f"    {md_path}")
    print(f"    {docs_schema_path}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_inspection()

