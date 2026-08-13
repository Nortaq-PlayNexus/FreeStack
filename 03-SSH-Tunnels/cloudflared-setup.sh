#!/usr/bin/env bash
# cloudflared-setup.sh - install cloudflared, create a named tunnel, run it as a service.
# Run on your free VM (07) or home server. Free Cloudflare account required.
set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

if ! command -v cloudflared >/dev/null; then
  echo ">> installing cloudflared..."
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
  sudo apt-get update && sudo apt-get install -y cloudflared
fi

echo ">> run: cloudflared tunnel login   (one-time browser auth)"
cloudflared tunnel login

TUNNEL_NAME="${TUNNEL_NAME:-freestack}"
cloudflared tunnel create "$TUNNEL_NAME" || true

TUNNEL_ID=$(cloudflared tunnel list | awk -v n="$TUNNEL_NAME" '$2==n{print $1}')
echo ">> tunnel id: $TUNNEL_ID"

# build config from template
sed -e "s/YOUR_TUNNEL_ID_HERE/$TUNNEL_ID/g" \
    -e "s/YOUR_DOMAIN/$DOMAIN/g" \
    "$(dirname "$0")/cloudflared-config.yml" | sudo tee /etc/cloudflared/config.yml >/dev/null

echo ">> DNS: point the hostnames at this tunnel (must be on the same Cloudflare account)"
cloudflared tunnel route dns "$TUNNEL_NAME" "app.$DOMAIN"
cloudflared tunnel route dns "$TUNNEL_NAME" "api.$DOMAIN"

sudo cloudflared service install
sudo systemctl enable --now cloudflared
echo ">> done. Status: systemctl status cloudflared"
