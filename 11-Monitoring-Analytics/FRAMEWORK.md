# FRAMEWORK: Free Monitoring, Uptime, Analytics & Alerts
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Know when your free-stack services go down, verify scheduled jobs ran, and see real website analytics - without paying.

## UPTIME MONITORING (check endpoints)
| Tool | Model | Free tier | Needs server? |
|---|---|---|---|
| Upptime | GitHub Actions + Issues + Pages | free forever | NO (pure GitHub) |
| Healthchecks.io | dead-man-switch (cron pings) | free tier | NO |
| Better Stack | hosted uptime | 10 monitors / 3-min checks | NO |
| UptimeRobot | hosted | 50 monitors / 5-min | NO |
| Uptime Kuma | self-hosted, 90+ notifiers | free (MIT) | YES - free VM |
| Gatus | self-hosted, config-in-YAML | free | YES - free VM |
| Statping-ng | self-hosted status pages | free | YES - free VM |

## ANALYTICS (privacy-first, free)
| Tool | Free tier |
|---|---|
| Cloudflare Web Analytics | free, unlimited, no cookie banner |
| Plausible | self-host free (or hosted trial) |
| Umami | self-host free |
| GoatCounter | free for non-commercial |
| PostHog | 1M events/mo free |
| Grafana Cloud | 10k metrics, 50GB logs, 14d retention free |
| Logtail / Better Stack telemetry | free tiers |

## FRAMEWORK A: Upptime (zero-infrastructure status page, ~10 min)
1. Fork github.com/upptime/upptime.
2. Edit `.upptimerc.yml`: list your URLs (sites, APIs, MCP endpoints).
3. GitHub Actions checks every 5 min, opens/closes GitHub Issues on outage, commits response-time history, and publishes a status page on GitHub Pages.
4. Add Slack/Discord/email notifications via the config.
5. 100% free, entirely on GitHub's free tier (2,000 Actions min/mo is plenty for ~5 sites at 5-min intervals).

## FRAMEWORK B: Healthchecks for cron verification
1. Create a check on healthchecks.io (or self-host on free VM).
2. Your cron/scrapers/backup scripts `curl https://hc-ping.com/<uuid>` on success.
3. If a ping doesn't arrive on time -> email/Slack/Discord/Telegram alert.
4. Use it to keep your free Supabase DB awake too: a periodic ping keeps the project from pausing (see 06).

## FRAMEWORK C: Uptime Kuma on the free Oracle VM (full power)
1. On your always-free VM (07): `docker run -d -p 3001:3001 --name kuma -v kuma-data:/app/data louislam/uptime-kuma`.
2. Web UI at `http://<vm-ip>:3001`. Add monitors (HTTP, TCP, ping, cert expiry, DNS, DB).
3. 90+ notification channels. Public status page built in.
4. Run a SECOND instance on another free box to cross-monitor the first (a monitor that dies silently is not a monitor).

## THE META (want monitoring without a monitor box?)
Every uptime product needs SOMEONE to do the checking. If you have zero servers: Upptime (GitHub) + Healthchecks.io + Better Stack free tiers give you three independent free monitors watching from different networks - more reliable than one paid one.

## GOTCHAS
- Free hosted monitors: check intervals are coarse (3-5 min) - acceptable for free-stack services.
- GitHub Actions free = public repo for Pages; keep the repo public or accept no status page.
- Better Stack free: 10 monitors, 3-min interval, limited SMS/phone (email + Slack free).
- Self-hosted monitors die with their host - cross-monitor with a second location.
- Cloudflare analytics needs a Cloudflare account + your site behind/pointed at Cloudflare (free).
