#!/usr/bin/env python3
"""
healthchecks.py - wrap any job with Healthchecks.io dead-man-switch pings.
Healthchecks.io is free & unlimited; the ping URL pattern is:
    https://hc-ping.com/<PING_KEY>[/start|/fail|<message>]

Usage:
    export HEALTHCHECKS_PING_KEY=<from dashboard>
    python3 healthchecks.py --start         # job started (optional)
    python3 healthchecks.py --success       # job finished OK
    python3 healthchecks.py --fail "reason" # job failed
"""
import os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ENV = HERE.parent / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

KEY = os.environ.get("HEALTHCHECKS_PING_KEY", "")
if not KEY:
    print("set HEALTHCHECKS_PING_KEY (from your Healthchecks.io dashboard) in ../.env")
    sys.exit(1)


def ping(suffix: str = "", body: bytes | None = None) -> bool:
    url = f"https://hc-ping.com/{KEY}"
    if suffix:
        url += "/" + suffix
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "help"
    if arg == "--start":
        ok = ping("start")
        print("started ping:", "OK" if ok else "FAILED")
        return 0 if ok else 1
    if arg == "--success":
        ok = ping()
        print("success ping:", "OK" if ok else "FAILED")
        return 0 if ok else 1
    if arg == "--fail":
        msg = sys.argv[2] if len(sys.argv) > 2 else "job failed"
        ok = ping("fail", msg.encode())
        print("fail ping:", "OK" if ok else "FAILED")
        return 0 if ok else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
