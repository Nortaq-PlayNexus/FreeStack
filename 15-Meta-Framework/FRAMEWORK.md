# META-FRAMEWORK: The Zero-Cost Stack (when no free tier exists)
Last researched: 2026-08-12

## THE PROBLEM
No single provider offers "free forever at fullest power" for everything. The people who run real things for $0 don't use one free tier - they combine ~10 free resources so each limit never bites. This file is the operating system for the whole FreeStack.

## THE 6 LAWS OF RUNNING THINGS FREE
1. **Static beats dynamic.** Anything precomputable (HTML, JSON, binaries) is hosted free with no real limits (Cloudflare Pages, R2, GitHub Releases). Move work off the request path.
2. **The free VM is the power lever.** Oracle Cloud Always Free (2 Arm cores / 12GB RAM / 200GB disk) + Google e2-micro give you REAL always-on compute. Everything with "no free tier" (big servers, databases, self-hosted apps) becomes free once it runs there.
3. **Edge does the cheap work.** Cloudflare free (Workers, KV, D1, R2, CDN, cache, DNS, email routing, analytics) absorbs 100k requests/day at $0 and caches the rest.
4. **Rotate budgets.** Every provider gives a separate free quota. Split load across Cloudflare + Cloud Run + Lambda + Neon + Turso + Groq + OpenRouter... a "limit" is only a limit if you put all your traffic on one.
5. **Cache, batch, compress.** Cache hits don't count. Batched jobs (GitHub Actions cron) run outside your request quotas. Compressed data fits free storage.
6. **A $0 stack needs a watchman.** Free things sleep, expire, and go down. Upptime + Healthchecks.io + Better Stack (free tiers) watch your stack and tell you when something rotated away.

## THE REFERENCE STACK (everything together, everything free)
```
DOMAIN:     yourname.is-a.dev  (12)
DNS/CDN:    Cloudflare free plan -> SSL, DDoS, CDN, email routing  (12)
WEBSITE:    Cloudflare Pages / GitHub Pages  (01)
DYNAMIC:    Render web service (750h) OR your Oracle VM  (01 / 07)
API/MCP:    Cloudflare Workers (100k req/day)  (13 / 02)
DATABASE:   Neon Postgres (free) + Turso for edge/SQLite  (06)
VECTOR/RAG: pgvector on Neon + free embedding APIs  (14 / 05)
STORAGE:    Cloudflare R2 10GB zero-egress  (08)
EMAIL:      Resend (3k/mo send) + Cloudflare Email Routing (receive)  (09)
LLM/AI:     OpenRouter free models / Kilo (no key) / self-host Ollama  (05)
COMPUTE:    Oracle Always Free VM - Docker host for the rest  (07)
TUNNELS:    Cloudflare Tunnel / ssh -R  (03)
CI/CRON:    GitHub Actions (free schedules, auto-deploy, backups)  (10)
MONITOR:    Upptime + Healthchecks + Better Stack (free)  (11)
SEARCH:     Brave 2k/mo + self-host Meilisearch on the VM  (14)
```
Total monthly cost: $0. The ONLY recurring purchase in the entire universe is a real `.com` TLD (~$10/yr) - and is-a.dev removes even that.

## WHEN A FREE TIER TRULY DOESN'T EXIST
Categories with no honest free tier: real .com TLD, GPU boxes, unlimited storage, guaranteed 99.9% SLA, dedicated IPs, always-warm big instances, SMS at scale, native Windows VMs free forever.

The meta for each:
| Need | Meta-answer |
|---|---|
| Big compute burst | Google $300 / AWS $200 / Azure $200 trial credits = big machines for 1-3 mo at $0 |
| GPU (AI training) | Colab free GPU tunneled to your VM; or buy nothing - use free hosted inference |
| >10GB storage | Oracle VM's 200GB disk + R2 for durability |
| 24/7 no-sleep dynamic | Run it on the Oracle VM (a VM never sleeps) |
| Unlimited LLM | Self-host open weights on your VM (Ollama). No quota at all |
| SMS | Twilio trial credit + email-as-fallback; or ntfy/Telegram (free push) |
| Guaranteed SLA | You don't get SLAs for free. Cross-monitor with 2 providers and auto-failover |
| .com domain | is-a.dev is free; buy a TLD only when revenue exists |

## THE FAIL-SAFE (when a free service dies - they do)
1. Everything in this stack is chosen for PORTABILITY: Postgres (Neon/Supabase/Turso/Cockroach - pg_dump works), S3-compatible (R2/B2/IDrive), git (GitHub/GitLab/Codeberg), OpenAI-compatible LLM endpoints. Nothing locks you in.
2. Keep a weekly automated export: GitHub Actions dumps DB -> R2 + your repo. If any provider vanishes, restore elsewhere in an afternoon.
3. Follow the rule: free tier = never your only copy, never your single point of failure.

## DECISION TREE (which folder to use)
- Need a website? -> 01. Need it to never sleep? -> 07 VM + tunnel.
- Need AI agents/MCP? -> 02 (hosting) + 05 (models) + 14 (search/RAG).
- Need to receive webhooks? -> 03 tunnel or 13 Worker.
- Need to store user data? -> 06 DB + 08 files.
- Need to send mail? -> 09.
- Need to stay alive? -> 11.
- Need a name? -> 12.
- Need to automate? -> 10.
- Everything else -> 04 APIs, then this file.

## AUDIT EVERY 3 MONTHS
Free tiers mutate (PlanetScale died, Fly.io killed its free tier, Firebase dropped free storage). Re-check the four the whole stack leans on: Cloudflare free plan, Oracle Always Free, GitHub free, Neon free. If any changes, this meta's portability rules make the move cheap.
