#!/usr/bin/env bash
# rclone-setup.sh - generate rclone config from ../.env and create buckets.
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

CONF="${RCLONE_CONFIG:-$HOME/.config/rclone/rclone.conf}"
mkdir -p "$(dirname "$CONF")"

if command -v rclone >/dev/null 2>&1; then
  echo ">> rclone found: $(rclone version | head -1)"
else
  echo ">> installing rclone..."
  curl https://rclone.org/install.sh | sudo bash
fi

R2_ACCOUNT_ID="${R2_ACCOUNT_ID:-}"
R2_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-}"
R2_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-}"

if [ -n "$R2_ACCOUNT_ID" ] && [ -n "$R2_ACCESS_KEY_ID" ] && [ -n "$R2_SECRET_ACCESS_KEY" ]; then
  echo ">> writing [r2] remote..."
  cat > "$CONF" <<EOF
[r2]
type = s3
provider = Cloudflare
access_key_id = $R2_ACCESS_KEY_ID
secret_access_key = $R2_SECRET_ACCESS_KEY
endpoint = https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com
acl = private
EOF
  rclone mkdir r2:freestack-backups 2>/dev/null || true
  echo ">> r2 remote ready. buckets:"
  rclone lsd r2:
else
  echo ">> R2_ACCOUNT_ID/R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY not all set - skipping r2 (add them to ../.env)"
fi

if [ -n "${B2_KEY_ID:-}" ] && [ -n "${B2_APP_KEY:-}" ]; then
  echo ">> writing [b2] remote..."
  cat >> "$CONF" <<EOF

[b2]
type = b2
account = $B2_KEY_ID
key = $B2_APP_KEY
hard_delete = false
EOF
  echo ">> b2 remote ready."
fi

echo ">> config at $CONF"
