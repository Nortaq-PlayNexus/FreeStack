#!/usr/bin/env bash
# deploy.sh - create the KV namespace and deploy the api-router Worker (free).
set -euo pipefail
cd "$(dirname "$0")/api-router"
ENV_FILE="../../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../../.env}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID in ../../.env}"

NS=$(curl -fsS -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/storage/kv/namespaces" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"title":"api-router-cache"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['id'])")

sed -i.bak "s/REPLACE_WITH_KV_NAMESPACE_ID/$NS/g" wrangler.jsonc

npm install
npx wrangler deploy

echo ""
echo "   LIVE: https://api-router.<your-subdomain>.workers.dev"
echo "   Try:  https://api-router.<your-subdomain>.workers.dev/v1/weather/open_meteo/?latitude=40.7&longitude=-74"
echo "   Add your real keys to the wrangler.jsonc vars or via Cloudflare dashboard -> Workers -> Settings -> Variables."
