#!/usr/bin/env bash
# deploy-all.sh - deploy every deployable piece in one go.
# Each step is independent (wraps each folder's own deploy script).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ENV_FILE=".env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

run() { echo ""; echo ">> $1"; shift; "$@"; echo "   done."; }

run "deploy static site (01)"  bash 01-Websites/deploy-static.sh
run "deploy r2-worker (08)"    bash -c "cd 08-Object-Storage/r2-worker && npm ci && npx wrangler deploy"
run "deploy functions api (13)" bash 13-Functions-Serverless/api/setup.sh

echo ""
green() { printf "\033[32m%s\033[0m\n" "$1"; }
green "== all deployed. Update DNS + monitoring next (12, 11). =="
