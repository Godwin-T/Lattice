#!/usr/bin/env bash
set -euo pipefail

if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
  retries="${AUTO_MIGRATE_RETRIES:-20}"
  delay="${AUTO_MIGRATE_DELAY_SECONDS:-2}"
  attempt=1
  if [ "${AUTO_GENERATE_MIGRATIONS:-true}" = "true" ]; then
    versions_dir="${ALEMBIC_VERSIONS_DIR:-alembic/versions}"
    if [ -d "$versions_dir" ] && [ -z "$(ls -A "$versions_dir" 2>/dev/null)" ]; then
      echo "[entrypoint] No migrations found. Autogenerating initial revision."
      alembic revision --autogenerate -m "init"
    fi
  fi
  echo "[entrypoint] Running migrations: alembic upgrade head"
  while true; do
    set +e
    alembic upgrade head
    status=$?
    set -e
    if [ "$status" -eq 0 ]; then
      break
    fi
    if [ "$attempt" -ge "$retries" ]; then
      echo "[entrypoint] Migration failed after ${retries} attempts"
      exit "$status"
    fi
    echo "[entrypoint] Migration failed (attempt ${attempt}/${retries}), retrying in ${delay}s..."
    attempt=$((attempt + 1))
    sleep "$delay"
  done
else
  echo "[entrypoint] Skipping migrations (AUTO_MIGRATE=${AUTO_MIGRATE})"
fi

echo "[entrypoint] Starting server"
exec "$@"
