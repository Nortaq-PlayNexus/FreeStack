#!/usr/bin/env bash
# deploy-static.sh - deploy the static site to Cloudflare Pages (free, 100 builds/day).
# Used by CI (10-Git-CICD/.github/workflows/deploy.yml) and runnable locally.
# Requires CLOUDFLARE_API_TOKEN in ../.env (or env).
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

TOKEN="${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../.env}"
ACCOUNT_ID="${CF_ACCOUNT_ID:-}"
PROJECT="${CF_PAGES_PROJECT:-freestack}"

command -v wrangler >/dev/null 2>&1 || npm install -g wrangler

echo ">> building site (copies site/ into .dist, keeps functions/)..."
rm -rf .dist && mkdir -p .dist
cp -r site/. .dist/

echo ">> deploying to Cloudflare Pages (project: $PROJECT)..."
npx wrangler pages deploy .dist --project-name "$PROJECT" --commit-dirty=true
echo ">> live at https://$PROJECT.pages.dev"
