#!/usr/bin/env bash
# test.sh - smoke test the deployed Worker.
# Usage: URL=https://freestack-api.<you>.workers.dev TOKEN=<token> bash test.sh
set -euo pipefail

URL="${URL:?Set URL (your worker URL)}"
TOKEN="${TOKEN:?Set TOKEN (API_TOKEN from wrangler.toml)}"

echo ">> healthz:"
curl -fsS "$URL/healthz"; echo

echo ">> create item:"
curl -fsS -X POST "$URL/api/items" -H "authorization: Bearer $TOKEN" -H "content-type: application/json" \
  -d '{"name":"smoke test '"$(date +%s)"'"}'; echo

echo ">> list items:"
curl -fsS "$URL/api/items"; echo

echo ">> upload file:"
echo "hello from freestack" | curl -fsS -X PUT "$URL/api/files/hello.txt" -H "authorization: Bearer $TOKEN" \
  -H "content-type: text/plain" --data-binary @-; echo

echo ">> fetch file:"
curl -fsS "$URL/api/files/hello.txt"; echo

echo ">> unauthorized write (expect 401):"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$URL/api/items" -H "content-type: application/json" -d '{"name":"x"}'
