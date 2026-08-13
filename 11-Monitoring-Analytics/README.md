# 11 — Free Monitoring & Analytics

| Provider | Free tier | Role |
|---|---|---|
| Better Stack | 10 monitors, 3-min checks | Uptime from THEIR infra (survives your box dying) |
| Healthchecks.io | unlimited checks | Dead-man-switch for cron/backups (04, 06, 10) |
| Uptime Kuma | self-hosted, unlimited | Full monitoring + status page on your free VM (07) |
| Cloudflare Web Analytics | unlimited | Privacy-first site analytics (free, no GDPR banner) |
| Sentry | 5k events/mo | Error tracking for the Python/JS services |
| umami | self-hosted | Google-Analytics-style, self-hosted |

| File | Purpose |
|---|---|
| `betterstack.yml` | Configuration for Better Stack Uptime (monitors all free services) |
| `healthchecks.py` | CLI to start/end Healthchecks.io pings (wrap any job) |
| `kuma-compose.yml` | Uptime Kuma self-hosted on the free VM |
| `cloudflare-analytics.html` | Drop-in snippet for site analytics |
| `README.md` | Steps |

## Quick start
```bash
# Better Stack (external, survives outages):
#   1. signup betterstack.com/uptime (free 10 monitors)
#   2. set BETTERSTACK_UPTIME_TOKEN in ../.env
python3 betterstack-deploy.py          # creates monitors from betterstack.yml

# Healthchecks.io (dead-man-switch for your cron jobs):
python3 healthchecks.py --start        # at job start
python3 healthchecks.py --success      # at job success
python3 healthchecks.py --fail "msg"   # at job failure
# flip UNABLE_TO_IMPORT fix: set HEALTHCHECKS_PING_KEY in ../.env

# Uptime Kuma (self-hosted):
docker compose -f kuma-compose.yml up -d   # on the free VM, then SSH-tunnel port 3001
```
