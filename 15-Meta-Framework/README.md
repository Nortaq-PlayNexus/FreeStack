# 15 — Meta-Framework: the glue that runs the whole free stack

Everything in this repo is independent; this folder ties it together.

| File | Purpose |
|---|---|
| `bootstrap.sh` | One-shot: checks prerequisites, generates `.env` from `.env.example`, runs every `setup.sh` |
| `audit.sh` | Prints a live status table: which keys are set, which services are reachable, quotas |
| `deploy-all.sh` | Deploys everything deployable (site, workers, R2 worker, API) with one command |
| `crontab.example` | All the cron lines the stack needs (keepalive, backup, duckdns, healthchecks) |
| `README.md` | The map |

## The map (how folders connect)
```
15-meta (bootstrap/audit/deploy)
 |-- 01-Websites        static site + deploy to Pages/Render
 |-- 02-MCP-Servers     tools for LLM agents
 |-- 03-SSH-Tunnels     public URL for your VM's private services
 |-- 04-APIs            catalog + router for free APIs
 |-- 05-LLM-AI          free LLM clients + router + self-hosted Ollama
 |-- 06-Databases       keepalives, backups, self-hosted Postgres
 |-- 07-Cloud-VMs       the two free VMs + hardening
 |-- 08-Object-Storage  R2/B2 + rclone + private-bucket worker
 |-- 09-Email           transactional email with failover
 |-- 10-Git-CICD        GitHub Actions as free cron + pipeline
 |-- 11-Monitoring      BetterStack/Healthchecks/Kuma/analytics
 |-- 12-Domains-DNS     is-a.dev + Cloudflare DNS + DuckDNS
 |-- 13-Functions       full Workers API (D1/KV/R2/cron)
 `-- 14-Search-Data     Meilisearch + RAG over your docs
```

## First run
```bash
bash 15-Meta-Framework/bootstrap.sh     # guided; creates .env and walks setup steps
bash 15-Meta-Framework/audit.sh         # after setup, shows what's live
crontab 15-Meta-Framework/crontab.example   # schedule the keepalive/backup jobs
```
