# FRAMEWORK: Free Domains, DNS, SSL & Naming
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
A real domain name (or subdomain) with free DNS and free SSL for your free-stack services.

## FREE SUBDOMAIN SERVICES (get a real URL without buying a TLD)
| Service | What | Rules |
|---|---|---|
| is-a.dev | `yourname.is-a.dev` | PR to github.com/is-a-dev/register, free forever, Cloudflare-backed |
| is-a.bot | `yourname.is-a.bot` | same, new service |
| DuckDNS | `yourname.duckdns.org` + dynamic DNS | token-based, free, for self-hosting/dynamic IPs |
| eu.org | `yourname.eu.org` | free for non-commercial, manual approval |
| nic.eu.org | `yourname.nic.eu.org` | alternative |
| js.org | `yourname.js.org` | GitHub Pages only, PR-based |
| netlify.app / vercel.app / pages.dev / onrender.com | built-in subdomains | free with each host |
| Cloudflare Pages/GH Pages subdomains | `<proj>.pages.dev` | free |

## FREE DNS + SSL (the backbone)
- **Cloudflare Free Plan**: full DNS hosting for any domain, DDoS protection, free edge SSL, CDN, email routing, workers, pages, R2... THE one account to build your free stack around. 100% free.
- deSEC: free DNS API (alternative).
- Let's Encrypt: free auto-renewing TLS certs everywhere.

## FRAMEWORK A: full branded identity at $0
1. Claim `yourname.is-a.dev`:
   - Fork is-a-dev/register, add `domains/yourname.json`, PR. Merge = DNS live in minutes.
   - Records supported: A, AAAA, CNAME, MX, TXT, SRV, CAA, NS (approved cases).
2. Add the zone to Cloudflare free (import records or let it proxy).
3. Free HTTPS via Cloudflare's edge cert + auto HTTPS on any host you point at.
4. Use it for: GitHub Pages, Cloudflare Pages, Vercel, your Oracle VM's services, email routing.
Result: a real-looking domain with SSL, DNS, CDN, DDoS - all free.

## FRAMEWORK B: dynamic DNS for a home server / VM with changing IP
1. DuckDNS: `https://www.duckdns.org/update?domains=yourname&token=TOKEN&ip=` -> a cron updates it when your IP changes.
2. Or Cloudflare dynamic DNS script: a cron on your box calls the Cloudflare API to update the A record (recommended if you own a zone there).
3. Point the name at your tunnel / VM and you have a permanent address.

## FRAMEWORK C: free real TLD (one year, e.g. .com-ish)
- No truly free .com forever exists. Legit one-time plays:
  - Vercel Pro trial includes a free domain 1st year (.online/.site/.space/.store/.tech/.website) - only if you take Pro.
  - Freenom-style free TLDs are effectively dead (2026).
- The meta: your `is-a.dev` subdomain IS your permanent free identity. If you later want a real TLD, that's the only honest $8-15/yr line item in the whole stack.

## GOTCHAS
- is-a.dev: one per user, no squatting, must be actively used; NS records limited.
- eu.org can take weeks for approval.
- DuckDNS: no custom domain, some Let's Encrypt rate-limit issues on their subdomains (certs through your own host instead).
- Cloudflare free: certs are shared edge certs (fine); you can also issue Let's Encrypt through Cloudflare for full control.
- Your domain is the ONE part of the stack you should treat as semi-permanent - pick names you'll keep.
