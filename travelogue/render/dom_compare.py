"""DOM structure signatures for golden regression."""

from __future__ import annotations

import re
from html.parser import HTMLParser


def _strip_preview_chrome(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    html = re.sub(r'(?is)<div class="golden-banner"[^>]*>.*?</div>\s*', "", html)
    return html


class _SigParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.signatures: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k: v for k, v in attrs if v is not None}
        block = ad.get("data-block")
        if block:
            self.signatures.append(f"{tag}:block={block}")

        if tag == "section":
            pid = ad.get("data-pattern")
            cid = ad.get("data-chapter-id", ad.get("id", ""))
            if pid:
                self.signatures.append(f"section:{cid}:{pid}")
            if ad.get("data-demo"):
                self.signatures.append(f"section:demo:{ad.get('data-demo')}")

        if tag == "figure" and "media-card" in ad.get("class", ""):
            mods = []
            for token in ("bleed", "fill", "overlay", "video"):
                if f"media-card--{token}" in ad.get("class", ""):
                    mods.append(token)
            if mods:
                self.signatures.append(f"figure:media-card:{'+'.join(sorted(mods))}")


def dom_signature(html: str, *, strip_chrome: bool = True) -> list[str]:
    if strip_chrome:
        html = _strip_preview_chrome(html)
    parser = _SigParser()
    parser.feed(html)
    parser.close()
    return parser.signatures


def compare_signatures(
    expected: list[str],
    actual: list[str],
) -> list[str]:
    """Return human-readable diff lines; empty if equal."""
    diffs: list[str] = []
    max_len = max(len(expected), len(actual))
    for i in range(max_len):
        e = expected[i] if i < len(expected) else None
        a = actual[i] if i < len(actual) else None
        if e != a:
            diffs.append(f"  [{i}] expected {e!r} got {a!r}")
    if len(expected) != len(actual) and not diffs:
        diffs.append(f"  length expected {len(expected)} got {len(actual)}")
    return diffs


def assert_dom_compatible(golden_html: str, rendered_html: str) -> None:
    expected = dom_signature(golden_html)
    actual = dom_signature(rendered_html)
    diffs = compare_signatures(expected, actual)
    if diffs:
        msg = "DOM signature mismatch vs golden.html:\n" + "\n".join(diffs[:20])
        if len(diffs) > 20:
            msg += f"\n  ... and {len(diffs) - 20} more"
        raise AssertionError(msg)
