#!/usr/bin/env python3
"""
search.py - semantic search over your indexed docs.
Queries Ollama for an embedding, then Meilisearch hybrid search (semantic + keyword).

Usage:
    python3 search.py "how do I deploy a worker"
    python3 search.py "deploy worker" --top 5
"""
import json, os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ENV = HERE.parents[1] / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700")
MEILI_KEY = os.environ.get("MEILI_KEY", "devkeychangeit")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
INDEX = os.environ.get("MEILI_INDEX", "docs")


def embed(text: str) -> list[float]:
    req = urllib.request.Request(f"{OLLAMA}/api/embeddings",
                                 data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["embedding"]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: search.py \"query\" [--top N]")
        return 1
    query = sys.argv[1]
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 3

    vec = embed(query)
    payload = {"q": query, "hybrid": {"embedder": "default", "semanticRatio": 0.7}, "limit": top,
               "vectors": {"default": vec}}
    req = urllib.request.Request(f"{MEILI_URL}/indexes/{INDEX}/search",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {MEILI_KEY}",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        hits = json.loads(r.read())["hits"]

    if not hits:
        print("no results")
        return 1
    for i, h in enumerate(hits, 1):
        print(f"[{i}] {h['source']} (chunk {h['chunk']})")
        print(f"    {h['text'][:180].strip()}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
