#!/usr/bin/env python3
"""
index-docs.py - chunk + embed + index documents into Meilisearch.
Works with the LOCAL Ollama embeddings (nomic-embed-text, from 05) so everything is free.

Needs: MEILI_URL + MEILI_KEY (env or defaults for the compose file above).
Usage:
    python3 index-docs.py notes.md blog/           # one file or a folder of .md
"""
import json, os, subprocess, sys, urllib.request
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
CHUNK = 800   # chars per chunk with ~100 overlap


def embed(text: str) -> list[float]:
    req = urllib.request.Request(f"{OLLAMA}/api/embeddings",
                                 data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["embedding"]


def chunks(text: str, size: int = CHUNK, overlap: int = 100) -> list[str]:
    if len(text) <= size:
        return [text]
    out = []
    i = 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def meili(action: str, path: str, payload=None, method="POST"):
    url = f"{MEILI_URL}/{action}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {MEILI_KEY}",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()) if r.status < 300 else None


def main() -> int:
    paths = sys.argv[1:]
    if not paths:
        print("usage: index-docs.py <file.md> [file2.md | folder/]")
        return 1

    files = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files += sorted(pp.rglob("*.md"))
        else:
            files.append(pp)

    docs = []
    for f in files:
        text = f.read_text(errors="replace")
        for i, c in enumerate(chunks(text)):
            docs.append({"id": f"{f.stem}:{i}", "source": str(f), "chunk": i, "text": c})

    print(f">> embedding {len(docs)} chunks (model: {EMBED_MODEL})...")
    for d in docs:
        d["_vectors"] = {"default": embed(d["text"])}

    print(f">> indexing into {INDEX}...")
    meili("indexes", INDEX, {"primaryKey": "id"})
    meili("indexes", f"{INDEX}/documents", docs)
    meili("indexes", f"{INDEX}/settings", {"embedders": {"default": {"source": "userProvided", "dimensions": 768}}})
    print(f">> done: {len(docs)} chunks indexed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
