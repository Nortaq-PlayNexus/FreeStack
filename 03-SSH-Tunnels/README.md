# 03 — Free SSH Tunnels & Remote Access

Zero-install exposure of localhost services, plus a fully self-owned tunnel endpoint so you are never limited by a third party.

| File | Purpose |
|---|---|
| `tunnel.ps1` | Windows wrapper: localhost.run / serveo / cloudflared quick tunnels |
| `tunnel.sh` | Same for Linux/macOS/Git Bash |
| `cloudflared-config.yml` | Named persistent tunnel (app + api subdomains -> localhost) |
| `cloudflared-setup.sh` | Install cloudflared + run a named tunnel as a service |
| `sish-compose.yml` | Self-host the `sish` tunnel server (Docker) on your free VM |
| `ssh-config.example` | ~/.ssh/config aliases for tunnel access |
| `README.md` | Step-by-step |

## Fastest one-liners (no install)
```bash
ssh -R 80:localhost:8080 nokey@localhost.run         # instant public URL
ssh -R 80:localhost:3000 serveo.net                  # alternative
ssh -t -R 80:localhost:3000 proxy.angkorsearch.dev   # MekongTunnel
```

## Persistent & named (Cloudflare Tunnel, free, no open ports)
```bash
bash cloudflared-setup.sh          # install + login + create tunnel
# tunnels app.mydomain and api.mydomain to localhost:8080 / localhost:8000
```

## Own your tunnel endpoint (the meta - unlimited tunnels)
On your free Oracle VM (07): `docker compose -f sish-compose.yml up -d`
Then from ANY machine: `ssh -p 2222 -R 80:localhost:8080 yourname.is-a.dev`
You now own the tunnel infra. No third-party session limits, ever.
