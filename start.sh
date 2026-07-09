#!/usr/bin/env sh
set -e

: "${HOST:=0.0.0.0}"
: "${PORT:=8000}"
: "${WEB_CONCURRENCY:=1}"
: "${LOG_LEVEL:=info}"
: "${RUN_MIGRATIONS:=false}"
: "${RUN_SEED:=false}"

if [ "$RUN_MIGRATIONS" = "true" ]; then
  alembic upgrade head
fi

if [ "$RUN_SEED" = "true" ]; then
  python scripts/seed_all.py
fi

exec uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WEB_CONCURRENCY" \
  --log-level "$LOG_LEVEL"
