# 04 — Free APIs: catalog + caching router

Two parts:

1. **`catalog.yml`** (at project root) — every free API we know, keyed by category with endpoints and key env vars. It is the source of truth for the router and the master list.
2. **`api-router/`** — a Cloudflare Worker (free, 100k req/day) that proxies free APIs with:
   - **caching** on the edge (KV, up to 1 hour) — cache hits cost 0 requests against the upstream quota
   - **key rotation/failover** — if provider A 429s, it falls back to provider B for the same data
   - **server-side keys** — your API keys never reach the browser
   - **rate limiting** per client IP (free)

| File | Purpose |
|---|---|
| `api-router/src/index.ts` | The Worker: proxy + cache + failover + rate limit |
| `api-router/wrangler.jsonc` | Worker config with KV binding |
| `api-router/package.json` | deps |
| `deploy.sh` | Create KV namespace + deploy worker |
| `client.sh` | Example client calls (curl) |
| `README.md` | Steps |

## 5-minute setup
```bash
bash deploy.sh
# ->
curl 'https://api-router.<you>.workers.dev/v1/weather?lat=40.7&lon=-74.0'
curl 'https://api-router.<you>.workers.dev/v1/crypto?coin=bitcoin'
curl 'https://api-router.<you>.workers.dev/v1/fx?base=USD&symbols=EUR,GBP'
```
All responses are cached for 1h, so your free upstream quotas go ~30x further.
