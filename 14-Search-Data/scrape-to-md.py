#!/usr/bin/env python3
"""
scrape-to-md.py - fetch a web page and convert to clean Markdown for indexing.
Pure stdlib (no BeautifulSoup dependency) via html.parser; good enough for most pages.

Usage:
    python3 scrape-to-md.py https://example.com/page > page.md
"""
import argparse, html, re, sys, urllib.request
from html.parser import HTMLParser


class ToMarkdown(HTMLParser):
    BLOCK = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "pre", "blockquote", "tr", "br"}

    def __init__(self):
        super().__init__()
        self.out = []
        self.skip = 0
        self.in_pre = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer", "noscript"):
            self.skip += 1
        if tag in self.BLOCK and not self.in_pre:
            self.out.append("\n\n" if tag not in ("li",) else "\n- ")
        if tag in ("h1",): self.out.append("# ")
        if tag in ("h2",): self.out.append("## ")
        if tag in ("h3",): self.out.append("### ")
        if tag == "a":
            href = dict(attrs).get("href", "")
            self._link = href
            self.out.append("[")
        if tag == "pre": self.in_pre, self.out = True, self.out + ["```\n"]
        if tag == "code" and not self.in_pre: self.out.append("`")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer", "noscript") and self.skip:
            self.skip -= 1
        if tag == "a" and getattr(self, "_link", ""):
            self.out.append(f"]({self._link})")
            self._link = ""
        if tag == "code" and not self.in_pre: self.out.append("`")
        if tag == "pre":
            self.in_pre, self.out = False, self.out + ["\n```"]
        if tag in ("li",): self.out.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_pre:
            self.out.append(data)
        else:
            self.out.append(html.unescape(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--user-agent", default="Mozilla/5.0 (compatible; FreeStackScraper/1.0)")
    args = ap.parse_args()

    req = urllib.request.Request(args.url, headers={"User-Agent": args.user_agent})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", errors="replace")

    parser = ToMarkdown()
    parser.feed(raw)
    text = "".join(parser.out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    sys.stdout.write(f"<!-- source: {args.url} -->\n\n{text.strip()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
