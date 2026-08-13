#!/usr/bin/env python3
"""
answer.py - Retrieval-Augmented Generation over your own docs.
1. Semantic search (search.py logic) -> top chunks
2. Ask a free LLM (05/llm.py / llm_router.py) with the chunks as context

Usage:
    python3 answer.py "how do I deploy a worker"
    OPENROUTER_API_KEY=sk-or-... python3 answer.py "question"
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
ENV = ROOT / ".env"
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
TOPK = int(os.environ.get("RAG_TOP_K", "4"))

sys.path.insert(0, str(HERE))
import search as search_mod


def retrieve(query: str) -> list[dict]:
    vec = search_mod.embed(query)
    payload = {"q": query, "hybrid": {"embedder": "default", "semanticRatio": 0.7}, "limit": TOPK,
               "vectors": {"default": vec}}
    import urllib.request
    req = urllib.request.Request(f"{MEILI_URL}/indexes/{INDEX}/search",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {MEILI_KEY}",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["hits"]


def ask_llm(query: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits)
    prompt = (f"Answer the question using ONLY the context below. "
              f"If the context doesn't contain the answer, say so. "
              f"Cite sources as [source].\n\nCONTEXT:\n{ctx}\n\nQUESTION: {query}")

    # prefer the router (has OpenRouter/Groq fallbacks); fall back to llm.py
    router = ROOT / "05-LLM-AI" / "llm_router.py"
    if router.exists():
        import subprocess
        r = subprocess.run([sys.executable, str(router), prompt], capture_output=True, text=True, timeout=180)
        if r.returncode == 0:
            return r.stdout
    sys.path.insert(0, str(ROOT / "05-LLM-AI"))
    import llm
    return llm.chat("openrouter", prompt)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: answer.py \"question\"")
        return 1
    query = " ".join(sys.argv[1:])
    hits = retrieve(query)
    print(f">> retrieved {len(hits)} chunks\n")
    answer = ask_llm(query, hits)
    print(answer)
    print("\n--- sources ---")
    for h in hits:
        print(f"  {h['source']} (chunk {h['chunk']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
