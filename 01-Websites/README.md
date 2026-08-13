# 01 — Free Websites: Deploy Kits

Everything needed to put a website live at $0. Static = effectively unlimited (Cloudflare Pages). Dynamic = free with sleep/cold-start trade-offs (Render) or fully 24/7 on your free VM (07).

## Contents
| File | Purpose |
|---|---|
| `site/` | Minimal ready-to-deploy static site (works everywhere, no build step) |
| `deploy-cloudflare.sh` | Create + deploy a Cloudflare Pages project (free, no bandwidth cap) |
| `deploy-render.sh` | Deploy a dynamic web service to Render (750 free hrs/mo) |
| `deploy.sh` | Universal deployer: reads `SITE_NAME` and picks the right target |
| `render.yaml` | Render blueprint (web service + optional Postgres) |
| `Dockerfile` | Container definition for any dynamic app (Render / your VM) |
| `README.md` | Exact steps: static first, dynamic second, 24/7 third |

## Quickest possible start (static, ~5 min)
```powershell
# from this folder
.\deploy-cloudflare.sh        # runs in Git Bash / WSL, or:
bash deploy-cloudflare.sh
```
The script creates the Pages project from `site/` and prints your `*.pages.dev` URL.

For the "never think about hosting again" path, read 12-Domains-DNS and point a free `is-a.dev` domain at the Pages URL, then flip the project to git-connected for auto-deploys.
