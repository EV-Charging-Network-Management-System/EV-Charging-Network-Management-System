"""Store time-series charger readings by session and timestamp."""

from alembic import op

revision = "0004_meter_readings"
down_revision = "0003_revocation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE meter_readings (
            session_id bigint REFERENCES charging_sessions(session_id) ON DELETE CASCADE,
            recorded_at timestamptz,
            energy_kwh numeric(12, 3),
            power_kw numeric(10, 3),
            PRIMARY KEY (session_id, recorded_at),
            CONSTRAINT meter_readings_energy_nonnegative CHECK (energy_kwh >= 0),
            CONSTRAINT meter_readings_power_nonnegative CHECK (power_kw >= 0),
            CONSTRAINT meter_readings_has_value CHECK (energy_kwh IS NOT NULL OR power_kw IS NOT NULL)
        )
    """)


def downgrade():
    op.drop_table("meter_readings")
