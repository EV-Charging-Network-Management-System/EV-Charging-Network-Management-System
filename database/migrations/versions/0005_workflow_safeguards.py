"""Persist replayable mutations and the administrative audit trail."""

from alembic import op

revision = "0005_workflow_safeguards"
down_revision = "0004_meter_readings"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE idempotent_operations (
            user_id bigint REFERENCES users(user_id) ON DELETE CASCADE,
            operation varchar(80),
            key_hash varchar(64),
            request_hash varchar(64) NOT NULL,
            response jsonb,
            PRIMARY KEY (user_id, operation, key_hash)
        )
    """)
    op.execute("""
        CREATE TABLE admin_audit_events (
            event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            actor_id bigint NOT NULL,
            action varchar(40) NOT NULL,
            resource_id bigint NOT NULL,
            details jsonb NOT NULL,
            occurred_at timestamptz NOT NULL DEFAULT now()
        )
    """)


def downgrade():
    op.drop_table("admin_audit_events")
    op.drop_table("idempotent_operations")
