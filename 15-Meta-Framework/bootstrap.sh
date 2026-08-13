#!/usr/bin/env bash
# bootstrap.sh - one-shot bootstrap of the whole free stack.
# 1) copies .env.example -> .env (won't overwrite), 2) checks tools,
# 3) prints next steps. Safe to run any time.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== FreeStack bootstrap =="

# 1. env
if [ ! -f .env ]; then
  cp .env.example .env
  echo ">> created .env from .env.example"
  echo ">>  EDIT IT NOW: fill at least OPENROUTER_API_KEY, RESEND_API_KEY, CLOUDFLARE_API_TOKEN"
else
  echo ">> .env exists (kept as-is)"
fi

# 2. tools
missing=0
for tool in python3 curl git; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "   [ok]   $tool: $(command -v "$tool")"
  else
    echo "   [MISS] $tool"
    missing=1
  fi
done
for tool in docker node npm npx rclone wrangler gcloud oci; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "   [ok]   $tool"
  else
    echo "   [opt]  $tool (not installed - needed only for the folder that uses it)"
  fi
done

echo ""
echo "== next steps =="
echo "  1. vim .env                     # keys"
echo "  2. bash 15-Meta-Framework/audit.sh"
echo "  3. bash 07-Cloud-VMs-Compute/...  # provision free VMs"
echo "  4. bash 13-Functions-Serverless/api/setup.sh"
echo "  5. bash 10-Git-CICD/runner-install.sh   # if you want unlimited CI"
echo "  6. crontab 15-Meta-Framework/crontab.example"
echo ""
exit "$missing"
