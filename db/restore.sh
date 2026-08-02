#!/bin/sh
set -e

DUMP=/docker-entrypoint-initdb.d/spotify_tracker.dump

if [ ! -f "$DUMP" ]; then
  echo "ERROR: $DUMP not found. Place the Postgres dump at the repo root (spotify_tracker.dump), then run: docker compose down -v && docker compose up --build" >&2
  exit 1
fi

echo "Restoring $DUMP into database '$POSTGRES_DB'..."
pg_restore --no-owner --no-privileges --exit-on-error -v -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$DUMP"
echo "Restore complete."
