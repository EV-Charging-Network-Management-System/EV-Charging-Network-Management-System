"""Track the last valid message from each configured charger."""

from alembic import op

revision = "0008_charger_heartbeats"
down_revision = "0007_tariff_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE charger_heartbeats (
            charger_id bigint PRIMARY KEY REFERENCES chargers(charger_id) ON DELETE CASCADE,
            last_seen_at timestamptz NOT NULL
        )
    """)


def downgrade():
    op.drop_table("charger_heartbeats")
