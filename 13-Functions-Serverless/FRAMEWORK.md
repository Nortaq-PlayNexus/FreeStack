# FRAMEWORK: Free Serverless / Functions / Edge Computing
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Run backend code - APIs, webhooks, scheduled jobs, MCP servers - without a server, paying $0.

## THE FREE MATRIX
| Platform | Free quota | Cold start | Timeout | Card |
|---|---|---|---|---|
| Cloudflare Workers | 100,000 req/day, 10ms CPU/invocation | ~0ms | 30s wall | No |
| Cloudflare Pages Functions | 100k req/day | ~0ms | - | No |
| Cloudflare Durable Objects | bundled | - | - | No |
| Google Cloud Run | 2M req/mo, 360k vCPU-s, 360k GiB-s | 1-3s | 60 min | billing acct needed |
| AWS Lambda | 1M req/mo, 400k GB-s | seconds | 15 min | Yes |
| Azure Functions | 1M req/mo, 400k GB-s (consumption) | seconds | 10 min | Yes |
| Vercel Functions | 100GB-hrs/mo | ~250ms | 10s free tier | No |
| Netlify Functions | 125k/mo | ms | 10s | No |
| Deno Deploy | 1M req/mo (verifiable) | ~ms | - | No |

## WINNER: Cloudflare Workers
- 100k req/day free = ~3M requests/month. More than most production personal apps ever see.
- Near-zero cold start (V8 isolates, not containers) = global edge API in milliseconds.
- Native data stores: KV, D1 (SQLite), R2 (object storage), Durable Objects (stateful), Vectorize (embeddings), Queues (jobs), Cron Triggers.
- The WHOLE free stack (Workers + Pages + R2 + D1 + KV + DNS + CDN + email routing + analytics) lives in one free Cloudflare account.

## FRAMEWORK: an API/webhook/job on Workers in ~10 min
1. `npm create cloudflare@latest my-api` (choose Workers, TypeScript).
2. Write your route handler. Add:
   - a KV/D1 binding for storage,
   - a Cron Trigger (`scheduled`) for recurring jobs,
   - a Queue binding for background work.
3. `npx wrangler deploy` -> live at `https://my-api.<subdomain>.workers.dev`, edge-served globally, free HTTPS.
4. Point a custom domain at it via Cloudflare (12-Domains-DNS).

## FRAMEWORK: container-y / long-running stuff -> Cloud Run
1. Dockerize (or `--source .` buildpack).
2. `gcloud run deploy my-svc --source . --region us-central1 --allow-unauthenticated --port 3000`
3. 2M requests/month free; scales to zero = $0 when idle. Handles WebSockets, 60-min timeouts, real containers.
4. Requires a billing account (not charged within free limits).

## THE META (need unlimited/always-warm serverless?)
Free serverless caps are daily/monthly requests. Meta:
1. **Always warm for $0**: Cloud Run with `--min-instances=0` is cold; for warm, combine: keep the compute light, let Cloudflare cache GETs (cache hit = no invocation) - cache everything cacheable.
2. **Add compute**: offload CPU-heavy work to your always-free Oracle VM (07) via HTTP - the VM does the heavy lifting, serverless does the edge.
3. **Split tenants**: spread services across Cloudflare + Cloud Run + Lambda + Deno (4 independent free budgets).
4. Cron-heavy work: GitHub Actions schedules (10-Git-CICD) are free and separate from your runtime quotas.

## GOTCHAS
- Workers free: 10ms CPU per invocation - fine for I/O-heavy edge code, NOT for heavy computation. Move CPU to a VM.
- Workers: no Node.js APIs; use Web Platform APIs (fetch, KV, etc.).
- Cloudflare Pages Functions count toward the same 100k/day.
- Vercel free: 10s function timeout; commercial projects require Pro.
- Cloud Run free tier requires a billing account on file (Google) - within limits, $0.
- Lambda/Azure free tiers need a card and their free requests are monthly (not daily).
- Serverless = stateless. Persistent state needs KV/D1/DO or an external DB (06).
