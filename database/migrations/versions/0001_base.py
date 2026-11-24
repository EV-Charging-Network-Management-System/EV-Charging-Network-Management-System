"""Install the original 14-table PostgreSQL schema."""

from pathlib import Path

from alembic import op

revision = "0001_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    source = Path(__file__).parents[2] / "schema" / "EV_Charging_Create_Tables.sql"
    ddl = source.read_text(encoding="utf-8").split("BEGIN;", 1)[1].split("COMMIT;", 1)[0]
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    for table in (
        "charger_status_history", "maintenance_records", "payments", "invoices",
        "charging_sessions", "reservations", "pricing_rules", "tariffs", "chargers",
        "stations", "vehicle_connector_types", "vehicles", "connector_types", "users",
    ):
        op.drop_table(table)
