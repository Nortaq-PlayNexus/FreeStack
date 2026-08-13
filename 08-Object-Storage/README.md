# 08 — Free Object Storage: R2 (zero egress) + B2

| Provider | Free tier | Why |
|---|---|---|
| Cloudflare R2 | 10GB storage, 1M class A ops, **no egress fees** | Backups, static assets, serving media - zero egress is the killer feature |
| Backblaze B2 | 10GB storage + free CDN egress through Cloudflare | Second copy / geo-redundancy |

| File | Purpose |
|---|---|
| `rclone.conf.example` | Ready-to-fill rclone config for R2 + B2 |
| `rclone-setup.sh` | Bootstraps rclone config from your ../.env, creates buckets |
| `r2-worker/` | Cloudflare Worker: serve PRIVATE R2 objects with a token; public upload endpoint |
| `backup-to-r2.sh` | Generic "any folder -> R2" sync (used by 06 for DB dumps) |
| `README.md` | Steps |

## Quick start
```bash
# 1) put in ../.env:
#    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY   (dash.cloudflare.com > R2 > Manage R2 API Tokens)
#    B2_KEY_ID, B2_APP_KEY                                    (backblaze app keys)
bash rclone-setup.sh

# 2) use it everywhere:
rclone ls r2:freestack-backups
bash backup-to-r2.sh ~/important-files freestack-backups/my-files
```

## Private bucket behind a Worker
The `r2-worker/` folder is a deployable Worker that:
- serves objects from a private R2 bucket at `https://<worker>.<you>.workers.dev/files/<key>`
- requires `?token=...` (set `OBJECT_TOKEN` var) - no public bucket needed
- uploads via `POST /upload` with the same token

```bash
cd r2-worker && npm i && npx wrangler deploy
curl "https://worker.you.workers.dev/files/hello.txt?token=SECRET"
```
