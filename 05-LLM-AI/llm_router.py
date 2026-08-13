#!/usr/bin/env python3
"""
llm_router.py - failover router across free LLM providers.
Tries each provider (in order) until one returns 2xx. Handles 429/5xx/timeouts.
Optionally spawns a tiny OpenAI-compatible server on --serve (default port 8787)
so ANY tool that speaks OpenAI can use the router via http://localhost:8787/v1.

Usage:
    python3 llm_router.py --provider groq --model llama-3.3-70b-versatile "prompt"
    python3 llm_router.py --serve --port 8787        # then point any client at it
    python3 llm_router.py --check                    # probe all providers, print status
"""
import argparse, json, os, sys, threading, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", ".env")
if os.path.exists(ENV):
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))

PROVIDERS = [
    {"id": "openrouter", "url": "https://openrouter.ai/api/v1/chat/completions",
     "key": os.environ.get("OPENROUTER_API_KEY", ""),
     "models": ["meta-llama/llama-3.3-70b-instruct:free", "north/code-mini:free", "google/gemma-4-31b:free"],
     "extra": {"HTTP-Referer": "https://freestack.local", "X-Title": "freestack"}},
    {"id": "groq", "url": "https://api.groq.com/openai/v1/chat/completions",
     "key": os.environ.get("GROQ_API_KEY", ""),
     "models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b"]},
    {"id": "cerebras", "url": "https://api.cerebras.net/v1/chat/completions",
     "key": os.environ.get("CEREBRAS_API_KEY", ""),
     "models": ["llama-3.3-70b"]},
    {"id": "gemini", "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
     "key": os.environ.get("GEMINI_API_KEY", ""),
     "models": ["gemini-3-flash", "gemini-3.5-flash-lite"]},
    {"id": "mistral", "url": "https://api.mistral.ai/v1/chat/completions",
     "key": os.environ.get("MISTRAL_API_KEY", ""),
     "models": ["open-mistral-nemo"]},
    {"id": "ollama", "url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1/chat/completions",
     "key": "", "models": ["llama3.2"], "local": True},
]


def _call(provider: dict, model: str, messages: list, **kw) -> tuple[int, dict | str]:
    body = {"model": model, "messages": messages, **kw}
    headers = {"content-type": "application/json"}
    if provider["key"]:
        headers["authorization"] = f"Bearer {provider['key']}"
    headers.update(provider.get("extra", {}))
    req = urllib.request.Request(provider["url"], data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=provider.get("timeout", 90)) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode(errors="replace")
    except Exception as e:
        return 0, str(e)


def route(prompt: str, system: str = None, max_tokens: int = 1024,
          only: str | None = None, prefer_model: str | None = None) -> dict:
    messages = [{"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}]
    last = None
    for provider in PROVIDERS:
        if only and provider["id"] != only:
            continue
        if not provider["key"] and not provider.get("local"):
            continue
        model = prefer_model if prefer_model and prefer_model in provider["models"] else provider["models"][0]
        code, data = _call(provider, model, messages, max_tokens=max_tokens)
        if code == 200:
            text = data["choices"][0]["message"]["content"]
            return {"ok": True, "provider": provider["id"], "model": model, "content": text}
        last = {"provider": provider["id"], "code": code, "detail": data}
    return {"ok": False, "last": last}


def check_all() -> None:
    print("== free LLM provider health ==")
    for provider in PROVIDERS:
        if not provider["key"] and not provider.get("local"):
            print(f"  {provider['id']:10s} SKIP (no key)")
            continue
        code, _ = _call(provider, provider["models"][0], [{"role": "user", "content": "ping"}], max_tokens=1)
        print(f"  {provider['id']:10s} {code}")


# ---- tiny OpenAI-compatible server ----
def _serve(port: int) -> None:
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def _send(self, obj, status=200):
            body = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/v1/models":
                models = [{"id": m, "object": "model"} for p in PROVIDERS for m in p["models"]]
                self._send({"object": "list", "data": models})
            else:
                self._send({"error": "not found"}, 404)

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                return self._send({"error": "not found"}, 404)
            n = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            messages = body.get("messages", [])
            prompt = messages[-1]["content"] if messages else ""
            res = route(prompt, max_tokens=body.get("max_tokens", 1024))
            if not res["ok"]:
                return self._send({"error": str(res)}, 502)
            self._send({"id": "chatcmpl-freestack", "object": "chat.completion", "model": res["model"],
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": res["content"]},
                                     "finish_reason": "stop"}]})

        def log_message(self, *a):
            pass

    print(f"serving OpenAI-compatible router on http://localhost:{port}/v1")
    HTTPServer(("0.0.0.0", port), H).serve_forever()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default=None)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--system", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        check_all()
        return 0
    if args.serve:
        _serve(args.port)
        return 0
    if not args.prompt:
        ap.print_help()
        return 1
    res = route(args.prompt, args.system, args.max_tokens, only=args.provider, prefer_model=args.model)
    if not res["ok"]:
        print("all providers failed:", res["last"], file=sys.stderr)
        return 1
    print(f"[{res['provider']}/{res['model']}]")
    print(res["content"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
