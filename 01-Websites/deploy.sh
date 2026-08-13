#!/usr/bin/env bash
# deploy.sh - Universal static deployer.
# Picks Cloudflare Pages (default, unlimited bandwidth) unless DEPLOY_TARGET=vercel|netlify.
# All three are free, no card. See FRAMEWORK.md for the matrix.
set -euo pipefail

cd "$(dirname "$0")"
TARGET="${DEPLOY_TARGET:-cloudflare}"
echo ">> deploying to: $TARGET"

case "$TARGET" in
  cloudflare) bash deploy-cloudflare.sh ;;
  vercel)     npx vercel --yes --prod "$PWD/site" ;;
  netlify)    npx netlify deploy --dir site --prod ;;
  *) echo "unknown target: $TARGET (cloudflare|vercel|netlify)"; exit 1 ;;
esac
