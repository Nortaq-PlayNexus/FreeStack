#!/usr/bin/env bash
# deploy-fastmcp.sh - Deploy the Python MCP server to FastMCP Cloud (free personal tier).
set -euo pipefail
cd "$(dirname "$0")/mcp-py"

python3 -m pip install -q "fastmcp[cli]"
fastmcp login
fastmcp deploy server.py --name freestack-mcp-py

echo ""
echo "   LIVE at: https://freestack-mcp-py.fastmcp.app/mcp"
echo "   (free personal tier: OAuth, monitoring, CI/CD from git included)"
