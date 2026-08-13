# 12 — Free Domains, DNS & SSL

| Provider | Free tier | Role |
|---|---|---|
| is-a.dev | `yourname.is-a.dev` free forever | Your root domain (via PR to their GitHub) |
| Cloudflare | DNS + SSL + CDN, unlimited | Nameservers, proxying, wildcard SSL, email routing |
| DuckDNS | `yourname.duckdns.org` | Dynamic DNS for home servers (no static IP) |
| Let's Encrypt | unlimited 90-day certs | Certs for self-hosted services on your VM |

| File | Purpose |
|---|---|
| `is-a-dev-generate.py` | Generates the PR file `domains/<sub>.json` for is-a.dev registration |
| `cloudflare-dns.py` | Add/update DNS records via Cloudflare API (put your domain behind CF) |
| `duckdns.sh` / `duckdns.ps1` | Dynamic-DNS updaters (Linux cron / Windows task) |
| `README.md` | Steps |

## Quick start
```bash
# 1) Free root domain: is-a.dev
python3 is-a-dev-generate.py --sub yourname --record '{"type":"CNAME","content":"freestack.pages.dev"}'
#    -> creates domains/yourname.json; PR it to github.com/is-a-dev/register

# 2) Put it behind Cloudflare (free): add the domain in CF, set NS to Cloudflare's.
#    Get CLOUDFLARE_API_TOKEN + CF_ZONE_ID -> ../.env, then:
python3 cloudflare-dns.py --add --name yourname.is-a.dev --type CNAME --content freestack.pages.dev --proxy

# 3) Dynamic DNS for a home/VM box without static IP:
./duckdns.sh            # Linux cron */5 min
.\duckdns.ps1           # Windows Task Scheduler
```
Wildcard `*.yourname.is-a.dev` via CF proxy = free SSL for every service on your VM
(Ollama, Kuma, Meilisearch, n8n...). Point each `CNAME` at your tunnel host (03).
