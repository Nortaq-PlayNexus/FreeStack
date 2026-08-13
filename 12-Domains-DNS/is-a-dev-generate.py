#!/usr/bin/env python3
"""
is-a-dev-generate.py - generate the file for a free `yourname.is-a.dev` subdomain.
Fork github.com/is-a-dev/register, drop the generated file under domains/, open a PR.

Usage:
    python3 is-a-dev-generate.py --sub yourname --cname freestack.pages.dev
    python3 is-a-dev-generate.py --sub yourname --a 1.2.3.4
    python3 is-a-dev-generate.py --sub yourname --cname freestack.pages.dev --owner you --repo freestack
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).parent


def build_record(args) -> dict:
    rec = {"name": args.sub}
    if args.cname:
        rec["record"] = {"type": "CNAME", "content": args.cname, "ttl": 3600}
        rec["proxied"] = bool(args.proxy)
    elif args.a:
        rec["record"] = {"type": "A", "content": args.a, "ttl": 3600}
    elif args.txt:
        rec["record"] = {"type": "TXT", "content": args.txt, "ttl": 3600}
    else:
        raise SystemExit("specify --cname, --a, or --txt")
    if args.owner and args.repo:
        rec["owner"] = {"username": args.owner, "repo": args.repo}
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", required=True)
    ap.add_argument("--cname")
    ap.add_argument("--a")
    ap.add_argument("--txt")
    ap.add_argument("--proxy", action="store_true", help="proxy via CF (recommended)")
    ap.add_argument("--owner", default="")
    ap.add_argument("--repo", default="")
    ap.add_argument("--out", default=str(HERE / "domains"))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.sub}.json"
    out_file.write_text(json.dumps([build_record(args)], indent=2) + "\n")
    print(f">> wrote {out_file}")
    print(">> next: fork github.com/is-a-dev/register -> put this file in domains/ -> open PR")
    print(">> docs: is-a.dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
