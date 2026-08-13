# 07 — Free Cloud VMs: always-free compute

Two genuinely always-free boxes:

| Provider | Spec | Fine print |
|---|---|---|
| Oracle Cloud | **4 OCPU + 24GB RAM** (2x A1.Flex) + 200GB disk + 10TB egress | Requires card at signup (never charged). The free A1 arm instances. |
| Google Cloud | **e2-micro** (0.25 vCPU / 1GB) + 30GB disk + 1GB egress | Free in us-west1/us-central1/us-east1 only. Billing account required. |

| File | Purpose |
|---|---|
| `oracle-provision.py` | Creates the free Oracle A1 instance + VCN/NSG/firewall via oci CLI |
| `gcp-create.sh` | Creates the e2-micro via gcloud |
| `bootstrap-server.sh` | Harden + dockerize either box: SSH keys, firewall, fail2ban, Docker, watchtower, cron for backups |
| `README.md` | Steps |

## The plan
1. Oracle = your workhorse (Postgres 06, Ollama 05, Meilisearch 14, n8n, uptime-kuma 11).
2. GCP e2-micro = the watchdog that monitors everything with Upptime/BetterStack and takes over if Oracle dies.
3. `bootstrap-server.sh` on both -> idempotent hardening + docker.

## 10-minute setup
```bash
# Oracle
bash -c "$(curl -fsSL https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
oci setup config            # paste your API key (console > your profile > API keys)
python3 oracle-provision.py --ssh-key ~/.ssh/id_ed25519.pub

# GCP
gcloud auth login
bash gcp-create.sh

# both, once IPs are up:
ssh ubuntu@<oracle-ip> 'bash -s' < bootstrap-server.sh
ssh <gcp-user>@<gcp-ip> 'bash -s' < bootstrap-server.sh
```
Then run your stacks: 06, 05, 11, 14.
