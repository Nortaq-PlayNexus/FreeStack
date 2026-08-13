#!/usr/bin/env bash
# audit.sh - live status of the whole stack: keys set, services reachable, quotas.
# Reads ../.env; never prints secret VALUES, only whether they're set.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red()   { printf "\033[31m%s\033[0m\n" "$1"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$1"; }

echo "== keys (.env) =="
for k in OPENROUTER_API_KEY GROQ_API_KEY CEREBRAS_API_KEY GEMINI_API_KEY MISTRAL_API_KEY \
         RESEND_API_KEY BREVO_API_KEY CLOUDFLARE_API_TOKEN CF_ACCOUNT_ID CF_ZONE_ID \
         R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY B2_KEY_ID B2_APP_KEY \
         NEON_DATABASE_URL SUPABASE_URL TURSO_DATABASE_URL \
         BETTERSTACK_UPTIME_TOKEN HEALTHCHECKS_PING_KEY DUCKDNS_DOMAIN DUCKDNS_TOKEN; do
  if [ -n "${!k:-}" ]; then green "   [set]   $k"; else yellow "   [empty] $k"; fi
done

echo ""
echo "== local services =="
for probe in "ollama|http://localhost:11434/api/tags" "meilisearch|http://localhost:7700/health" "uptime-kuma|http://localhost:3001"; do
  name="${probe%%|*}"; url="${probe##*|}"
  if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then green "   [up]    $name"; else red "   [down]  $name"; fi
done

echo ""
echo "== remote (free) services =="
check_url() { # name url
  if curl -fsS --max-time 10 "$2" >/dev/null 2>&1; then green "   [up]   $1"; else red "   [down] $1"; fi
}
[ -n "${FREESTACK_API_URL:-}" ] && check_url "freestack-api" "$FREESTACK_API_URL/healthz" || true
check_url "openrouter" "https://openrouter.ai/api/v1/models"
check_url "betterstack" "https://uptime.betterstack.com/api/v2/monitors"

echo ""
echo "== quota reminders =="
echo "   Cloudflare Workers  100k req/day | D1 5GB | KV 10M reads | R2 10GB, 0 egress"
echo "   GitHub Actions      2000 min/mo  | cron = free scheduler"
echo "   Resend              3000/mo 100/day"
echo "   Better Stack        10 monitors 3-min checks"
echo "   Oracle A1           4 OCPU/24GB RAM/200GB disk (always free)"
echo "   GCP e2-micro        0.25 vCPU/1GB (us-west1/central1/east1)"
echo "   OpenAI/Groq/etc     per-provider free tiers (see 04/catalog)"
