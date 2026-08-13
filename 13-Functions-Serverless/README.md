# 13 — Free Serverless Functions: a complete Workers API project

A production-shaped Cloudflare Worker showing the full free-serverless surface in one app:
**D1** (SQLite database), **KV** (cache), **R2** (files), **Cron triggers**, **CORS**,
**bearer auth**, and **JSON routes**. All on the free plan (100k req/day).

| File | Purpose |
|---|---|
| `api/src/index.ts` | The Worker: routes, auth, D1, KV cache, R2 uploads, scheduled job |
| `api/schema.sql` | D1 schema (applied by setup script) |
| `api/wrangler.toml` | Config + bindings (D1, KV, R2) + cron |
| `api/package.json` | wrangler devDependency |
| `setup.sh` | Creates D1/KV/R2, writes IDs into wrangler.toml, deploys |
| `test.sh` | Smoke test the live endpoints |
| `README.md` | Steps |

## Quick start
```bash
cd api && bash setup.sh
# => deploys, prints the URL
curl https://freestack-api.<you>.workers.dev/healthz
# writes need a bearer token (generated + printed by setup.sh, or set API_TOKEN in wrangler.toml)
curl -X POST https://freestack-api.<you>.workers.dev/api/items \
  -H "authorization: Bearer <token>" -H "content-type: application/json" \
  -d '{"name":"first item"}'
curl https://freestack-api.<you>.workers.dev/api/items
```

## Routes
| Method/Path | Auth | What |
|---|---|---|
| GET `/healthz` | none | health + D1/KV/R2 status |
| GET `/api/items` | none | list items (KV-cached 60s) |
| POST `/api/items` | bearer | create item in D1, bust cache |
| GET `/api/files/<key>` | none | stream file from R2 |
| PUT `/api/files/<key>` | bearer | upload file to R2 |
| Cron `0 6 * * *` | - | warm D1, prune old KV keys |
