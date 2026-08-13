# 14 — Free Search, RAG & Data Pipelines

| Provider | Free tier | Role |
|---|---|---|
| Meilisearch (self-hosted) | unlimited | Full-text search engine, typo-tolerant, tiny RAM |
| Cloudflare Workers AI | 10k neurons/day | Embeddings + LLM on the edge |
| Groq / OpenRouter (05) | free | Generation for RAG answers |
| Turso/Neon (06) | free | Vector storage (pgvector / libsql) |

| File | Purpose |
|---|---|
| `meilisearch-compose.yml` | Meilisearch for the free VM (07) |
| `rag/index-docs.py` | Chunk + embed your docs -> index into Meilisearch |
| `rag/search.py` | Semantic search CLI (query -> top chunks) |
| `rag/answer.py` | Full RAG: retrieve chunks, ask an LLM (05 router) |
| `scrape-to-md.py` | Convert any webpage to clean Markdown for indexing |
| `README.md` | Steps |

## The loop
```
docs/ (or any web pages)
  -> scrape-to-md.py -> clean .md files
  -> index-docs.py   -> chunk, embed (Workers AI/OpenRouter), push to Meilisearch
  -> search.py / answer.py  -> query with context, ask LLM, get cited answer
```

## Quick start
```bash
docker compose -f meilisearch-compose.yml up -d    # on the VM, or run locally

# index something
python3 scrape-to-md.py https://example.com/notes > notes.md
python3 rag/index-docs.py notes.md                 # chunks + embeds + indexes

# search + answer
python3 rag/search.py "how do I deploy workers"
python3 rag/answer.py "how do I deploy workers"    # needs OPENROUTER_API_KEY (05)
```
