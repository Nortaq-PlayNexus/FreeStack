#!/usr/bin/env bash
# client.sh - example calls against your free API router.
# Replace BASE with your deployed worker URL.
set -euo pipefail
BASE="${BASE:-https://api-router.YOUR_SUBDOMAIN.workers.dev}"

echo "== weather (open-meteo, no key) =="
curl -s "$BASE/v1/weather/open_meteo/?latitude=40.7&longitude=-74&current=temperature_2m"

echo
echo "== weather (weatherapi with key fallback) =="
curl -s "$BASE/v1/weather/weatherapi/?q=London"

echo
echo "== crypto =="
curl -s "$BASE/v1/crypto/coingecko/bitcoin" | head -c 300

echo
echo "== fx =="
curl -s "$BASE/v1/fx/frankfurter/latest?from=USD&to=EUR"

echo
echo "== news =="
curl -s "$BASE/v1/news/gnews/?q=technology&max=2"
echo
