"""Studio Chrome injection for preview pages."""

from __future__ import annotations

import html
from pathlib import Path

CHROME_ALLOWLIST = frozenset({"index.html", "index-mobile.html"})
# index-longshot.html intentionally excluded: capture surface must stay chrome-free (ADR-018 D6).


SHARE_QUERY_MARKERS = ("share=1", "mode=share")

CHROME_INJECT = (
    '<script src="/__studio/studio-theme-accent.js"></script>\n'
    '<link rel="stylesheet" href="/__studio/studio-modal.css">\n'
    '<link rel="stylesheet" href="/__studio/preview-toolbar.css">\n'
    '<script src="/__studio/studio-modal.js" defer></script>\n'
    '<script type="module" src="/__studio/preview-toolbar.js"></script>'
)


def is_share_preview_query(query: str) -> bool:
    q = (query or "").lower()
    return any(marker in q for marker in SHARE_QUERY_MARKERS)


def should_inject_studio_chrome(rel_path: str, query: str = "") -> bool:
    if Path(rel_path).name.lower() not in CHROME_ALLOWLIST:
        return False
    return True


def inject_studio_chrome(
    html_doc: str,
    *,
    studio_token: str | None = None,
    share_mode: bool = False,
) -> str:
    if 'data-preview-toolbar="on"' in html_doc or 'data-preview-share="on"' in html_doc:
        return html_doc
    lower = html_doc.lower()
    if studio_token and "<head" in lower:
        token = html.escape(studio_token, quote=True)
        meta = f'<meta name="studio-token" content="{token}">'
        if 'name="studio-token"' not in html_doc:
            head_end = lower.index("<head")
            insert_at = html_doc.index(">", head_end) + 1
            html_doc = html_doc[:insert_at] + "\n  " + meta + html_doc[insert_at:]
    preview_attr = 'data-preview-share="on"' if share_mode else 'data-preview-toolbar="on"'
    if "<body" in lower:
        idx = lower.index("<body")
        end = html_doc.index(">", idx) + 1
        tag = html_doc[idx:end]
        if "data-preview-toolbar" not in tag and "data-preview-share" not in tag:
            html_doc = html_doc[: end - 1] + f" {preview_attr}" + html_doc[end - 1 :]
    lower = html_doc.lower()
    if "</body>" in lower:
        pos = lower.rindex("</body>")
        html_doc = html_doc[:pos] + CHROME_INJECT + "\n" + html_doc[pos:]
    return html_doc
