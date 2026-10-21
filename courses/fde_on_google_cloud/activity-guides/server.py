"""Serve the FDE discussion activity guides.

Routes:
  /                    home page linking to the four team guides
  /<guide>             a team guide, e.g. /01-unblock-the-launch
  /instructor-activity-guide   the Instructor Activity Guide (not linked from the home page)

Env var: PORT (set by Cloud Run, default 8080).
"""
import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HTML_DIR = Path(__file__).parent / "html"

GUIDES = [
    ("01-unblock-the-launch", "Unblock the Launch", "Who owns the fix?", "#1A73E8"),
    ("02-scope-defense-sparring", "Scope Defense Sparring", "Absorb, defer, or route?", "#188038"),
    ("03-trick-question-to-eval-case", "Trick Question to Eval Case", "Turn a scary anecdote into a permanent test", "#B06000"),
    ("04-escalation-triage-under-load", "Escalation Triage Under Load", "Defect, or working as designed?", "#C5221F"),
]

HOME = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FDE Discussion Activities</title>
<style>
  body { margin: 0; background: #F8F9FA; color: #202124;
         font: 16px/1.55 "Google Sans", Roboto, "Segoe UI", system-ui, sans-serif; }
  .page { max-width: 880px; margin: 32px auto; padding: 0 16px; }
  header { padding: 8px 4px 20px; }
  h1 { font-size: 34px; line-height: 1.2; margin: 0 0 6px; font-weight: 600; }
  .sub { color: #5F6368; margin: 0; }
  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
  a.card { display: block; text-decoration: none; color: inherit; background: #fff;
           border-radius: 14px; border-top: 6px solid var(--c); padding: 20px 22px;
           box-shadow: 0 1px 2px rgba(60,64,67,.15), 0 2px 8px rgba(60,64,67,.08);
           transition: transform .12s, box-shadow .12s; }
  a.card:hover { transform: translateY(-2px);
                 box-shadow: 0 2px 4px rgba(60,64,67,.2), 0 6px 16px rgba(60,64,67,.12); }
  .num { font-size: 13px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: var(--c); }
  h2 { font-size: 21px; margin: 6px 0 4px; font-weight: 600; }
  .tag { color: #5F6368; margin: 0 0 14px; }
  .go { font-weight: 600; color: var(--c); }
  footer { color: #5F6368; font-size: 13px; padding: 24px 4px; }
  @media screen and (min-width: 1200px) { html { zoom: 1.25; } }
  @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } h1 { font-size: 28px; } }
</style>
</head>
<body>
<div class="page">
<header>
  <h1>Discussion Activities</h1>
  <p class="sub">Forward Deployed Engineering on Google Cloud · Open the guide your instructor names.</p>
</header>
<main class="grid">
{cards}
</main>
<footer>Each activity runs 13 minutes in teams of 3–4. Case thread: Cymbal Logistics.</footer>
</div>
</body>
</html>
"""

CARD = """<a class="card" style="--c:{color}" href="/{slug}">
  <div class="num">Discussion {n}</div>
  <h2>{title}</h2>
  <p class="tag">{tagline}</p>
  <span class="go">Open guide &rarr;</span>
</a>"""


def build_pages():
    cards = "\n".join(
        CARD.format(color=c, slug=s, n=i, title=html.escape(t), tagline=html.escape(g))
        for i, (s, t, g, c) in enumerate(GUIDES, 1)
    )
    pages = {"": HOME.replace("{cards}", cards).encode()}
    for slug, *_ in GUIDES:
        pages[slug] = (HTML_DIR / f"{slug}.html").read_bytes()
    pages["instructor-activity-guide"] = (HTML_DIR / "instructor-activity-guide.html").read_bytes()
    return pages


PAGES = build_pages()


class Handler(BaseHTTPRequestHandler):
    def _send(self, include_body):
        path = self.path.split("?", 1)[0].strip("/")
        path = path.removesuffix(".html")
        body = PAGES.get(path)
        status = 200 if body is not None else 404
        if body is None:
            body = b"<!doctype html><title>Not found</title><p>Page not found. <a href='/'>Home</a></p>"
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Robots-Tag", "noindex")
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self):
        self._send(True)

    def do_HEAD(self):
        self._send(False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Serving on :{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
