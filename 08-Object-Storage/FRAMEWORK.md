# FRAMEWORK: Free Object Storage (Files, Images, Backups)
Last researched: 2026-08-12 | Tier: 100% free, no card

## GOAL
S3-compatible storage for user uploads, images, backups, datasets - at $0 forever, with no surprise egress bills.

## THE FREE MATRIX
| Provider | Free storage | Egress | Ops | Ongoing? |
|---|---|---|---|---|
| Cloudflare R2 | 10 GB | ZERO egress fee - always | 1M Class A + 10M Class B/mo | Yes |
| Backblaze B2 | 10 GB | 3x your stored data free (30GB) | 2,500/day free | Yes |
| IDrive e2 | 10 GB | 1:1 ratio | unlimited | Yes |
| Filebase | 5 GB | 5 GB | - | Yes |
| Cloudflare R2 Infrequent Access | 10GB @ $0.01 | zero | - | Yes |
| AWS S3 | 5 GB | 100GB | 2k PUT/20k GET | 12-mo TRIAL only |
| Scaleway | 75 GB | 75GB | - | 3-mo trial only |

## WINNER: Cloudflare R2
- 10GB storage free forever + ZERO egress fees (even past the free tier - egress is never charged, period).
- S3-compatible API -> use boto3, rclone, aws cli unchanged.
- Plays perfectly with Cloudflare Workers/Pages (same account).
- This is the default free object storage. No trial clock. No card.

## FRAMEWORK: R2 in 5 minutes
1. Cloudflare account (free) -> R2 -> Create bucket.
2. Dashboard > R2 > Manage R2 API Tokens -> create token (Object Read & Write).
3. Use it like S3:
   - `rclone config` (s3 provider "Cloudflare") or
   - boto3 with `endpoint_url=https://<accountid>.r2.cloudflarestorage.com`
4. Serve files: either public bucket URL, or (better) a Worker with a custom route (13-Functions-Serverless) with your own caching/auth.
5. Presigned URLs for private user uploads.

## FRAMEWORK: B2 (backup-focused alternative)
1. Sign up Backblaze -> Create bucket (S3 compatible).
2. Free egress is 3x stored data, AND unlimited free egress through Cloudflare CDN / Fastly / Vultr / bunny.net (Bandwidth Alliance) - so put Cloudflare in front of a B2 bucket for free global delivery.
3. Best rclone target for offsite backups (B2 + rclone + cron = free offsite backup).

## USE CASES (all free)
- User uploads / avatars / images: R2 + a Worker.
- Offsite backups: rclone to R2 or B2 on a schedule (from your free VM).
- Static site assets: R2 or B2 fronted by Cloudflare CDN.
- Data lake for a free-stack data pipeline (logs, exports).
- Served data behind a presigned URL for paywalled content.

## THE META (need >10GB free forever?)
Free caps are 5-10GB. Legitimate meta:
1. Compression: images -> AVIF/WebP, logs -> gzip/parquet. 10GB of text is a LOT.
2. Lifecycle rules: B2/R2 Infrequent Access ($0.01/GB) is nearly free for cold data.
3. Split: hot data R2 + cold archive on multiple free providers.
4. "Unlimited": store on your free Oracle VM's 200GB disk (07) + back up the important subset to R2. Your VM is your big bucket; R2 is your durability layer.

## GOTCHAS
- AWS S3 free tier is a 12-month TRIAL - after that, real bills. Don't build on it.
- Firebase removed free Cloud Storage (Feb 2026).
- Wasabi = trial only (30 days), no free tier.
- B2 charges $0.01/GB for egress beyond 3x (except through partner CDNs) - keep the CDN in front.
- R2 operation counts (1M writes/10M reads/mo) are the real limit, not storage.
