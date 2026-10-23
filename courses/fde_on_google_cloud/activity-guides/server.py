"""Serve the FDE team activity guides.

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
    ("01-unblock-the-launch", "Unblock the Launch", "Who owns the fix?", "#1A73E8", "#E8F0FE"),
    ("02-scope-defense-sparring", "Scope Defense Sparring", "Absorb, defer, or route?", "#188038", "#E6F4EA"),
    ("03-trick-question-to-eval-case", "Trick Question to Eval Case", "Turn a scary anecdote into a permanent test", "#B06000", "#FEF7E0"),
    ("04-escalation-triage-under-load", "Escalation Triage Under Load", "Defect, or working as designed?", "#C5221F", "#FCE8E6"),
]

HOME = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FDE Team Activities</title>
<style>
  body { margin: 0; background: #F8F9FA; color: #202124;
         font: 16px/1.55 "Google Sans", Roboto, "Segoe UI", system-ui, -apple-system, sans-serif;
         -webkit-font-smoothing: antialiased; }
  .page { max-width: 760px; margin: 48px auto; background: #fff; border-radius: 16px;
          box-shadow: 0 1px 2px rgba(60,64,67,.15), 0 2px 8px rgba(60,64,67,.08); overflow: hidden; }
  header { padding: 40px 44px 24px; border-bottom: 1px solid #DADCE0; }
  .kicker { font-size: 13px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #5F6368; margin: 0; }
  h1 { font-size: 34px; line-height: 1.2; margin: 8px 0; font-weight: 600; }
  .sub { color: #5F6368; margin: 0; }
  ol { list-style: none; margin: 0; padding: 12px 0; }
  li { position: relative; }
  /* Timeline line: one segment per row, joined through the circle centers. */
  li::before { content: ""; position: absolute; left: 71px; top: 0; bottom: 0; width: 2px; background: #DADCE0; z-index: 1; }
  li:first-child::before { top: 50%; }
  li:last-child::before { bottom: 50%; }
  a.row { position: relative; display: grid; grid-template-columns: 56px 1fr; align-items: center; gap: 20px;
          padding: 14px 44px; text-decoration: none; color: inherit; transition: background .15s; }
  a.row:hover { background: var(--tint); }
  .dot { position: relative; z-index: 2; width: 56px; height: 56px; border-radius: 50%; display: grid; place-items: center;
         background: #fff; border: 2px solid var(--c); color: var(--c); font-size: 20px; font-weight: 600;
         transition: background .15s, color .15s; }
  a.row:hover .dot { background: var(--c); color: #fff; }
  .label { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--c); }
  h2 { font-size: 19px; line-height: 1.3; margin: 2px 0 2px; font-weight: 600; }
  .tag { color: #5F6368; margin: 0; font-size: 15px; }
  footer { display: flex; flex-wrap: wrap; gap: 8px; padding: 18px 44px 24px; border-top: 1px solid #DADCE0; }
  .chip { font-size: 13px; color: #5F6368; background: #F1F3F4; border-radius: 999px; padding: 4px 12px; }
  /* 15% smaller than the guide pages' scaling (1 and 1.25 on wide screens). */
  html { zoom: .85; }
  @media screen and (min-width: 1200px) { html { zoom: 1.0625; } }
</style>
</head>
<body>
<div class="page">
<header>
  <p class="kicker">Forward Deployed Engineering on Google Cloud</p>
  <h1>Team Activities</h1>
  <p class="sub">Open the activity your instructor names.</p>
</header>
<ol>
{cards}
</ol>
<footer><span class="chip">13 minutes each</span><span class="chip">Teams of 3–4</span><span class="chip">Case: Cymbal Logistics</span></footer>
</div>
</body>
</html>
"""

CARD = """  <li><a class="row" style="--c:{color};--tint:{tint}" href="/{slug}"><span class="dot">{n}</span><div><div class="label">Activity {n}</div><h2>{title}</h2><p class="tag">{tagline}</p></div></a></li>"""


def build_pages():
    cards = "\n".join(
        CARD.format(color=c, tint=tn, slug=s, n=i, title=html.escape(t), tagline=html.escape(g))
        for i, (s, t, g, c, tn) in enumerate(GUIDES, 1)
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
