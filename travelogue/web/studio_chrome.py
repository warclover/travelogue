"""Studio Chrome injection for preview pages."""

from __future__ import annotations

from pathlib import Path

CHROME_ALLOWLIST = frozenset({"index.html", "index-mobile.html"})

SHARE_QUERY_MARKERS = ("share=1", "mode=share")

CHROME_INJECT = (
    '<link rel="stylesheet" href="/__studio/preview-toolbar.css">\n'
    '<script src="/__studio/studio-modal.js" defer></script>\n'
    '<script src="/__studio/preview-toolbar.js" defer></script>'
)


def should_inject_studio_chrome(rel_path: str, query: str = "") -> bool:
    if Path(rel_path).name.lower() not in CHROME_ALLOWLIST:
        return False
    q = (query or "").lower()
    return not any(marker in q for marker in SHARE_QUERY_MARKERS)


def inject_studio_chrome(html: str, *, studio_token: str | None = None) -> str:
    if 'data-preview-toolbar="on"' in html:
        return html
    lower = html.lower()
    if studio_token and "<head" in lower:
        meta = f'<meta name="studio-token" content="{studio_token}">'
        if 'name="studio-token"' not in html:
            head_end = lower.index("<head")
            insert_at = html.index(">", head_end) + 1
            html = html[:insert_at] + "\n  " + meta + html[insert_at:]
    if "<body" in lower:
        idx = lower.index("<body")
        end = html.index(">", idx) + 1
        if "data-preview-toolbar" not in html[idx:end]:
            html = html[: end - 1] + ' data-preview-toolbar="on"' + html[end - 1 :]
    lower = html.lower()
    if "</body>" in lower:
        pos = lower.rindex("</body>")
        html = html[:pos] + CHROME_INJECT + "\n" + html[pos:]
    return html
