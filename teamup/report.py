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
