#!/usr/bin/env bash
# runner-install.sh - register a free VM as a GitHub self-hosted runner.
# Gives the VM free, unlimited Actions minutes (runs on your hardware, not GitHub's).
#
# 1) Create a PAT: github.com/settings/tokens (repo scope, runner registration).
# 2) On the VM (or from laptop if SSH key available):
#    GITHUB_TOKEN=ghp_xxx REPO=you/freestack ./runner-install.sh
set -euo pipefail

GITHUB_TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN (PAT)}"
REPO="${REPO:?Set REPO as you/freestack}"
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"

mkdir -p "$RUNNER_DIR" && cd "$RUNNER_DIR"

if [ ! -f config.sh ]; then
  echo ">> downloading runner for linux x64..."
  curl -sSL -o runner.tar.gz \
    https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-2.319.1.tar.gz
  tar xzf runner.tar.gz
  rm runner.tar.gz
fi

echo ">> fetching registration token..."
# PAT scoped to repo; call API to get a runner token (works for both user and org via header)
TOKEN=$(curl -sS -X POST -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$REPO/actions/runners/registration-token" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

echo ">> configuring runner for $REPO..."
./config.sh --url "https://github.com/$REPO" --token "$TOKEN" --unattended --replace --labels freestack

echo ">> installing as a service..."
sudo ./svc.sh install && sudo ./svc.sh start
echo ">> done. Runner online at github.com/$REPO/settings/actions/runners"
echo ">> use in workflows:   runs-on: [self-hosted, freestack]"
