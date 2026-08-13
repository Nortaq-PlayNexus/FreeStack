#!/usr/bin/env python3
"""
send.py - send email with automatic provider failover.
Providers (in order): Resend API -> Brevo API -> Gmail SMTP.

Env (../.env): RESEND_API_KEY, BREVO_API_KEY, EMAIL_FROM,
               optional GMAIL_USER + GMAIL_APP_PASSWORD as final fallback.

Usage:
    python3 send.py to@example.com "Subject" "<p>body</p>"
    python3 send.py to@example.com "Subject" "<p>body</p>" --only resend
"""
import argparse, json, os, smtplib, ssl, sys
from email.message import EmailMessage
from email.utils import formataddr
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", ".env")
if os.path.exists(ENV):
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def _post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"content-type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def send_resend(to, subject, html):
    key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("EMAIL_FROM")
    if not key:
        return False
    _post("https://api.resend.com/emails",
          {"from": sender, "to": [to], "subject": subject, "html": html},
          {"Authorization": f"Bearer {key}"})
    return True


def send_brevo(to, subject, html):
    key = os.environ.get("BREVO_API_KEY")
    sender = os.environ.get("EMAIL_FROM")
    if not key:
        return False
    _post("https://api.brevo.com/v3/smtp/email",
          {"sender": {"email": sender}, "to": [{"email": to}], "subject": subject, "htmlContent": html},
          {"api-key": key})
    return True


def send_gmail(to, subject, html):
    user = os.environ.get("GMAIL_USER")
    app_pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not app_pw:
        return False
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.set_content("Please use an HTML-capable client.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(user, app_pw)
        s.send_message(msg)
    return True


PROVIDERS = [("resend", send_resend), ("brevo", send_brevo), ("gmail", send_gmail)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("to")
    ap.add_argument("subject")
    ap.add_argument("html")
    ap.add_argument("--only", choices=[p for p, _ in PROVIDERS])
    args = ap.parse_args()

    for name, fn in PROVIDERS:
        if args.only and name != args.only:
            continue
        try:
            if fn(args.to, args.subject, args.html):
                print(f">> sent via {name}")
                return 0
        except Exception as e:
            print(f"   {name} failed: {e}", file=sys.stderr)
    print("all providers failed or unconfigured", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
