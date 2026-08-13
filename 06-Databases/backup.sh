#!/usr/bin/env bash
# backup.sh - nightly database backup to free object storage (R2/B2).
# Dumps:  (NEON|DATABASE)_URL  -> rclone -> r2:freestack-backups/db/
# Retention: keep last 30 dumps, delete older.
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

DB_URL="${DATABASE_URL:-${NEON_DATABASE_URL:-}}"
: "${DB_URL:?Set DATABASE_URL or NEON_DATABASE_URL in ../.env}"
: "${RCLONE_REMOTE:?Set RCLONE_REMOTE (e.g. r2:freestack-backups) after configuring rclone in 08-Object-Storage}"
: "${RETENTION_DAYS:=30}"

STAMP="$(date +%F-%H%M%S)"
TMP="$(mktemp -d)"
DUMP="$TMP/db-$STAMP.sql.gz"

echo ">> dumping database..."
if command -v pg_dump >/dev/null 2>&1; then
  pg_dump --no-owner --no-privileges "$DB_URL" | gzip -9 > "$DUMP"
else
  # docker fallback so the VM needs no postgres client
  docker run --rm -i postgres:16-alpine pg_dump --no-owner --no-privileges "$DB_URL" | gzip -9 > "$DUMP"
fi

echo ">> uploading to $RCLONE_REMOTE/db/"
rclone copy "$DUMP" "$RCLONE_REMOTE/db/" --progress --stats 5s 2>/dev/null || rclone copy "$DUMP" "$RCLONE_REMOTE/db/"

echo ">> pruning dumps older than $RETENTION_DAYS days"
rclone lsf "$RCLONE_REMOTE/db/" | while read -r f; do
  ts="${f#db-}"; ts="${ts%.sql.gz}"
  if [[ "$(date -d "$ts" +%s 2>/dev/null || echo 0)" -lt "$(date -d "-${RETENTION_DAYS} days" +%s)" ]]; then
    rclone delete "$RCLONE_REMOTE/db/$f"
    echo "   deleted $f"
  fi
done

rm -rf "$TMP"
echo ">> backup complete: db-$STAMP.sql.gz ($(du -h "$DUMP" | cut -f1) compressed)"
