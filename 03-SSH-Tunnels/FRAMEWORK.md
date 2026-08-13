# FRAMEWORK: Free SSH Servers, Tunnels & Remote Access
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Expose a localhost service (web app, SSH daemon, game server, API) to the public internet - bypassing NAT/firewalls - at $0. Also: get a free public SSH server / remote box.

## FREE HOSTED TUNNELS (no server needed)
| Service | What you get | Auth | Limits |
|---|---|---|---|
| Cloudflare Tunnel (`cloudflared`) | Named or quick tunnels, HTTPS, any TCP service via `cloudflared access tcp` | free account | None for normal use |
| localhost.run | `ssh -R 80:localhost:8080 nokey@localhost.run` | none | ephemeral, HTTP/WS only |
| serveo.net | `ssh -R 80:localhost:3000 serveo.net` | none | ephemeral |
| MekongTunnel | `ssh -t -R 80:localhost:3000 proxy.angkorsearch.dev` | none | free, MIT, *.proxy.angkorsearch.dev |
| OpenTunnel (client mode) | wraps cloudflare/ngrok quick tunnels | - | - |
| ngrok | free tier 1 agent, basic HTTP | account | session limit ~8hrs, 1GB data |

NOTE: `ssh -R` to a public tunnel host requires NO client install - just the OpenSSH client that ships with Windows/macOS/Linux.

## SELF-HOSTED TUNNEL SERVERS (run your own on a free VM)
| Project | Lang | Features |
|---|---|---|
| sish | Go | HTTP(S)/WS/TCP, SNI, aliases, load balance. Docker image. |
| ratatosk | Go | HTTP/TCP/UDP, wildcard Let's Encrypt DNS-01, basic auth |
| sandhole | Go | OpenSSH-client only (no agent!), auto HTTPS, custom domains per key |
| rathole | Rust | NAT traversal reverse proxy, high perf |
| wstunnel | Rust | WebSocket-based (works on networks that block SSH) |
| sshuttle | Python | VPN-over-SSH, only needs Python on server |
| 2nnel | Go | tunnels + promotes local apps to server containers via Nixpacks |
| here | Go | lightweight, Docker, HTTP only |

## FRAMEWORK A: Instant tunnel (2 min, zero install)
```
ssh -R 80:localhost:8080 nokey@localhost.run
```
That exposes `localhost:8080` at a public URL immediately. Perfect for demos, webhooks (Slack/Stripe callbacks to your laptop), and testing.

## FRAMEWORK B: Persistent named tunnel via Cloudflare (best for production-ish)
1. `cloudflared tunnel login` (free account).
2. `cloudflared tunnel create mysite` -> get a tunnel ID.
3. Point a DNS record (e.g. `app.mydomain.com`) at `tunnel-id.cfargotunnel.com`.
4. `cloudflared tunnel run mysite` -> your local port is public at that domain, with free TLS and Cloudflare's DDoS protection.
5. Runs on your free Oracle/Google VM or even your home PC. No open inbound ports, no static IP needed.

## FRAMEWORK C: The "no free tier exists" escape -> run your own tunnel endpoint
Some tunnel providers limit you. The meta: get a FREE always-on VM (07-Cloud-VMs-Compute), install `sish` via Docker:
```
docker run -itd -v ~/sish/ssl:/ssl -v ~/sish/keys:/keys -v ~/sish/pubkeys:/pubkeys \
  --net=host antoniomika/sish:latest \
  --ssh-address=:2222 --http-address=:80 --https-address=:443 \
  --https=true --domain=yourdomain.com --bind-random-ports=false
```
Then ANY machine anywhere (even a $0 free account device) can do `ssh -p 2222 -R 80:localhost:3000 yourdomain.com` -> unlimited tunnels, no third-party limits. You own the whole thing.

## FREE PUBLIC SSH SERVER (remote shell, no money)
- **Oracle Cloud Always Free VM** gives you a real public SSH server (port 22) permanently. That IS your free SSH box. 2 Arm cores / 12GB RAM.
- Google Cloud e2-micro: another always-free public SSH host.
- See 07-Cloud-VMs-Compute for signup framework.

## GOTCHAS
- Free hosted tunnels (localhost.run, serveo) are ephemeral - fine for demos, not for permanent services.
- ngrok free: sessions expire (~8 hours), subdomain changes.
- Self-hosted tunnels need a public IP + domain (or use DuckDNS free subdomain, see 12-Domains-DNS).
- Never expose databases/SMTP to the internet via tunnel without strong auth.

## SECURITY
- Key-only SSH auth on any server you open up.
- `fail2ban` on your tunnel VM.
- Only expose 22/80/443; keep the tunnel backend port internal.
- Treat tunnel client tokens like passwords.
