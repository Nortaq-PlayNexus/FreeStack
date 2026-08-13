#!/usr/bin/env bash
# duckdns.sh - update DuckDNS dynamic DNS. Run every 5 min from cron.
# Set DUCKDNS_DOMAIN + DUCKDNS_TOKEN in ../.env (free at duckdns.org).
# crontab:  */5 * * * * bash ~/freestack/12-Domains-DNS/duckdns.sh
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${DUCKDNS_DOMAIN:?Set DUCKDNS_DOMAIN (no .duckdns.org suffix) in ../.env}"
: "${DUCKDNS_TOKEN:?Set DUCKDNS_TOKEN in ../.env}"

curl -fsS "https://www.duckdns.org/update?domains=$DUCKDNS_DOMAIN&token=$DUCKDNS_TOKEN&ip=" \
  | grep -q OK && echo "duckdns OK" || echo "duckdns FAILED"
