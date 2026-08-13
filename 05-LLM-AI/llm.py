#!/usr/bin/env python3
"""
llm.py - tiny OpenAI-compatible client with NO third-party dependencies.
Uses urllib only. Reads keys from ../.env (or environment).
Default provider: OpenRouter free models. Zero cost.

Usage:
    python3 llm.py "your prompt"
    python3 llm.py --provider groq --model llama-3.3-70b-versatile "prompt"
    OPENROUTER_API_KEY=sk-or-... python3 llm.py "prompt"
"""
import argparse, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", ".env")
if os.path.exists(ENV):
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))

PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": os.environ.get("OPENROUTER_API_KEY", ""),
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "extra": {"HTTP-Referer": "https://freestack.local", "X-Title": "freestack"},
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "default_model": "llama-3.3-70b-versatile",
    },
    "cerebras": {
        "url": "https://api.cerebras.net/v1/chat/completions",
        "key": os.environ.get("CEREBRAS_API_KEY", ""),
        "default_model": "llama-3.3-70b",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key": os.environ.get("GEMINI_API_KEY", ""),
        "default_model": "gemini-3-flash",
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key": os.environ.get("MISTRAL_API_KEY", ""),
        "default_model": "open-mistral-nemo",
    },
    "ollama": {
        "url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1/chat/completions",
        "key": "",
        "default_model": "llama3.2",
    },
}


def chat(provider: str, prompt: str, model: str | None = None, system: str | None = None, **kwargs) -> str:
    cfg = PROVIDERS[provider]
    body = {
        "model": model or cfg["default_model"],
        "messages": [{"role": "system", "content": system or "You are a helpful assistant."},
                     {"role": "user", "content": prompt}],
        **kwargs,
    }
    headers = {"content-type": "application/json"}
    if cfg["key"]:
        headers["authorization"] = f"Bearer {cfg['key']}"
    headers.update(cfg.get("extra", {}))

    req = urllib.request.Request(cfg["url"], data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default="Say hello.")
    ap.add_argument("--provider", choices=list(PROVIDERS), default="openrouter")
    ap.add_argument("--model", default=None)
    ap.add_argument("--system", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    args = ap.parse_args()

    try:
        print(chat(args.provider, args.prompt, args.model, args.system, max_tokens=args.max_tokens))
        return 0
    except Exception as e:
        print(f"error with provider {args.provider}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
