# FRAMEWORK: Free Email (Transactional API + Inbox)
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Send transactional email (password resets, notifications, receipts) programmatically at $0. Plus: a usable inbox without paying.

## TRANSACTIONAL EMAIL APIs (free tiers)
| Provider | Free quota | Daily | Card | Notes |
|---|---|---|---|---|
| Resend | 3,000 emails/mo | 100/day | No | BEST overall: REST API + SMTP relay + SDKs + inbound, 1 domain |
| MailerSend | 500 emails/mo | 100/day | No | SMTP relay + API, webhooks, 1 domain |
| Brevo (Sendinblue) | 300 emails/day | - | No | good for low volume |
| Mailtrap | 1,000 emails/mo | - | No | sandbox/test sending only (not deliverable to real inboxes on free) |
| EmailJS | 200/mo, 3 templates | - | No | client-side sending (no server needed) |
| SMTP2GO | 1,000/mo (test) | - | - | testing only |
| Postmark | 100/mo | - | - | test only |

## FRAMEWORK: Resend (the default free transactional email)
1. Sign up resend.com -> add and verify a domain (SPF + DKIM records - instructions provided; DMARC optional but recommended).
2. Grab API key. That's it.
3. Send:
   ```
   curl https://api.resend.com/emails \
     -H "Authorization: Bearer re_xxx" \
     -d '{"from":"you@yourdomain.com","to":"user@x.com","subject":"hi","html":"<p>hi</p>"}'
   ```
4. Or use SDKs (`@react-email`, Python `resend`, etc.) / SMTP relay.
5. 3,000/mo is ~100 emails/day = more than enough for most apps' auth mail.
6. Inbound email (receiving) also included - count it against the same quota.

## FREE INBOX / MAIL HOSTING (receiving + a real address)
- **Free email on your own domain is hard** (that's the part without a true free tier).
- Workarounds:
  - Cloudflare Email Routing (free): forwards mail sent to your domain to any inbox. Catch-all, no storage - but gives you a real `you@yourdomain.com` that forwards.
  - ForwardEmail.net: free forwarding service.
  - Gmail alias: `yourname+anything@gmail.com` - free unlimited aliases.
  - iCloud+ / Zoho Mail free tier: free domain email hosting (Zoho Lite is free for 1 user/5GB).
- The meta: Cloudflare Email Routing -> forward to your Gmail = you OWN a branded inbox for $0 (domain needed - see 12-Domains-DNS: is-a.dev gives you a domain for free too).

## FRAMEWORK: full free mail loop
1. Free domain: `name.is-a.dev` (12-Domains-DNS).
2. DNS at Cloudflare free plan.
3. Enable Cloudflare Email Routing -> route `hi@name.is-a.dev` -> your Gmail.
4. For SENDING: Resend with that domain verified (3,000/mo free).
Result: branded send + branded receive, $0.

## THE META (no free tier exists for bulk email?)
- Newsletters/bulk: free tiers cap hard (Resend marketing = 1,000 contacts). The meta:
  1. Resend free marketing: up to 1,000 contacts, unlimited sends - covers small newsletters.
  2. Self-host Mail-in-a-Box / Postal on your free Oracle VM (07) = unlimited self-owned email on your domain (deliverability is on you: warm up IP, SPF/DKIM/DMARC).
  3. Multiple providers in rotation for different mail streams (each free quota is separate).

## GOTCHAS
- Free tiers STOP sending when quota hits (no auto-bill on Resend/MailerSend free - they pause).
- Daily limits (100/day) reset at midnight UTC.
- Inbound email counts toward the same quota on Resend.
- Deliverability: verify SPF + DKIM + DMARC or land in spam.
- Sending domains need verification approval on some providers - do it first, it can take minutes to a day.
- Resend free = 1 domain only.
