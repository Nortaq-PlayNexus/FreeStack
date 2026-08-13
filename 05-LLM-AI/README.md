# 05 — Free LLM / AI: failover router + self-host

Three ways to call LLMs for $0:

| Kit | What | When to use |
|---|---|---|
| `llm_router.py` | OpenAI-compatible failover router (429/5xx/timeout -> next free provider) | Most things |
| `llm.py` | Tiny no-dependency client (no `openai` package needed) | Scripts, quick tests |
| `ollama-setup.sh` | Self-host open models on your free VM (Ollama, no quota at all) | "Fullest power" |

## How the router works
It reads provider config, tries them in order, and on 429/5xx/timeout rotates to the next:
```
OpenRouter (free models) -> Groq -> Cerebras -> Gemini -> Mistral -> Kilo (no key)
```
Once any provider succeeds, that result is returned. Keys come from `../.env`.

## Quick start
```bash
cp ../../.env.example ../../.env   # fill in at least OPENROUTER_API_KEY
python3 llm.py "explain quantum computing in one sentence"
# or with provider control:
python3 llm_router.py --provider groq --model llama-3.3-70b-versatile "hi"
```

## Self-host (the unlimited play)
```bash
bash ollama-setup.sh   # run ON the free VM (07): installs Ollama + pulls models + serves OpenAI-compatible API
# then point the router at OLLAMA_BASE_URL - zero quotas, zero cost, fully owned.
```
