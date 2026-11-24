"""Enforce half-open active bookings per charger in PostgreSQL."""

from alembic import op

revision = "0002_booking"
down_revision = "0001_base"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("""
        ALTER TABLE reservations ADD CONSTRAINT exclude_overlapping_reservations
        EXCLUDE USING gist (
            charger_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        ) WHERE (status IN ('PENDING', 'CONFIRMED'))
    """)


def downgrade():
    op.drop_constraint("exclude_overlapping_reservations", "reservations")
