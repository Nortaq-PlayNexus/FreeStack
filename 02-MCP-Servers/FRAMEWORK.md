# FRAMEWORK: Free MCP (Model Context Protocol) Servers
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Turn an MCP server into a remote HTTPS endpoint that ANY AI client (Claude Desktop, Cursor, agents) can call, at $0/month.

## THE RULE: transport first
- stdio = local only (runs as subprocess of the client). CANNOT be hosted remotely.
- Streamable HTTP = the standard for remote. Your server must expose `POST /mcp` over HTTPS.
- The 2025-03-26 spec made Streamable HTTP the default. HTTP+SSE is deprecated. Do not start new projects on it.
- Switching transport is a few lines in both the Python (FastMCP) and TypeScript (@modelcontextprotocol/sdk) SDKs.

## THE FREE MATRIX
| Platform | Free quota | Best for | Cold start | State |
|---|---|---|---|---|
| Cloudflare Workers (Agents SDK `McpAgent`) | 100k req/day, 10ms CPU | TypeScript, global edge, built-in OAuth | ~0ms | Durable Objects |
| FastMCP Cloud (Prefect Horizon) | free personal tier | Python FastMCP, one-command `fastmcp deploy` | - | dedicated process |
| mcphosting.io | free | zero-config, connect GitHub repo | - | - |
| Vercel Functions | 100GB-hrs/mo | Next.js teams | ~250ms | stateless only |
| Google Cloud Run | 2M req/mo, 360k vCPU-s | containers, longer exec, WebSockets | 1-3s | yes (restart loses state) |
| Render (web service) | 750 hr/mo | long-running processes | 30-50s (spins down) | yes |
| Railway | $5 credit + $1/mo | long-running | none | yes |
| AWS Lambda | 1M req/mo, 400k GB-s | bursty stateless | seconds | no |

## FRAMEWORK A: TypeScript -> Cloudflare Workers (fastest, ~15 min)
1. `npm create cloudflare@latest my-mcp -- --template mcp-agent-starter` (official template).
2. Use `McpAgent` from the `agents` package - it wires Streamable HTTP, WebSocket hibernation, and OAuth automatically.
3. `npx wrangler deploy`.
4. Connect: `https://my-mcp.<your-subdomain>.workers.dev/mcp` in any MCP client.
5. 100k req/day is far more than a personal/team MCP server needs. Free forever.

## FRAMEWORK B: Python FastMCP -> FastMCP Cloud (fastest for Python)
1. Build server with FastMCP: `from fastmcp import FastMCP; mcp = FastMCP("x")`.
2. `fastmcp deploy` -> one command. Free personal tier includes OAuth, monitoring, CI/CD from git.
3. Live at `https://<name>.fastmcp.app/mcp`.

## FRAMEWORK C: Containers / persistent connections -> Cloud Run
1. Write a Dockerfile for your server (create-mcp-server scaffold includes one).
2. `gcloud run deploy my-mcp-server --source . --region us-central1 --allow-unauthenticated --port 3000`
3. Live at `https://<hash>.run.app/mcp`. 2M requests/month free. Scales to zero = $0 when idle.
4. NOTE: Cloud Run requires a billing account even on free tier (you won't be charged within limits).

## AUTH (do not skip)
- Any HTTP client can hit a public endpoint. Add bearer-token check on every request, or use OAuth 2.1 (MCP spec standard).
- Validate the Origin header (DNS rebinding protection).
- For single-user: static API key in Authorization header is fine.

## GOTCHAS
- Serverless = stateless across requests. For per-session state use Cloudflare Durable Objects, or a container platform.
- Vercel free tier function timeout is 10s - tools calling slow APIs will time out. Use Railway/Render/Cloud Run instead.
- MCP SDKs (as of mid-2025) do NOT support external session persistence - a session must stay on one instance.
- 20 concurrent stdio connections = 20/22 failures in one real test. Never run stdio under load.

## THE META (no-free-tier escape)
If you need an MCP server that NEVER sleeps, holds persistent state, and runs heavy workloads: deploy it to the free always-on Oracle VM (2 Arm cores / 12GB RAM) in a Docker container, expose it via `ssh -R` tunnel or Cloudflare Tunnel, put Cloudflare in front for HTTPS. Costs $0. See 07 + 03.
