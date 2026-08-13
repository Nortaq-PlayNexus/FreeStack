#!/usr/bin/env python3
"""
keepalive.py - keep free databases awake so they never suspend.
Pokes Supabase, Neon, and Turso once a day (also fine to run more often).

Environment (../.env or shell):
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
    NEON_DATABASE_URL, TURSO_DATABASE_URL (one of them)
"""
import json, os, sqlite3, sys, urllib.request
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", ".env")
if os.path.exists(ENV):
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def poke_supabase() -> bool:
    url, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return True  # not configured = skip silently
    req = urllib.request.Request(f"{url}/rest/v1/?limit=1",
                                 headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status < 400


def poke_postgres(url: str) -> bool:
    if not url:
        return True
    p = urlparse(url)
    u = (p.username or "").replace("%40", "@")  # handle encoded @
    pw = (p.password or "").replace("%40", "@")
    host, port, db = p.hostname, p.port or 5432, (p.path or "/").lstrip("/")
    params = dict(s.split("=", 1) for s in p.query.split("&") if "=" in s)

    # use libpq-compatible connection if psql available, else pure-python
    if os.system(f"psql {url!r} -c 'SELECT 1' >/dev/null 2>&1") == 0:
        return True

    # fallback: need psycopg2/pg8000
    try:
        import pg8000.native  # pure python, pip install pg8000
        conn = pg8000.native.Connection(user=u, password=pw, host=host, port=port, database=db)
        conn.run("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def poke_turso(url: str) -> bool:
    if not url:
        return True
    if not url.startswith("file:"):
        return True  # remote turso needs the turso CLI: `turso db execute` - handle via cli
    try:
        con = sqlite3.connect(url[len("file:"):])
        con.execute("SELECT 1")
        con.close()
        return True
    except Exception:
        return False


def main() -> int:
    checks = [
        ("supabase", poke_supabase()),
        ("neon", poke_postgres(os.environ.get("NEON_DATABASE_URL", ""))),
        ("turso", poke_turso(os.environ.get("TURSO_DATABASE_URL", ""))),
    ]
    ok = True
    for name, result in checks:
        print(f"  {name:10s} {'OK' if result else 'FAIL'}")
        ok = ok and result
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
