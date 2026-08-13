#!/usr/bin/env python3
"""
betterstack-deploy.py - create Better Stack Uptime monitors from betterstack.yml.
Free tier: 10 monitors, 3-min checks (survives your VMs dying).
Requires: BETTERSTACK_UPTIME_TOKEN in ../.env (dashboard -> Settings -> API tokens)
"""
import json, os, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ENV = HERE.parent / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

TOKEN = os.environ.get("BETTERSTACK_UPTIME_TOKEN", "")
if not TOKEN:
    print("set BETTERSTACK_UPTIME_TOKEN in ../.env (betterstack.com -> Settings -> Tokens)")
    sys.exit(1)

API = "https://uptime.betterstack.com/api/v2/monitors"
import yaml
CONFIG = yaml.safe_load((HERE / "betterstack.yml").read_text())


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  API error {e.code}: {e.read()[:200]}")
        return None


def main() -> int:
    created = 0
    for m in CONFIG["monitors"]:
        payload = {"url": m["url"], "name": m["name"],
                   "expected_status_code": m.get("expected_status", 200),
                   "check_frequency": m.get("check_interval", 60)}
        if "port" in m:
            payload["port"] = m["port"]
            payload["url"] = f"https://{m['url']}:{m['port']}"
        result = api("POST", API, payload)
        if result and result.get("data"):
            print(f"  created monitor: {m['name']} -> {result['data']['url']}")
            created += 1
        time.sleep(1)  # rate limit breathing room
    print(f">> done: {created} monitors created")
    return 0


if __name__ == "__main__":
    sys.exit(main())
