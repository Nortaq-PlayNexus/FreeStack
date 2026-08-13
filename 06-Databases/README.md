# 06 — Free Databases: keepalive, backups, self-host

Free-tier managed DBs suspend when idle (Supabase: 7 days) and ship no real backups.
This kit fixes both and adds a self-hosted Postgres for unlimited everything.

| File | Purpose |
|---|---|
| `keepalive.py` | Wakes every free DB once/day (Supabase + Neon + Turso) - run from GitHub Actions (10) |
| `backup.sh` | pg_dump -> gzip -> upload to R2 (08) with retention. Cron nightly |
| `postgres-compose.yml` | Self-hosted Postgres 16 + pgadmin on your free VM (07) |
| `README.md` | Steps |

## Quick start
```bash
cp ../../.env.example ../../.env   # fill DATABASE_URL / SUPABASE_URL / TURSO_URL
python3 keepalive.py                # manual poke; better: schedule in 10-Git-CICD
bash backup.sh                      # nightly to r2:freestack-backups (configure rclone in 08)
# on the VM:
docker compose -f postgres-compose.yml up -d
```

## Why these three
- **Supabase** pauses after 7 days idle -> keepalive pings it daily.
- **Neon** scale-to-zero adds cold-start latency -> keepalive keeps it warm.
- **Turso/libSQL** free tier is generous but same idea -> keepalive covers it.
- **Backups**: even free tier can delete your data (Render wipes after 30 days). pg_dump is the answer.
