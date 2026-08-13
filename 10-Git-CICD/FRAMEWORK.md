# FRAMEWORK: Free Git Hosting, CI/CD, Automation
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Store code, auto-build/deploy/test on every push, and run scheduled automation - all at $0.

## THE FREE MATRIX
| Tool | Free tier | Notes |
|---|---|---|
| GitHub | unlimited public + private repos | THE hub; everything integrates |
| GitHub Actions | 2,000 min/mo public; 500-2,000 private | CI/CD, schedules, releases, free |
| GitLab | unlimited repos, 400 CI min/mo | self-hostable |
| Bitbucket | 1,000 CI min/mo (free plan) | - |
| Codeberg | free repos (non-commercial) | forges join github/gitlab |
| Sourcehut | free for open source | - |
| Jenkins/Gitea (self-host) | unlimited | run on free VM (07) |
| CircleCI | 6,000 min/mo on free? (verify) | - |

## FRAMEWORK: the $0 pipeline
1. GitHub account (free) -> push all code. Unlimited public repos, unlimited private with actions quota.
2. GitHub Actions = your free cron + CI/CD + deploy machine:
   - **Auto-deploy**: on push to main, a workflow runs `npm run build` and pushes to Cloudflare Pages / Vercel / Render (see 01). Deploy triggers are native.
   - **Scheduled jobs (cron)**: `schedule: cron: '0 */6 * * *'` - run scrapers, keep-alive pings, backups, data refreshes. Your own free cron server.
   - **Backups**: nightly `pg_dump` of your free Neon/Supabase DB -> upload to R2 (08). Automate database backups = solves the "free DB has no backups" problem.
   - **Releases**: auto-build binaries with `release: draft` and upload to GitHub Releases (1GB per file, free hosting for your binaries).
3. Self-host runners when you need more minutes: attach your free Oracle VM (07) as a runner - Actions minutes become effectively unlimited.

## FRAMEWORK: Uptime/bot automation
- Upptime (11-Monitoring-Analytics) runs 100% inside GitHub Actions.
- n8n / Huginn (self-hosted automation) on your free VM for webhooks/scrapers/chatbots with no vendor quota.

## THE META (need unlimited CI minutes?)
Free quotas: 2,000 min/mo GitHub. Meta:
1. Public repos get MORE Actions minutes (2,000) and free on self-hosted runners - attach your Oracle VM as a self-hosted runner for truly unlimited compute.
2. Split pipelines across GitHub + GitLab + Bitbucket (3 free budgets).
3. Cache aggressively (Actions caching) to cut minutes; skip heavy steps on PRs.
4. Move long compute to a free always-on VM (cron there), keep Actions for glue.

## GOTCHAS
- Private repo Actions minutes are limited (public = 2,000/mo free on free tier; verify current numbers - they change).
- Cron minimum in Actions is 5-minute intervals.
- Secrets: store API keys as GitHub Secrets, never in code.
- Actions minutes roll monthly; a leaky workflow (rebuild on every keystroke) burns them.
- Codeberg/GitLab free tiers may restrict commercial use - check your use case.
