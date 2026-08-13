# FRAMEWORK: Free Databases (Relational, NoSQL, Edge, Vector)
Last researched: 2026-08-12 | Tier: 100% free, most need NO credit card

## GOAL
A real, managed database that lives at $0/month. Prefer PostgreSQL-compatible (Supabase/Neon/Cockroach) = zero lock-in (pg_dump migrates anywhere).

## THE FREE MATRIX
| Service | Type | Free storage | Card? | Always-on? | Best for |
|---|---|---|---|---|---|
| Neon | Serverless Postgres | 0.5GB x up to 100 projects | No | scale-to-zero | pure Postgres, branching, pgvector |
| Supabase | Postgres + auth + storage | 500MB DB + 1GB files | No | pauses after 7d idle | full-stack backend, auth, realtime |
| CockroachDB | Distributed Postgres | 10 GiB | No | Yes (99.99%) | max free storage, SLA |
| Turso | Edge SQLite (libSQL) | 9 GB | No | Yes | edge reads, zero cold starts |
| Cloudflare D1 | Edge SQLite | 5 GB | No | Yes | Workers ecosystem |
| MongoDB Atlas M0 | Document NoSQL | 512 MB | No | Yes | flexible schemas, mobile |
| Firebase Firestore | Document NoSQL | 1 GiB | No | Yes | Google stack, realtime |
| Appwrite Cloud | BaaS + DB | 2 GB | No | Yes | auth, functions bundled |
| Aiven | Postgres dedicated node | 1 GB (1CPU/1GB RAM) | No | powers off idle | real dedicated VM |
| Nile | Multi-tenant Postgres | 1-10 GB | No | Yes | SaaS/multi-tenant |
| Xata | Postgres-compatible | generous | No | Yes | - |
| Vercel Postgres | Serverless Postgres | 256 MB | No | scale-to-zero | Next.js only |
| Render Postgres | Postgres | 1 GB | No | EXPIRES in 30 days | demos only |

## FRAMEWORK A: "I just need a database" -> Neon (the default)
1. Sign up at neon.tech (email or GitHub). No card.
2. Create a project -> get connection string `postgresql://...`.
3. It scales to zero when idle (you pay nothing), wakes in 1-3s on first query. Supports branching (instant DB clones for CI) and pgvector (embeddings/RAG).
4. Point any Postgres client/ORM at it. `psql "$DATABASE_URL"`.

## FRAMEWORK B: "I need auth + storage + APIs too" -> Supabase
1. Sign up -> new project -> it auto-generates REST + GraphQL APIs from your schema.
2. Use built-in auth (50k MAU), storage (1GB), realtime subscriptions, edge functions.
3. WATCH: project pauses after 1 week with no API requests. Add a free keep-alive cron (Uptime Kuma / Healthchecks ping) so it never sleeps.
4. No backups on free plan - export with `pg_dump` weekly via GitHub Actions (see 10-Git-CICD).

## FRAMEWORK C: max free storage + SQLite edge -> Turso
1. `turso db create mydb` (or web signup) -> get up to 9GB, 500 databases.
2. Embedded replicas give ultra-low-latency reads at 26+ locations. SQLite-compatible.
3. Always-on, no pauses. Best for read-heavy apps, mobile, edge.

## FRAMEWORK D: vector/embeddings (RAG) for free
- pgvector on Neon or Supabase free tiers = your vector DB for $0.
- Cloudflare Vectorize: free tier on Workers.
- Weaviate/Zilliz: limited free tiers.
- Or self-host any vector DB on your free Oracle VM (see 07).

## THE META (no free database can hold it?)
Free storage caps are hard limits. Legitimate meta:
1. Tier your data: hot data in free managed DB (Neon), cold/archive in free object storage (R2/B2, see 08) as Parquet/JSONL, query on demand.
2. For genuinely unlimited: run Postgres on the free always-on Oracle VM (12GB RAM, 200GB disk). Zero vendor, zero limits, root access. That is the "fullest power" database.
3. Compress: most side-project data is 90% logs - rotate logs to R2 and keep the DB lean.

## GOTCHAS
- PlanetScale REMOVED its free tier (April 2024) - never build a critical business on a free tier without a migration plan.
- Supabase pauses after 7 days idle; no backups on free.
- Render free Postgres DELETES after 30 days.
- Firebase removed free Cloud Storage (Feb 2026) - don't pair it with file storage.
- Neon free tier is per-project storage (0.5GB each) - use many projects for microservices.
- Keep-alive: use Healthchecks.io (free) to ping Supabase/Neon hourly so they never suspend.
