#!/usr/bin/env bash
# bootstrap-server.sh - harden + dockerize a fresh Ubuntu VM. Idempotent; run as root.
# Usage (from your laptop):  ssh ubuntu@<ip> 'sudo bash -s' < bootstrap-server.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root:  ssh ubuntu@<ip> 'sudo bash -s' < bootstrap-server.sh"
  exit 1
fi

SSH_USER="${SSH_USER:-ubuntu}"
cd /root

export DEBIAN_FRONTEND=noninteractive
echo ">> apt update/upgrade (this can take a while)..."
apt-get update -y && apt-get upgrade -y

echo ">> installing base tools..."
apt-get install -y curl git htop tmux ufw fail2ban unattended-upgrades ca-certificates gnupg

echo ">> hardening SSH: disable password auth + root login..."
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

echo ">> enabling unattended upgrades (auto security patches)..."
echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";' > /etc/apt/apt.conf.d/20auto-upgrades

echo ">> firewall: allow 22/80/443 only..."
ufw default deny incoming
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
echo "y" | ufw enable

echo ">> fail2ban: ban after 5 failed SSH attempts..."
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
[sshd]
enabled = true
EOF
systemctl enable --now fail2ban

echo ">> installing Docker Engine + compose plugin..."
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "$SSH_USER"
fi

echo ">> installing docker compose..."
apt-get install -y docker-compose-plugin || true
docker compose version || true

echo ">> watchtower: auto-update containers weekly..."
docker run -d --name watchtower --restart=unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower --schedule "0 4 * * 1" --cleanup || true

echo ">> swap (256MB) so the e2-micro/1GB-box doesn't OOM..."
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 512M /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo ""
echo "== bootstrap complete =="
echo "  next: run your stacks, e.g."
echo "    docker compose -f freestack/06-Databases/postgres-compose.yml up -d"
echo "    bash freestack/05-LLM-AI/ollama-setup.sh"
echo "    docker compose -f freestack/11-Monitoring-Analytics/uptime-kuma-compose.yml up -d"
