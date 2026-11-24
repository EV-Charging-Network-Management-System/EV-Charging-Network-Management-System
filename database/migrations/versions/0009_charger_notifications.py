"""Notify the live charger inventory when status or membership changes."""

from alembic import op

revision = "0009_charger_notifications"
down_revision = "0008_charger_heartbeats"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE FUNCTION notify_charger_inventory() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP <> 'UPDATE' OR OLD.operational_status IS DISTINCT FROM NEW.operational_status THEN
                PERFORM pg_notify('ev_chargers', '');
            END IF;
            RETURN NULL;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER charger_inventory_changed
        AFTER INSERT OR DELETE OR UPDATE OF operational_status ON chargers
        FOR EACH ROW EXECUTE FUNCTION notify_charger_inventory()
    """)


def downgrade():
    op.execute("DROP TRIGGER charger_inventory_changed ON chargers")
    op.execute("DROP FUNCTION notify_charger_inventory()")
