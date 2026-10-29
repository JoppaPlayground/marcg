#!/usr/bin/env python3
"""Checks for marcgigliotti.com. Run before merging: python3 .github/scripts/check_site.py

Static checks need only the standard library. The render checks need Playwright
(pip install playwright && python -m playwright install chromium); pass
--static-only to skip them.
"""
import html
import json
import os
import re
import sys
import threading
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAGE = os.path.join(ROOT, "index.html")
SITE = "https://www.marcgigliotti.com/"

# Phrases that make the copy read as AI-written. Checked in visible page text only.
AI_TELLS = [
    r"\bnot just\b", r"\bdon't just\b", r"\bintersection of\b", r"\bnavigate the\b",
    r"\bseasoned\b", r"\btransform(ing|ative)?\b", r"\bAI-powered\b", r"\bseamless(ly)?\b",
    r"\bcurated\b", r"\bthoughtfully\b", r"\bgame[- ]chang", r"\bcutting[- ]edge\b",
    r"\bworld[- ]class\b", r"\bsynerg", r"\bdelve\b", r"\bunlock(s|ing)?\b", r"\belevate\b",
    r"\bempower", r"\bholistic\b", r"\bon the horizon\b", r"\bthings that matter\b",
    r"\bWhether you\b", r"\bnext generation of\b", r"\bpattern recognition\b",
]

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}

failures = []


def fail(check, msg):
    failures.append(f"[{check}] {msg}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def visible_text(src):
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", src, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


def check_dashes():
    for name in ("index.html", "llms.txt"):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        for i, line in enumerate(read(path).splitlines(), 1):
            if re.search(r"—|&mdash;|&#8212;|&#x2014;", line, re.I):
                fail("em dash", f"{name}:{i}: {line.strip()[:100]}")


def check_ai_tells(src):
    text = visible_text(src)
    for pattern in AI_TELLS:
        for m in re.finditer(pattern, text, re.I):
            snippet = text[max(0, m.start() - 40):m.end() + 40].strip()
            fail("wording", f"'{m.group(0)}' in: ...{snippet}...")


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            return
        open_tags = [t for t, _ in self.stack]
        if tag in open_tags:
            while self.stack and self.stack[-1][0] != tag:
                t, line = self.stack.pop()
                fail("markup", f"<{t}> opened on line {line} is never closed")
            self.stack.pop()
        else:
            fail("markup", f"stray </{tag}> on line {self.getpos()[0]}")


def check_markup(src):
    p = Balance()
    p.feed(src)
    p.close()
    for tag, line in p.stack:
        fail("markup", f"<{tag}> opened on line {line} is never closed")


def check_structured_data(src):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    if not blocks:
        fail("structured data", "no JSON-LD block found")
        return
    faq = None
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            fail("structured data", f"JSON-LD does not parse: {e}")
            continue
        for node in data.get("@graph", [data]):
            if node.get("@type") == "FAQPage":
                faq = node.get("mainEntity", [])
    if faq is None:
        return
    norm = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()
    vis_q = [norm(q) for q in re.findall(r'class="faq-q"[^>]*>(.*?)</', src, re.S)]
    vis_a = [norm(a) for a in re.findall(r'class="faq-a"[^>]*>(.*?)</p>', src, re.S)]
    data_q = [norm(i["name"]) for i in faq]
    data_a = [norm(i["acceptedAnswer"]["text"]) for i in faq]
    if vis_q != data_q:
        fail("structured data", f"FAQ questions differ from the page: data={data_q} page={vis_q}")
    for q, d, v in zip(data_q, data_a, vis_a):
        if d != v:
            fail("structured data", f"FAQ answer for '{q}' differs from the page")
    if len(data_a) != len(vis_a):
        fail("structured data", f"{len(data_a)} FAQ answers in data, {len(vis_a)} on the page")


def check_links(src):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', src)
    if not m or m.group(1) != SITE:
        fail("links", f"canonical should be {SITE}")
    refs = re.findall(r'(?:src|href)="([^"#?]+)', src) + re.findall(r"url\(([^)'\"]+)\)", src)
    for ref in set(refs):
        if re.match(r"^(https?:|mailto:|tel:|data:|#|//)", ref) or ref == "/":
            continue
        path = os.path.join(ROOT, ref.lstrip("/"))
        if not os.path.exists(path):
            fail("links", f"missing file: {ref}")


def check_render():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("render", "Playwright is not installed (or pass --static-only)")
        return
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = partial(Quiet, directory=ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, w, h in (("desktop", 1440, 900), ("tablet", 820, 1180), ("phone", 360, 740)):
                page = browser.new_page(viewport={"width": w, "height": h})
                errors = []
                page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda exc, e=errors: e.append(str(exc)))
                page.on("response", lambda r, e=errors: e.append(f"{r.status} {r.url}")
                        if r.status >= 400 and r.url.startswith(url) else None)
                page.goto(url, wait_until="networkidle")
                page.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
                page.wait_for_timeout(300)
                for e in errors:
                    fail("render", f"{name}: {e}")
                sw = page.evaluate("document.documentElement.scrollWidth")
                if sw > w:
                    fail("render", f"{name}: page scrolls sideways ({sw}px wide in a {w}px window)")
                page.close()
            browser.close()
    finally:
        server.shutdown()


def main():
    src = read(PAGE)
    check_dashes()
    check_ai_tells(src)
    check_markup(src)
    check_structured_data(src)
    check_links(src)
    if "--static-only" not in sys.argv:
        check_render()
    if failures:
        print(f"{len(failures)} problem(s):")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("All site checks passed.")


if __name__ == "__main__":
    main()
