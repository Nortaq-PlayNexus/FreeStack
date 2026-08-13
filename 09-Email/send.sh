#!/usr/bin/env bash
# send.sh - curl-based email one-liner. Uses Resend if RESEND_API_KEY set, else Brevo.
# Usage: bash send.sh to@example.com "Subject" "<p>body</p>"
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE="../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

TO="${1:?usage: send.sh TO SUBJECT HTML}"
SUBJECT="${2:-FreeStack}"
HTML="${3:-<p>hi</p>}"
FROM="${EMAIL_FROM:?Set EMAIL_FROM in ../.env}"

if [ -n "${RESEND_API_KEY:-}" ]; then
  curl -fsS https://api.resend.com/emails \
    -H "Authorization: Bearer $RESEND_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json,sys;print(json.dumps({'from':sys.argv[1],'to':[sys.argv[2]],'subject':sys.argv[3],'html':sys.argv[4]}))" "$FROM" "$TO" "$SUBJECT" "$HTML")"
  echo ">> sent via resend"
elif [ -n "${BREVO_API_KEY:-}" ]; then
  curl -fsS https://api.brevo.com/v3/smtp/email \
    -H "api-key: $BREVO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json,sys;print(json.dumps({'sender':{'email':sys.argv[1]},'to':[{'email':sys.argv[2]}],'subject':sys.argv[3],'htmlContent':sys.argv[4]}))" "$FROM" "$TO" "$SUBJECT" "$HTML")"
  echo ">> sent via brevo"
else
  echo "Set RESEND_API_KEY or BREVO_API_KEY in ../.env" >&2
  exit 1
fi
