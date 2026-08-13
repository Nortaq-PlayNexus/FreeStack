#!/usr/bin/env bash
# gcp-create.sh - create the Google Cloud always-free e2-micro instance.
# Only us-west1 / us-central1 / us-east1 are always-free. Billing account required (free tier only).
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-freestack-$(echo $RANDOM | head -c 6)}"
ZONE="${GCP_ZONE:-us-central1-a}"
MACHINE="e2-micro"

echo ">> project: $PROJECT_ID (create it first at console.cloud.google.com if new)"
gcloud config set project "$PROJECT_ID"

echo ">> creating e2-micro in $ZONE..."
gcloud compute instances create freestack \
  --zone "$ZONE" \
  --machine-type "$MACHINE" \
  --image-family ubuntu-2404-lts-amd64 \
  --image-project ubuntu-os-cloud \
  --boot-disk-size 30 \
  --boot-disk-type pd-standard \
  --tags freestack-ssh

echo ">> opening firewall for ssh (22) and web (80/443)..."
gcloud compute firewall-rules create freestack-ssh \
  --allow tcp:22 --target-tags freestack-ssh || true
gcloud compute firewall-rules create freestack-web \
  --allow tcp:80,tcp:443 --target-tags freestack-ssh || true

echo ">> done. connect with:  gcloud compute ssh freestack --zone $ZONE"
echo ">> then run bootstrap-server.sh"
