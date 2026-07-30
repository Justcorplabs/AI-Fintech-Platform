#!/bin/sh
set -eu

echo "Applying database migrations..."
python -m alembic upgrade head

echo "Starting API..."
PORT="${PORT:-8000}"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT"
