#!/usr/bin/env bash
# deploy-workers.sh - Deploy the TS MCP server to Cloudflare Workers (free).
set -euo pipefail
cd "$(dirname "$0")/mcp-ts"
ENV_FILE="../../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../../.env}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID in ../../.env}"

# create the KV namespace the binding needs (free)
NS=$(curl -fsS -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/storage/kv/namespaces" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"title":"freestack-mcp-kv"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['id'])")

# bake the namespace id + a random token into the config if not already set
sed -i.bak "s/REPLACE_WITH_KV_NAMESPACE_ID/$NS/g; s/REPLACE_WITH_LONG_RANDOM_TOKEN/$(head -c24 /dev/urandom | base64 | tr -d '/+=')/g" wrangler.jsonc

npm install
npx wrangler login || true
npx wrangler deploy
echo ""
echo "   MCP endpoint: https://freestack-mcp.<your-subdomain>.workers.dev/mcp"
echo "   Bearer token was generated into wrangler.jsonc vars.MCP_AUTH_TOKEN"
echo "   Client config example: see connect.json.example"
