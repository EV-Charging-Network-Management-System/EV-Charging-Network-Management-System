from alembic import context

from backend.app.core.config import settings
from backend.app.core.database import engine

if context.is_offline_mode():
    context.configure(url=settings.sync_database_url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
