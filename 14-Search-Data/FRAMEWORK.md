# FRAMEWORK: Free Search, Vector & Data APIs
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Web search, semantic/vector search (RAG), and data-wrangling for your apps - at $0.

## WEB SEARCH APIs
| Provider | Free tier | Notes |
|---|---|---|
| Brave Search API | 2,000 queries/mo | independent index, no Google dependency |
| SerpApi | 100 searches/mo | Google/Bing/etc. results |
| Tavily | 1,000 API credits/mo | AI-agent-optimized search |
| Exa (Metaphor) | 1,000 credits/mo | semantic web search for agents |
| Bing Web Search | 1,000 txs/mo | via Azure free tier |
| Wikipedia / Wikivoyage | unlimited | REST API |
| DuckDuckGo Instant Answer | unlimited, no key | api.duckduckgo.com |
| OpenAlex | unlimited | scholarly/semantic citations |
| Crossref | unlimited | DOI metadata |

## VECTOR DATABASES / EMBEDDINGS (RAG) - free tiers
| Service | Free tier |
|---|---|
| pgvector on Neon / Supabase | free with those Postgres tiers (see 06) |
| Cloudflare Vectorize | free tier on Workers account |
| Weaviate Cloud | limited free cluster |
| Zilliz (Milvus) | limited free cluster |
| Qdrant | free cluster (verify) |
| Upstash Vector | limited free tier |
| Chroma (self-host) | 100% free, run on your free VM |
| LanceDB (embedded) | 100% free, no server |

## EMBEDDINGS (the vectors themselves)
- OpenRouter free models, Google AI Studio (Gemini embeddings), Mistral, Cohere (free tier), or self-host all-MiniLM/bge models with Ollama on your free VM. All $0 (see 05-LLM-AI).

## FRAMEWORK: RAG stack at $0 (agent-ready search)
1. Docs/dataset -> chunk text.
2. Embed with a free embedding API (Google AI Studio or self-hosted Ollama) -> store vectors.
3. Store in pgvector on Neon (free Postgres) or Cloudflare Vectorize.
4. Query: user question -> embed -> vector search -> feed top chunks + question to a free LLM (OpenRouter free models, 05) -> answer.
5. The whole pipeline = Neon + Cloudflare + free LLM APIs. $0. Runs daily as a cron (10-Git-CICD) or on a Worker (13).

## FRAMEWORK: web search for agents at $0
1. Brave Search API (2k/mo) OR Exa/Tavily for semantic.
2. Wrap in a Cloudflare Worker (13) so the key never ships to the client and caching cuts usage.
3. Fallback chain: Brave -> SerpApi -> DDG Instant Answer (unlimited) so one 429 doesn't kill the agent.

## THE META (need unlimited scraping/search?)
Free search quotas are real. Meta:
1. Cache aggressively (Cloudflare KV) - most search intents repeat.
2. Multiple providers in rotation (each free budget is separate).
3. Self-host your own index for YOUR data (OpenSearch / Meilisearch / Typesense on the free Oracle VM) - full-text search on your own content is unlimited and free.
4. For crawling: your own VM + free crawler (Crawl4AI, Playwright) + Cloudflare Workers for scheduling = your own search index for your domain.

## GOTCHAS
- Free search tiers usually prohibit commercial/resale use.
- Exa/Tavily credits refresh monthly; pick based on your agent's query shape.
- Vector free tiers are small (hundreds of MB vectors) - fine for docs, not for whole-corpus.
- Upstash vector / Qdrant free clusters have limits; pgvector on Neon is the most predictable free option.
- Verify current quotas - search providers change them more than any other category.
