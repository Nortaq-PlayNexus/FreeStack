#!/usr/bin/env bash
# tunnel.sh - Linux/macOS/Git Bash: expose a local port publicly with zero install.
# Usage: ./tunnel.sh 8080            (localhost.run)
#        ./tunnel.sh 8080 serveo     (serveo.net)
#        ./tunnel.sh 8080 cloudflared (needs cloudflared)
set -euo pipefail

PORT="${1:?usage: tunnel.sh PORT [localhostrun|serveo|mekong|cloudflared]}"
PROVIDER="${2:-localhostrun}"
TARGET="localhost:${PORT}"

case "$PROVIDER" in
  localhostrun) ssh -R "80:${TARGET}" nokey@localhost.run ;;
  serveo)       ssh -R "80:${TARGET}" serveo.net ;;
  mekong)       ssh -t -R "80:${TARGET}" proxy.angkorsearch.dev ;;
  cloudflared)
    command -v cloudflared >/dev/null || { echo "install: brew install cloudflared"; exit 1; }
    cloudflared tunnel --url "http://${TARGET}" ;;
  *) echo "unknown provider: $PROVIDER"; exit 1 ;;
esac
