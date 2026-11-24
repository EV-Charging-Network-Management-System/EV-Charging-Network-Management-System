"""Store short-window account sign-in throttles."""

from alembic import op

revision = "0006_login_throttle"
down_revision = "0005_workflow_safeguards"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE login_windows (
            subject_hash varchar(64),
            window_start timestamptz,
            attempts integer NOT NULL CHECK (attempts > 0),
            PRIMARY KEY (subject_hash, window_start)
        )
    """)
    op.create_index("ix_login_windows_window_start", "login_windows", ["window_start"])


def downgrade():
    op.drop_table("login_windows")
