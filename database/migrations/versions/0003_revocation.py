"""Persist access-token revocations for all API workers."""

import sqlalchemy as sa
from alembic import op

revision = "0003_revocation"
down_revision = "0002_booking"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "revoked_tokens",
        sa.Column("token_id", sa.String(32), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade():
    op.drop_table("revoked_tokens")
