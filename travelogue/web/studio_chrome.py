"""Studio Chrome injection for preview pages."""

from __future__ import annotations

from pathlib import Path

CHROME_ALLOWLIST = frozenset({"index.html", "index-mobile.html"})

CHROME_INJECT = (
    '<link rel="stylesheet" href="/__studio/preview-toolbar.css">\n'
    '<script src="/__studio/preview-toolbar.js" defer></script>'
)


def should_inject_studio_chrome(rel_path: str) -> bool:
    return Path(rel_path).name.lower() in CHROME_ALLOWLIST


def inject_studio_chrome(html: str) -> str:
    if 'data-preview-toolbar="on"' in html:
        return html
    lower = html.lower()
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
