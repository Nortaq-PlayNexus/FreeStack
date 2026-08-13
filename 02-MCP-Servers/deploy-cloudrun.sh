#!/usr/bin/env bash
# deploy-cloudrun.sh - Deploy the Python MCP server as a container to Cloud Run.
# Free tier: 2M requests/mo, 360k vCPU-seconds, scales to zero. Needs a GCP billing account
# (not charged while inside the free tier).
set -euo pipefail
cd "$(dirname "$0")/mcp-py"
ENV_FILE="../../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID in ../../.env}"
REGION="${GCP_REGION:-us-central1}"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$GCP_PROJECT_ID"

# serve the FastMCP app over HTTP: expose a small ASGI wrapper
cat > app.py <<'EOF'
from fastmcp.server import FastMCP
import server  # reuse tools
app = server.mcp.streamable_http_app
EOF

gcloud run deploy freestack-mcp-py \
  --source . \
  --project "$GCP_PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 1 --memory 512Mi --max-instances 3

echo ""
echo "   MCP endpoint: https://<hash>.<region>.run.app/mcp"
echo "   NOTE: --allow-unauthenticated exposes it publicly; add a bearer-token check"
echo "   in app.py for production (see FRAMEWORK.md AUTH section)."
