#!/usr/bin/env bash
set -euo pipefail

echo "== db_restore: starting =="

: "${DB_HOST:?Missing DB_HOST}"
: "${DB_PORT:?Missing DB_PORT}"
: "${DB_NAME:?Missing DB_NAME}"
: "${DB_USER:?Missing DB_USER}"
: "${DB_PASSWORD:?Missing DB_PASSWORD}"

DUMP_FILE="${DUMP_FILE:-/dumps/latest.dump}"
RECREATE_DB="${RECREATE_DB:-true}" # set to true if you want to drop & recreate DB

export PGPASSWORD="$DB_PASSWORD"

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "ERROR: Dump file not found: $DUMP_FILE"
  echo "Contents of /dumps:"
  ls -lah /dumps || true
  exit 1
fi

echo "Dump file found: $DUMP_FILE"
ls -lah "$DUMP_FILE"

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 2
done
echo "Postgres is ready."

if [[ "$RECREATE_DB" == "true" ]]; then
  echo "Recreating database $DB_NAME..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}';
DROP DATABASE IF EXISTS "${DB_NAME}";
CREATE DATABASE "${DB_NAME}";
SQL
fi

# Decide restore method
if file "$DUMP_FILE" 2>/dev/null | grep -qi "PostgreSQL custom database dump"; then
  echo "Detected custom-format dump. Restoring with pg_restore..."
  pg_restore \
    --clean --if-exists \
    --no-owner --no-privileges \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d "$DB_NAME" \
    "$DUMP_FILE"
else
  # Fallback based on extension (or if "file" isn't available)
  case "$DUMP_FILE" in
    *.sql)
      echo "Detected .sql dump. Restoring with psql..."
      psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$DUMP_FILE"
      ;;
    *)
      echo "WARNING: Could not confidently detect dump type."
      echo "Trying pg_restore first (common for .dump)..."
      pg_restore \
        --clean --if-exists \
        --no-owner --no-privileges \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -d "$DB_NAME" \
        "$DUMP_FILE" \
      || {
        echo "pg_restore failed. If your dump is plain SQL, rename it to .sql and try again."
        exit 1
      }
      ;;
  esac
fi

echo "== db_restore: done =="
