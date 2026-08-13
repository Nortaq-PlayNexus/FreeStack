# 02 — Free MCP Servers

Two ready-to-run MCP servers with free remote hosting:

1. **TypeScript on Cloudflare Workers** (`mcp-ts/`) — the recommended path. Free tier 100k req/day, ~0ms cold start, built-in OAuth, WebSocket hibernation. Deploy with one command.
2. **Python FastMCP** (`mcp-py/`) — deploy in one command to FastMCP Cloud (free personal tier), or run locally over stdio.

Also included:
| File | Purpose |
|---|---|
| `mcp-ts/` | Complete Workers MCP server (Weather + KV notes), Streamable HTTP via official MCP SDK |
| `mcp-ts/wrangler.jsonc` | Workers config with KV binding + auth token |
| `mcp-py/server.py` | FastMCP server with memory/note tool + weather tool |
| `mcp-py/requirements.txt` | Dependencies |
| `mcp-py/smoketest.py` | End-to-end stdio round-trip test |
| `deploy-workers.sh` | Deploy the TS server to Cloudflare (free) |
| `deploy-fastmcp.sh` | Deploy the Python server to FastMCP Cloud (free personal tier) |
| `deploy-cloudrun.sh` | Deploy the Python server as a container to Cloud Run (2M req/mo free) |
| `Dockerfile` | Container for Cloud Run / Render / your VM |
| `connect.json.example` | Claude/Cursor config snippet to attach the remote server |
| `README.md` | Step-by-step |

## 30-second version
```bash
cd mcp-ts
npm install
npx wrangler deploy          # free, needs Cloudflare account + token in ../.env
# connect your MCP client to https://<worker>.<your-subdomain>.workers.dev/mcp
```
See README.md for the client config and auth.
