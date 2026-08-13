# FreeStack

Run websites, MCP servers, SSH tunnels, APIs, databases, AI, email, and more **at $0/month** — with real, runnable setup code.

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](https://opensource.org/licenses/MIT)
[![Shell](https://img.shields.io/badge/Shell-Bash%20%2B%20PowerShell-blue.svg)](#)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6.svg)](https://www.typescriptlang.org/)
[![Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Workers-orange.svg)](https://workers.cloudflare.com/)
[![Zero Cost](https://img.shields.io/badge/Cost-$0%2Fmo-brightgreen.svg)](#)

Everything here is a self-contained "run it free" kit: a researched `FRAMEWORK.md` plus working scripts, configs, templates, and apps that make it happen. No fluff, no locked-in services — escape hatches everywhere.

## What's inside

```
00-MasterList          A-Z index of ~150 free services
01-Websites            Static + dynamic hosting deploy kits
02-MCP-Servers         Runnable MCP servers (TS + Python) + deploy scripts
03-SSH-Tunnels         Tunnel one-liners, wrappers, self-hosted sish
04-APIs                Free-API catalog + caching Worker router
05-LLM-AI              Multi-provider failover LLM router + Ollama self-host
06-Databases           Keep-alive, backup automation, self-host Postgres
07-Cloud-VMs-Compute   Oracle/GCP always-free VM provisioning + hardening
08-Object-Storage      rclone + R2/B2 private-bucket serving
09-Email               Resend/SMTP send scripts + domain mail loop
10-Git-CICD            GitHub Actions workflows (deploy/cron/backup)
11-Monitoring-Analytics  Better Stack + Healthchecks + Uptime Kuma kits
12-Domains-DNS         is-a.dev generator + Cloudflare DNS + DuckDNS
13-Functions-Serverless  Complete Cloudflare Worker API project
14-Search-Data         RAG pipeline + Meilisearch compose
15-Meta-Framework      Whole-stack bootstrap + free-tier audit
```

## Features

- **~150 free services cataloged** (`00-MasterList`) with the free tier that actually works.
- **Multi-provider LLM failover router** (`05-LLM-AI`) — hits OpenRouter → Groq → Cerebras → Gemini → Mistral on 429/timeout, zero cost.
- **Free-API router** (`04-APIs`) — weather, crypto, FX, geo, news behind a caching Cloudflare Worker.
- **Always-free compute** (`07`) — Oracle Arm VM (2 vCPU / 12 GB / 200 GB) + GCP e2-micro provisioning and hardening.
- **Self-hosted everything** — Postgres, Meilisearch, Uptime Kuma, and sish tunnels via `docker compose`.
- **Automated backups & keep-alives** (`06`, `08`) — nightly `pg_dump` → R2, so free tiers never snooze.
- **Zero lock-in** — Postgres (`pg_dump`), S3-compatible (`rclone`), OpenAI-compatible (router), and git. Every escape hatch included.
- **No card required** — every account is free; only a real `.com` TLD (~$10/yr) is optional, and `is-a.dev` removes even that.

## Order of operations (the professional rollout)

Phase 0 — accounts (5 min each, all free, most no card):
`Cloudflare` → `GitHub` → `Neon` (or Supabase) → `OpenRouter` → `Resend`

Phase 1 — identity & edge (12):
`is-a.dev` subdomain → add to Cloudflare DNS

Phase 2 — compute (07):
Oracle Always Free VM (2 Arm / 12GB / 200GB) + Google e2-micro

Phase 3 — data (06 + 08):
Neon database → keep-alive → nightly backups to R2

Phase 4 — apps (01 + 13 + 02):
Cloudflare Pages site → Worker API → MCP servers

Phase 5 — glue (10 + 11):
GitHub Actions (deploy/cron/backup) → Better Stack + Healthchecks watching everything

Phase 6 — the meta (15):
`bootstrap.sh` provisions the rest; `audit.sh` re-verifies free tiers quarterly.

## How to run a folder kit

Each folder has a `README.md` with exact commands. Scripts are idempotent and safe to re-run. Where a service requires a real account, scripts stop and print the 2-minute signup step instead of failing silently.

```bash
# Clone and jump into a kit
git clone <your-url> FreeStack
cd FreeStack/05-LLM-AI
cp ../.env.example ../.env   # fill in keys
python llm_router.py "hello from $0/month"
```

## The rules of the road

- Free tiers mutate. `15-Meta-Framework/audit.sh` re-checks every quarter.
- Nothing locks you in: Postgres (`pg_dump`), S3-compatible (`rclone`), OpenAI-compatible (router), git. Escape hatches everywhere.
- The ONLY recurring cost in this entire stack is a real `.com` TLD if you ever want one (~$10/yr). `is-a.dev` removes even that.

## Repo layout notes

- `.sh` scripts target Linux (the free VMs / GitHub Actions).
- `.ps1` scripts target Windows (your machine).
- `.github/` at the root is meant to be copied into a real GitHub repo.
- Every script reads secrets from `../.env` (never hardcoded). See `.env.example`.

## License

MIT
