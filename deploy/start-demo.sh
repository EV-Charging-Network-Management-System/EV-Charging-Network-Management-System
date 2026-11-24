set -eu
alembic upgrade head
if [ "${SEED_SAMPLE_DATA:-false}" = "true" ]; then
  python -m database.seed.demo --confirm-demo-database
  python -m database.seed.history --confirm-demo-database
fi
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-access-log
