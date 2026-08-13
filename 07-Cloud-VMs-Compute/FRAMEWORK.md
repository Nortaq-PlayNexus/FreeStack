# FRAMEWORK: Free Cloud VMs & Always-On Compute
Last researched: 2026-08-12 | Tier: free forever (2 winners) / 6-12mo trials (rest)

## GOAL
A permanently-on server you fully control (SSH, Docker, anything), at $0/month.

## THE ONLY TWO TRULY FREE-FOREVER BOXES
| Provider | Specs | Duration | Card |
|---|---|---|---|
| **Oracle Cloud Always Free** | 2 Arm Ampere OCPU + 12GB RAM always-on (or 4 OCPU for half month), 200GB block storage, 10TB/mo egress. Plus 2 AMD micro VMs | FOREVER | Yes (verify only, not charged) |
| **Google Cloud Free Tier** | 1 e2-micro (2 shared vCPU burst, 1GB RAM), 30GB disk | FOREVER | Yes |

Oracle is the clear winner: the 12GB RAM Arm instance is a real server. Runs Docker, nginx, Postgres, Ollama (7B models), a tunnel endpoint (sish), multiple apps - all on one box, all free.

## TIME-LIMITED (useful bursts of full power)
| Provider | Credit | Duration | Card |
|---|---|---|---|
| Google Cloud trial | $300 | 90 days | Yes |
| Oracle trial | $300 | 30 days | Yes |
| AWS Free | $100 + up to $100 more | 6 months (new accounts) | Yes |
| Azure Free | $200 | 30 days | Yes |
| DigitalOcean | $200 | 60 days | Yes |
| GitHub Student Pack | $200 DO + $100 Azure | while student | - |

## FRAMEWORK: Oracle Always Free VM (the "fullest power free" box)
1. Sign up at oracle.com/cloud/free. Choose home region CAREFULLY (Always Free resources only in home region).
2. Card required for identity verification - a temporary auth hold, no charge. (Oracle: no prepaid/virtual cards.)
3. Create Compute > Instance > shape = Ampere A1 (Arm). Choose 2 OCPU + 12GB RAM within Always Free allowance.
4. Add your SSH public key -> create -> you get a public IP and port 22 (your free SSH server!).
5. Install Docker:
   - `curl -fsSL https://get.docker.com | sh`
   - run anything: nginx, Postgres, Uptime Kuma, sish tunnel server, Ollama, your MCP servers, 24/7 dynamic websites.
6. Add a free domain (12-Domains-DNS) + Cloudflare free plan in front for SSL/DDoS.
7. Keep it alive: if the account is idle 30 days Oracle may reclaim idle Always Free instances - run something real on it, or use free Uptime Kuma to ping it.

## FRAMEWORK: Google e2-micro (tiny always-free backup box)
1. cloud.google.com -> Free Trial signup -> billing account.
2. Create VM: region MUST be us-west1 / us-central1 / us-east1, machine = e2-micro, 30GB standard disk.
3. 1GB RAM is tight - good for cron, a lightweight API, a tunnel server, or a WireGuard VPN endpoint.

## THE META (need a 4GB+ GPU or 64GB RAM free forever?)
No provider gives a big/GPU box free forever. The meta:
1. **Burst power free**: Google/Azure/AWS trial credits (up to $300-200) = rent big machines for 1-3 months at $0.
2. **Colab**: free GPU sessions for AI work, tunneled to your free VM.
3. **Combine free boxes**: Oracle (compute) + Google e2-micro (backup) + Cloudflare (edge) = a redundant free stack. A monitor on one pings the other.
4. **Distributed**: your free VMs + your home PC (Tailscale) = a free "cluster". A laptop on 24/7 is more RAM than any free VM.

## GOTCHAS
- Oracle/AWS/Azure all want a card; it's verification only within free limits - but set spend alerts and never "upgrade to paid" accidentally.
- Oracle Arm instance: egress is 10TB/mo - plenty, but track it.
- Free trial credits EXPIRE (calendar reminder mandatory).
- AWS new free tier is CREDITS, not the old 12-month t3.micro - it runs out after 6 months or when spent.
- Google e2-micro free is only in 3 US regions and 1GB egress/mo free.
- Don't run a second instance that pushes you over the monthly free OCPU-hour pool on Oracle.
