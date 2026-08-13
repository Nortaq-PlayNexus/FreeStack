# FRAMEWORK: Free Websites (Static + Dynamic)
Last researched: 2026-08-12 | Tier: 100% free, no credit card for static path

## GOAL
A permanent, live website at $0/month. Two tiers:
- STATIC (HTML/CSS/JS or a static-site framework) -> effectively unlimited, best-in-class.
- DYNAMIC (server-side code: Flask, Node, PHP, Django) -> free with sleep/cold-start trade-offs.

## RULE 1: Default to STATIC
Static sites are 100% solved. No bandwidth anxiety. Hosting static files costs providers ~nothing, so the free tiers are effectively permanent.

## THE FREE MATRIX (Static)
| Host | Free quota | Bandwidth | Builds | Custom domain | SSL |
|---|---|---|---|---|---|
| Cloudflare Pages | Unlimited sites | UNLIMITED | 500/mo | 100/project | Auto |
| GitHub Pages | 1GB/site | 100GB/mo (soft) | 10/hr | Yes | Auto |
| Netlify | Credit pool | ~100GB/mo | 300 min/mo | Yes | Auto |
| Vercel | 100GB/mo | 100GB/mo | 6000 min/mo | Yes | Auto |
| Render (static) | Unlimited | included | git-push | Yes | Auto |

WINNER: **Cloudflare Pages** - only major host with NO bandwidth cap. Free DDoS protection + privacy analytics + 300-city CDN.

## THE FREE MATRIX (Dynamic)
| Platform | Free tier | Cold start | Card | Notes |
|---|---|---|---|---|
| Render (web service) | 750 hr/mo (~1 service 24/7) | 30-50s after 15min idle | No | Postgres free 30 days |
| Cloudflare Workers | 100k req/day, 10ms CPU | ~0ms | No | Serverless, edge |
| Cloudflare Pages Functions | 100k req/day | ~0ms | No | Add logic to static |
| SnapDeploy | 4 containers 512MB/0.25vCPU, 10 deploys/day | 10-30s | No | Auto-sleep/wake |
| dployr Hobby | 1 workload 64MB/0.1vCPU/10GB | sleeps | No | free forever |
| Vercel Functions | 100GB-hrs/mo | ~250ms | No | 10s function timeout |
| Netlify Functions | 125k/mo | ms | No | 10s timeout |
| Koyeb | 1 service 0.1 vCPU | scale-to-zero | No | |
| Railway | $5 one-time + $1/mo credit | none | No | Not sustainable long-term |
| PythonAnywhere | 1 web app | - | No | Free tier |

## FRAMEWORK: Static site -> live in ~20 min
1. Build static output (plain HTML, or a framework: Astro, Hugo, Jekyll, Vite, Next.js export).
2. Push code to a GitHub repo (free, unlimited public repos).
3. Go to pages.cloudflare.com -> Create project -> Connect GitHub repo -> Cloudflare auto-detects the framework, builds, deploys.
4. Site is live at `https://<project>.pages.dev` with automatic HTTPS.
5. (Optional) Add your own domain in Pages -> Custom domains -> Add. Free SSL auto-provisioned.
6. Every `git push` auto-redeploys. Use deploy previews for PRs.

## FRAMEWORK: Dynamic app -> free
1. Containerize with a Dockerfile (or rely on auto-detect: Render detects Node/Python/Ruby/Go/Rust/Elixir).
2. Deploy to Render web service (git-push), start command e.g. `gunicorn app:app`.
3. Accept the free-tier contract: spins down after 15 min idle, ~1 min wake. Keep it alive with Upptime (see 11-Monitoring-Analytics) or accept cold starts.
4. For edge/low-latency: Cloudflare Workers. For 24/7 without sleep: you are asking for "fullest power" -> see 15-Meta-Framework for the always-on VPS path (Oracle/Google free VMs).

## THE META (no-free-tier escape)
Truly always-on dynamic hosting with no free tier does NOT exist in the "sleep-free, unlimited" category from these hosts. Escape path: get a permanently free always-on VM (Oracle Cloud Always Free: 2 Arm cores / 12GB RAM / 200GB disk) -> run your own Docker / nginx / anything -> expose via free tunnel or Cloudflare DNS (see 07-Cloud-VMs-Compute + 03-SSH-Tunnels).

## GOTCHAS
- Vercel free tier is for NON-COMMERCIAL use.
- Netlify new accounts: 300 credits/mo pool; exceeding suspends the site (no auto-bill).
- GitHub Pages free = public repos only.
- Render free Postgres EXPIRES after 30 days; don't build on it.
- Cloudflare Pages: 100 projects/account cap; 20,000 files/site on free plan.
- All dynamic free tiers sleep or cold-start; plan for it.

## WATCH OUT (dead or trap services as of 2026)
- Fly.io: no free tier for new users (card required).
- Railway: $5 trial credit, then $1/mo - not a permanent free host.
- PlanetScale: removed free tier entirely (a warning for all of these).
