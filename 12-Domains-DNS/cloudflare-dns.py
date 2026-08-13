#!/usr/bin/env python3
"""
cloudflare-dns.py - manage DNS records on a Cloudflare zone (free plan).
Auto-proxies (orange cloud) by default -> free CDN + SSL + DDoS protection.

Requires in ../.env: CLOUDFLARE_API_TOKEN, CF_ZONE_ID (12/README.md).
Usage:
    python3 cloudflare-dns.py --list
    python3 cloudflare-dns.py --add --name app.yourname.is-a.dev --type CNAME --content freestack.pages.dev
    python3 cloudflare-dns.py --del --name app.yourname.is-a.dev --type CNAME
"""
import argparse, json, os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ENV = HERE.parent / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
ZONE = os.environ.get("CF_ZONE_ID", "")
if not TOKEN or not ZONE:
    print("set CLOUDFLARE_API_TOKEN and CF_ZONE_ID in ../.env")
    sys.exit(1)

BASE = f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records"


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read()[:200]}")
        sys.exit(1)


def find(name, rtype):
    result = api("GET", f"{BASE}?name={name}&type={rtype}")["result"]
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--del", dest="delete", action="store_true")
    ap.add_argument("--name")
    ap.add_argument("--type", default="CNAME")
    ap.add_argument("--content")
    ap.add_argument("--no-proxy", dest="proxy", action="store_false", default=True)
    args = ap.parse_args()

    if args.list:
        for rec in api("GET", f"{BASE}?per_page=50")["result"]:
            print(f"  {rec['type']:6s} {rec['name']:40s} -> {rec['content']:30s} proxied={rec.get('proxied')}")
        return 0

    if args.add:
        if not args.name or not args.content:
            print("--add needs --name and --content")
            return 1
        existing = find(args.name, args.type)
        payload = {"type": args.type, "name": args.name, "content": args.content,
                   "ttl": 1, "proxied": args.proxy}
        if existing:
            api("PATCH", f"{BASE}/{existing[0]['id']}", payload)
            print(f">> updated {args.name} {args.type} -> {args.content}")
        else:
            api("POST", BASE, payload)
            print(f">> created {args.name} {args.type} -> {args.content}")
        return 0

    if args.delete:
        if not args.name:
            print("--del needs --name")
            return 1
        for rec in find(args.name, args.type):
            api("DELETE", f"{BASE}/{rec['id']}")
            print(f">> deleted {rec['name']} {rec['type']}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
