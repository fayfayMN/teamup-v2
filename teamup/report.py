"""Downloadable reports for TeamUp — self-contained HTML, print-to-PDF.

Parity with Team Doctor: we hand the user a single .html file that opens in any
browser and prints cleanly to PDF. No external CSS, no fonts, no JS — everything
is inline so the file works offline and can be emailed as-is.

The working agreement is authored once as simple Markdown (the kickoff page's
``lines`` list); ``md_to_html`` renders exactly the small subset of Markdown that
agreement uses (H1/H2, bold, italic, bullet lists, pipe tables) so there is a
single source of truth and no second copy to drift.
"""

from __future__ import annotations

import html
import re
from typing import List

_PAGE_CSS = """
*{box-sizing:border-box}
body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#20223F;
line-height:1.55;max-width:760px;margin:28px auto;padding:0 22px}
h1{font-size:25px;margin:0 0 6px;color:#1B1B3A}
h2{font-size:17px;margin:22px 0 6px;color:#3C3489;border-bottom:1px solid #eee;padding-bottom:3px}
ul{margin:6px 0 6px 2px;padding-left:20px}li{margin:3px 0}
p{margin:6px 0}
strong{color:#1B1B3A}
em{color:#555}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}
th,td{text-align:left;border-bottom:1px solid #e6e6e6;padding:6px 8px}
th{border-bottom:2px solid #ddd}
.sub{color:#888;font-size:12px;margin-top:26px;border-top:1px solid #eee;padding-top:10px}
@media print{body{margin:0}}
"""

_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITAL = re.compile(r"_([^_]+)_")


def _inline(text: str) -> str:
    """Escape HTML, then apply **bold** and _italic_."""
    out = html.escape(text)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITAL.sub(r"<em>\1</em>", out)
    return out


def _is_table_sep(cells: List[str]) -> bool:
    return all(set(c.strip()) <= set("-:") and c.strip() for c in cells)


def md_to_html(md: str) -> str:
    """Render the agreement's small Markdown subset to HTML fragments."""
    out: List[str] = []
    lines = md.split("\n")
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Pipe table: collect the contiguous block of | ... | rows.
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            out.append("<table>")
            for r_idx, cells in enumerate(rows):
                if _is_table_sep(cells):
                    continue
                tag = "th" if r_idx == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>"
                                             for c in cells) + "</tr>")
            out.append("</table>")
            continue

        # Bullet list: collect contiguous "- " items.
        if stripped.startswith("- "):
            out.append("<ul>")
            while i < n and lines[i].strip().startswith("- "):
                out.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("</ul>")
            continue

        if stripped.startswith("## "):
            out.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            out.append(f"<h1>{_inline(stripped[2:])}</h1>")
        elif stripped == "":
            pass  # blank line — paragraph break handled by block spacing
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
        i += 1
    return "\n".join(out)


def wrap_html(title: str, body_html: str, footer: str = "") -> str:
    """Wrap rendered fragments in a full, self-contained HTML document."""
    foot = (f'<p class="sub">{html.escape(footer)}</p>' if footer else "")
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{_PAGE_CSS}</style></head>"
            f"<body>{body_html}{foot}</body></html>")


def agreement_html(title: str, md: str) -> str:
    """Full downloadable HTML for a working agreement authored as Markdown."""
    return wrap_html(title, md_to_html(md),
                     footer="Made with TeamUp · free, key-less, and yours to edit. "
                            "Open in a browser and print to PDF to save a copy.")


_SEV = {"high": ("#A32D2D", "#FCEBEB"), "med": ("#8A5A00", "#FDF3E0"),
        "low": ("#20223F", "#EFF1FB")}


def team_report_html(team_name: str, scenario: dict, coached: dict) -> str:
    """Downloadable 'Team plan' for a fixed team: scores explained, who owns what,
    and how to make the best of the hand you have."""
    e = html.escape
    b: List[str] = []
    b.append(f"<h1>Team plan — {e(team_name or 'our team')}</h1>")
    b.append(f"<p><strong>{e(scenario['label'])}</strong> · "
             f"{len(coached['summary']['members'])} people</p>")
    b.append(f"<p><em>Watch out for:</em> {e(scenario['top_risk'])}</p>")
    b.append(f"<p><em>Do this:</em> {e(scenario['emphasis'])}</p>")

    b.append("<h2>How your team scored</h2><ul>")
    for line in coached["explanations"]:
        b.append(f"<li>{e(line)}</li>")
    b.append("</ul>")
    if coached.get("size_note"):
        b.append(f"<p><em>{e(coached['size_note'])}</em></p>")

    b.append("<h2>Who owns what (day one)</h2>")
    b.append("<table><tr><th>Role</th><th>Owner</th><th>Note</th></tr>")
    for a in coached["assignments"]:
        owner = a["owner"] or "— recruit / drop —"
        tag = " <strong>(stretch)</strong>" if a["stretch"] else ""
        b.append(f"<tr><td>{e(a['role'])}</td><td>{e(owner)}{tag}</td>"
                 f"<td>{e(a['why'])}</td></tr>")
    b.append("</table>")

    if coached["advice"]:
        b.append("<h2>Make the best of it</h2>")
        for ad in coached["advice"]:
            color, bg = _SEV.get(ad["sev"], _SEV["low"])
            b.append(f"<p style='background:{bg};border-radius:6px;padding:8px 12px'>"
                     f"<strong style='color:{color}'>{e(ad['title'])}:</strong> "
                     f"{e(ad['body'])}</p>")

    from teamup.comm import style as _cstyle
    cs = _cstyle(coached["comm"]["style"])
    b.append("<h2>How to communicate</h2>")
    b.append(f"<p><strong>Recommended: {e(cs['name'])}</strong> — {e(coached['comm']['why'])}</p>")

    return wrap_html(f"Team plan — {team_name or 'our team'}", "\n".join(b),
                     footer="Made with TeamUp · free, key-less, deterministic (no AI guessing). "
                            "Open in a browser and print to PDF to save a copy.")
