#!/usr/bin/env bash
# backup-to-r2.sh - sync any folder/bucket to R2. Incremental + checksummed.
# Usage: bash backup-to-r2.sh /path/to/data [r2:bucket/prefix] [--delete]
set -euo pipefail

SRC="${1:?usage: backup-to-r2.sh SRC [DEST] [--delete]}"
DEST="${2:-r2:freestack-backups}"
EXTRA="${3:-}"

command -v rclone >/dev/null 2>&1 || { echo "rclone missing - run rclone-setup.sh first"; exit 1; }

echo ">> syncing $SRC -> $DEST (incremental, checksummed)"
rclone sync "$SRC" "$DEST" \
  --progress --stats 5s --transfers 4 --checkers 8 \
  --exclude '.git/**' --exclude 'node_modules/**' --exclude '__pycache__/**' \
  $EXTRA
echo ">> done."
