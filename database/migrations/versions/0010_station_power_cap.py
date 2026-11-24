"""Store an optional site-wide power cap."""

from alembic import op

revision = "0010_station_power_cap"
down_revision = "0009_charger_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE stations ADD COLUMN site_power_cap_kw numeric(10, 3)
        CHECK (site_power_cap_kw IS NULL OR site_power_cap_kw > 0)
    """)


def downgrade():
    op.drop_column("stations", "site_power_cap_kw")
