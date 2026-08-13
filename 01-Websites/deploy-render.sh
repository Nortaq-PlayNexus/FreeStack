#!/usr/bin/env bash
# deploy-render.sh - Deploy a dynamic web service to Render (750 free hours/month).
# Requires: RENDER_API_KEY in ../.env (free account, no card for free services)
# Also installs the render CLI: https://render.com/docs/cli
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${RENDER_API_KEY:?Set RENDER_API_KEY in ../.env}"
SERVICE_NAME="${SERVICE_NAME:-freestack-app}"

if ! command -v render >/dev/null; then
  echo ">> installing render CLI..."
  curl -fsSL https://render.com/download/render-cli.sh | sh
fi

echo ">> deploying dynamic service: $SERVICE_NAME"
render deploy --type web --name "$SERVICE_NAME" --repo "$GITHUB_REPO"

echo ""
echo "   Free tier contract: spins down after 15 min idle, ~1 min cold start on first hit."
echo "   Keep it warm for free with Upptime (11-Monitoring-Analytics) or accept the cold start."
echo ""
echo "   Want it 24/7 with zero sleep? Deploy the same Dockerfile to your free VM:"
echo "     docker compose -f ../03-SSH-Tunnels/sish-compose.yml up -d   # after VM setup (07)"
