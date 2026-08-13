#!/usr/bin/env bash
# deploy-cloudflare.sh - Create + deploy a static site to Cloudflare Pages (free, unlimited bandwidth)
# Requires: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID in ../.env (free Cloudflare account)
# Idempotent: safe to re-run; updates the project if it exists.
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../.env}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID in ../.env}"
SITE_NAME="${SITE_NAME:-freestack-site}"

API="https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects"
AUTH="Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# 1. Ensure the Pages project exists (free plan supports 100 projects).
if ! curl -fsS -H "$AUTH" "$API/$SITE_NAME" >/dev/null 2>&1; then
  echo ">> creating Pages project: $SITE_NAME"
  curl -fsS -X POST "$API" -H "$AUTH" -H "content-type: application/json" \
    -d "{\"name\":\"$SITE_NAME\"}" >/dev/null
else
  echo ">> project $SITE_NAME already exists"
fi

# 2. Upload site files as a deployment (no git needed for the free tier).
DEPLOY_ID=$(curl -fsS -X POST "$API/$SITE_NAME/deployments" -H "$AUTH" \
  --data-binary "@-" -H "content-type: multipart/form-data" <<EOF | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['id'])"
name=site&file=@site/index.html&file=@site/style.css&file=@site/functions/healthz.js&file=@site/functions/hello.js
EOF
)

echo ">> deploying... deployment id: $DEPLOY_ID"
URL="https://$SITE_NAME.pages.dev"
echo ""
echo "   LIVE at: $URL"
echo "   healthz: $URL/healthz"
echo ""
echo "   Next: connect git for auto-deploys, or add your free domain (12-Domains-DNS)."
