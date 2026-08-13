#!/usr/bin/env bash
# verify.sh - add SPF / DMARC / MX email-authentication records to Cloudflare DNS.
# Needed by Resend, Brevo, Mailgun, etc. for inbox (not spam) delivery.
# Requires: CLOUDFLARE_API_TOKEN + CF_ZONE_ID in ../.env (free Cloudflare zone, see 12).
#
# NOTE: DKIM records are per-provider (Resend: Dashboard > Domains > Add records,
# or API). After adding this zone to Resend, click "Add records" there - it self-verifies.
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in ../.env}"
: "${CF_ZONE_ID:?Set CF_ZONE_ID in ../.env}"

API="https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records"
AUTH="Authorization: Bearer $CLOUDFLARE_API_TOKEN"
CONTENT_TYPE="Content-Type: application/json"

add() { # name type content [priority]
  local name="$1" type="$2" content="$3" prio="${4:-}"
  local body
  if [ -n "$prio" ]; then
    body=$(python3 -c "import json,sys;print(json.dumps({'type':sys.argv[1],'name':sys.argv[2],'content':sys.argv[3],'priority':int(sys.argv[4]),'ttl':1}))" "$type" "$name" "$content" "$prio")
  else
    body=$(python3 -c "import json,sys;print(json.dumps({'type':sys.argv[1],'name':sys.argv[2],'content':sys.argv[3],'ttl':1}))" "$type" "$name" "$content")
  fi
  curl -fsS -X POST "$API" -H "$AUTH" -H "$CONTENT_TYPE" -d "$body" >/dev/null \
    && echo "  added $type $name -> $content" || echo "  FAILED $type $name"
}

echo ">> adding SPF + DMARC (name '' = zone root, e.g. yourname.is-a.dev)..."

add "" "TXT" "v=spf1 include:_spf.resend.com ~all"
add "" "TXT" "v=DMARC1; p=none; rua=mailto:admin@${EMAIL_FROM#*@}"

echo ""
echo ">> done. Next steps:"
echo "   1. In Resend: Dashboard > Domains > Add domain. It shows 3 DKIM CNAME records -"
echo "      run for each:  bash add-record.sh <name> CNAME <value>"
echo "   2. Resend verifies automatically once the records resolve (usually < 1 min)."
echo "   3. Repeat in Brevo if you use it as a fallback provider."
