# 10 — Free Git + CI/CD: GitHub as your cron & pipeline engine

GitHub Actions gives you **2000 free minutes/month on public repos** (0 on private without
a paid plan), plus **scheduled workflows** that act as a free cron - perfect for the
keep-alives, backups, and health checks in this stack.

| File | Purpose |
|---|---|
| `.github/workflows/keepalive.yml` | Daily: poke free DBs so they never suspend (uses 06/keepalive.py) |
| `.github/workflows/backup.yml` | Nightly: dump DB -> rclone -> R2 (uses 06/backup.sh + 08) |
| `.github/workflows/deploy.yml` | On push: deploy the site (01) + r2-worker (08) |
| `.github/workflows/daily-check.yml` | Hourly: ping all services, email on failure (uses 09/send.py) |
| `runner-install.sh` | Register a free VM (07) as a self-hosted runner for unlimited minutes |
| `README.md` | Steps |

## Where these live
GitHub Actions reads workflows from the repo root: copy this folder's `.github/`
into your project root (or keep this whole repo and let them run from here).

## Secrets to set (Settings > Secrets and variables > Actions)
`CLOUDFLARE_API_TOKEN`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
`NEON_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`,
`EMAIL_FROM`, `EMAIL_ALERT_TO`, `B2_KEY_ID`, `B2_APP_KEY`
