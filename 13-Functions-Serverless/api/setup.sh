#!/usr/bin/env bash
# setup.sh - create D1/KV/R2 resources, wire wrangler.toml, apply schema, deploy.
# Requires: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID in ../.env
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../../.env}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID in ../../.env}"

command -v node >/dev/null || { echo "node required"; exit 1; }
[ -d node_modules ] || npm install

echo ">> creating D1 database..."
D1_ID=$(npx wrangler d1 create freestack-d1 2>/dev/null | grep -oE '"[0-9a-f]{32}"' | head -1 | tr -d '"')
if [ -z "$D1_ID" ]; then
  D1_ID=$(npx wrangler d1 create freestack-d1 | grep -oE '[0-9a-f]{32}' | head -1 || true)
fi
if [ -n "$D1_ID" ]; then
  sed -i "s/database_id = .*/database_id = \"$D1_ID\"/" wrangler.toml
  echo "   d1 id: $D1_ID"
  npx wrangler d1 execute freestack-d1 --file schema.sql --remote >/dev/null
fi

echo ">> creating KV namespace..."
KV_ID=$(npx wrangler kv namespace create KV 2>/dev/null | grep -oE '[0-9a-f]{32}' | head -1 || true)
[ -n "$KV_ID" ] && sed -i "s/id = .*/id = \"$KV_ID\"/" wrangler.toml && echo "   kv id: $KV_ID"

echo ">> creating R2 bucket..."
npx wrangler r2 bucket create freestack-files || true

echo ">> setting a random API token (override in wrangler.toml if you want)..."
TOKEN=$(python3 -c "import secrets;print(secrets.token_urlsafe(32))")
sed -i "s/API_TOKEN = .*/API_TOKEN = \"$TOKEN\"/" wrangler.toml
echo "   API_TOKEN: $TOKEN"

echo ">> deploying..."
npx wrangler deploy

echo ""
echo ">> live: https://freestack-api.<you>.workers.dev  (set the custom domain in CF, see 12)"
