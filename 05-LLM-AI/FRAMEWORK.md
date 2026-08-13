# FRAMEWORK: Free LLM / AI APIs (Full Power, No Credits)
Last researched: 2026-08-12 | Tier: 100% free, no money ever

## GOAL
Call frontier-class AI models (Llama, DeepSeek, Gemini, Qwen, Mistral, GPT-OSS...) for $0 forever - without paying per-token.

## FREE PROVIDERS (no credits needed - the real deal)
| Provider | Endpoint | Key? | Top free models |
|---|---|---|---|
| OpenRouter | https://openrouter.ai/api/v1 | free account | Ling 3.0 Flash, North Mini Code, Nemotron 3 Ultra 550B, Gemma 4 31B, GPT-OSS-20B |
| Google AI Studio | https://generativelanguage.googleapis.com/v1 | Google key | Gemini 3 Flash, Gemini 3.5 Flash-Lite, Gemma 4 31B, Gemma 3 27B |
| Kilo Gateway | https://kilo.ai/api/v1 | NO | auto-router to all free models below |
| Groq | https://api.groq.com/openai | yes | Llama 3.3 70B, GPT-OSS-120B, DeepSeek R1, Qwen QwQ 32B |
| Cerebras | https://api.cerebras.net | yes | GPT-OSS-120B, GLM-4.7, Gemma 4 31B |
| NVIDIA NIM | https://integrate.nvidia.com | phone verify | open models, 40 req/min |
| Mistral (La Plateforme) | https://api.mistral.ai | phone verify | all open + proprietary Mistral models |
| Cloudflare Workers AI | https://api.cloudflare.com/client/v4 | yes | Llama 4 Scout, Gemma 3, DeepSeek R1, Qwen QwQ 32B |
| OpenCode Zen | https://opencode.ai/zen | yes | DeepSeek V4 Flash, MiMo-V2.5, Nemotron 3 Ultra |
| Cohere | https://api.cohere.com | yes | free tier |
| HuggingFace Inference | https://api-inference.huggingface.co | token ($0.10) | all HF models |

## TRIAL-CREDIT PROVIDERS (free money, use-then-rotate)
Fireworks $1 | Baseten $30 | Nebius $1 | Novita $0.5/yr | AI21 $10/3mo | Upstage $10/3mo | NLP Cloud $15 | Alibaba 1M tokens/90d | Modal $30/mo | Inference.net $1 | Hyperbolic $1 | SambaNova $5/3mo | Scaleway 1M tokens

## FRAMEWORK A: the 100% free router (recommended)
1. Create free OpenRouter account -> grab API key. It aggregates ~all open models with the free ones marked `:free`.
2. Point any OpenAI-compatible client at `https://openrouter.ai/api/v1` with the free model id (e.g. `meta-llama/llama-3.3-70b-instruct:free`).
3. Rate limits on free models reset daily and rotate by provider - if one 429s, switch model id. Build a tiny failover list in your app.

## FRAMEWORK B: zero-key path
1. Kilo Gateway `https://kilo.ai/api/v1` - NO key required, auto-routes to the best currently-free model. Fastest possible start.

## FRAMEWORK C: self-host the weights (max power, absolute zero cost)
The nuclear option = zero API dependency. Run open models ON YOUR OWN FREE INFRASTRUCTURE:
- Oracle Cloud Always Free VM (4 OCPUs burst / 12GB RAM) can run small models (7B quantized) at usable speed, or llama.cpp server for inference.
- Google Colab free GPU (when available) runs 7-13B models fully free, streamed over a tunnel.
- Cloudflare Workers AI free tier for small fast inference at the edge.
- Run via Ollama + llama.cpp: `ollama run llama3.2` - then expose an OpenAI-compatible endpoint at `http://localhost:11434` over an ssh tunnel (see 03).
This is the "fullest power, 100% free" play: your compute, your weights, no quotas at all.

## THE META (no free tier exists for your model?)
A model only available on paid APIs (e.g. GPT-4/Claude/Opus frontier gated models) has no free tier. The meta:
1. Find an open-weight equivalent that IS free (Llama 4, DeepSeek R1/V4, Qwen QwQ, Nemotron 3, GPT-OSS-120B).
2. Distill: use the paid model once to generate data, then fine-tune a free open model on your data. Free after the one-time generation.
3. Route: send trivial requests to free models, keep the gated model for the rare high-stakes call on a trial credit.

## GOTCHAS
- Free model endpoints rotate daily - code a retry/failover loop.
- Free tiers are rate-limited (requests/min + daily reset); not for mass production.
- Phone-verification required: NVIDIA, Mistral.
- HF inference needs ~$0.10 balance for paid models; free ones need none.
- "Free" OpenRouter models are community-hosted - occasional downtime expected.
