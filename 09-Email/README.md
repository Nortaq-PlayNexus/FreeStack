# 09 — Free Email: sending + receipts

| Provider | Free tier | Use for |
|---|---|---|
| Resend | 3,000/mo, 100/day | Transactional (alerts, verification) |
| Brevo (Sendinblue) | 300/day | Higher-volume email, no daily cap issue |
| Gmail SMTP | 500/day | Zero-setup fallback via App Password |

| File | Purpose |
|---|---|
| `send.py` | Send email via any of: Resend API, Brevo API, Gmail SMTP. Auto-fails over. |
| `send.sh` | Shell one-liner wrapper using curl (Resend + Brevo). |
| `verify.sh` | Adds SPF/DKIM/DMARC records to your Cloudflare DNS for the domain (12). |
| `README.md` | Steps |

## Quick start
```bash
# ../.env:
#   RESEND_API_KEY=re_...          (resend.com - verify your domain there)
#   EMAIL_FROM="noreply@yourname.is-a.dev"
python3 send.py "recipient@example.com" "Subject" "<p>hello</p>"

# or Gmail fallback: EMAIL_FROM=you@gmail.com GMAIL_APP_PASSWORD=xxxx
# (google.com/settings/security > App passwords, enable 2FA first)
```

## Deliverability (important!)
Free senders land in spam unless the domain is verified. Run `verify.sh` once
(needs CLOUDFLARE_API_TOKEN + CF_ZONE_ID in ../.env) after adding your domain to Resend,
then do the same in Brevo if used. Every provider wants SPF + DKIM + DMARC.
