"""Keep the accepted session price independent of later tariff edits."""

from alembic import op

revision = "0007_tariff_snapshot"
down_revision = "0006_login_throttle"
branch_labels = None
depends_on = None

COLUMNS = (
    ("locked_base_price_per_kwh", "numeric(10, 2)"),
    ("applied_rate_per_kwh", "numeric(14, 2)"),
    ("locked_session_fee", "numeric(10, 2)"),
    ("locked_tax_rate_percent", "numeric(5, 2)"),
    ("applied_multiplier", "numeric(6, 3)"),
    ("applied_rule_type", "varchar(24)"),
)


def upgrade():
    for name, data_type in COLUMNS:
        op.execute(f"ALTER TABLE charging_sessions ADD COLUMN {name} {data_type}")
    op.execute("""
        ALTER TABLE charging_sessions ADD CONSTRAINT charging_sessions_complete_tariff_snapshot
        CHECK (
            num_nonnulls(locked_base_price_per_kwh, applied_rate_per_kwh, locked_session_fee,
                         locked_tax_rate_percent, applied_multiplier, applied_rule_type) IN (0, 6)
        )
    """)


def downgrade():
    op.drop_constraint("charging_sessions_complete_tariff_snapshot", "charging_sessions")
    for name, _ in reversed(COLUMNS):
        op.drop_column("charging_sessions", name)
