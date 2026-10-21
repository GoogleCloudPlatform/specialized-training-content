"""Convert the activity-guide Markdown subset into styled, self-contained HTML.

Usage (from activity-guides/): python3 build/md2html.py markdown/*.md
Each .md is written as a .html in html/, using build/template.html.
"""
import html
import re
import sys
from pathlib import Path

HTML_DIR = Path(__file__).parent.parent / "html"

ACCENTS = {
    "01": ("#1A73E8", "#E8F0FE", "1"),
    "02": ("#188038", "#E6F4EA", "2"),
    "03": ("#B06000", "#FEF7E0", "3"),
    "04": ("#C5221F", "#FCE8E6", "4"),
    "in": ("#5F6368", "#F1F3F4", "Instructor"),
}


def inline(text):
    codes = []

    def keep(m):
        codes.append("<code>" + html.escape(m.group(1)) + "</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table(lines, cls=""):
    head, body = cells(lines[0]), [cells(l) for l in lines[2:]]
    if head and head[0] == "Clock":
        cls += " timeline"
    if body and sum(1 for c in body[0] if not c) > 1:
        cls += " grid"
    out = [f'<div class="tw"><table class="{cls.strip()}"><thead><tr>']
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        for c in row:
            if c:
                out.append(f"<td>{inline(c)}</td>")
            else:
                out.append('<td class="blank" contenteditable="true"></td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def stat_cards(lines):
    head, vals = cells(lines[0]), cells(lines[2])
    items = "".join(
        f'<div class="stat"><div class="sv">{inline(v)}</div><div class="sl">{inline(h)}</div></div>'
        for h, v in zip(head, vals)
    )
    return f'<div class="stats">{items}</div>'


def convert(md, key):
    lines = md.split("\n")
    out, i = [], 0
    title, tagline, eyebrow = "", "", ""
    seen_stats = False
    section_open = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            buf = []
            while not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append(f'<pre data-lang="{lang}"><code>{html.escape(chr(10).join(buf))}</code></pre>')
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            i += 1
            continue
        if title and not tagline and not eyebrow and line.strip() and not out:
            parts = [p.strip() for p in line.split("·")]
            m = re.match(r"\*\*(.+)\*\*", parts[0])
            if m:
                tagline, eyebrow = m.group(1), " · ".join(parts[1:])
            else:
                eyebrow = " · ".join(parts)
            i += 1
            continue
        if line.startswith("## "):
            if section_open:
                out.append("</section>")
            name = line[3:].strip()
            cls = "report" if name.startswith("Report-out") else "reminder" if name.startswith("Reminder") else ""
            out.append(f'<section class="{cls}"><h2>{inline(name)}</h2>')
            section_open = True
            i += 1
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.strip() == "---":
            if section_open:
                out.append("</section>")
                section_open = False
            out.append('<hr class="divider">')
            i += 1
            continue
        if line.startswith("|"):
            buf = []
            while i < len(lines) and lines[i].startswith("|"):
                buf.append(lines[i])
                i += 1
            if not seen_stats and not section_open:
                out.append(stat_cards(buf))
                seen_stats = True
            else:
                out.append(table(buf))
            continue
        if line.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            out.append(f'<blockquote>{inline(" ".join(buf))}</blockquote>')
            continue
        if re.match(r"^(- |\d+\. )", line):
            ordered = re.match(r"^(\d+)\. ", line)
            tag = "ol" if ordered else "ul"
            start = f' start="{ordered.group(1)}"' if ordered and ordered.group(1) != "1" else ""
            buf = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                buf.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                i += 1
            out.append(f"<{tag}{start}>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + f"</{tag}>")
            continue
        if line.strip():
            buf = [line.strip()]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|- |\d+\. |```)", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(buf))}</p>")
            continue
        i += 1
    if section_open:
        out.append("</section>")

    accent, tint, badge = ACCENTS[key]
    head_title = re.sub(r"^Activity \d+: ", "", title)
    eyebrow_label = f"Activity {badge}" if badge != "Instructor" else "Instructor only"
    tpl = Path(__file__).with_name("template.html").read_text()
    return (
        tpl.replace("{{TITLE}}", html.escape(head_title))
        .replace("{{H1}}", inline(title))
        .replace("{{TAGLINE}}", inline(tagline))
        .replace("{{EYEBROW}}", inline(eyebrow))
        .replace("{{BADGE}}", eyebrow_label)
        .replace("{{ACCENT}}", accent)
        .replace("{{TINT}}", tint)
        .replace("{{BODY}}", "\n".join(out))
    )


if __name__ == "__main__":
    for path in map(Path, sys.argv[1:]):
        key = path.name[:2]
        out = HTML_DIR / f"{path.stem}.html"
        out.write_text(convert(path.read_text(), key))
        print("wrote", out)
