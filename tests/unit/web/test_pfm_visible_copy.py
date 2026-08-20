"""AC-PFM-23 · C 端可见串不含 edition / PFM / MCS / page-*。"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from travelogue.paths import ROOT

pytestmark = pytest.mark.unit

_STUDIO = ROOT / "templates" / "studio"
_JOURNAL = ROOT / "templates" / "visual-journal"

_COMMENT_RE = re.compile(
    r"/\*[\s\S]*?\*/|//[^\n]*|<!--[\s\S]*?-->",
    re.MULTILINE,
)
_JS_STRING_RE = re.compile(r"""(?P<q>['"`])(?P<body>(?:\\.|(?!\1).)*)(?P=q)""")
_HTML_ATTR_RE = re.compile(
    r"""(?:aria-label|title|placeholder|alt|aria-description)\s*=\s*(['"])(.*?)\1""",
    re.I,
)
_HTML_TAG_RE = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", re.I)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_FORBIDDEN = (
    re.compile(r"\bPFM\b"),
    re.compile(r"\bMCS\b"),
    re.compile(r"\bedition\b", re.I),
    re.compile(r"page-\d"),
    re.compile(r"page-[a-z0-9]+-[a-z0-9-]+"),
)


def _iter_user_files() -> list[Path]:
    files: list[Path] = []
    for root in (_STUDIO, _JOURNAL):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".html", ".js", ".hbs"}:
                continue
            if "node_modules" in path.parts:
                continue
            files.append(path)
    return files


def _visible_strings(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    stripped = _COMMENT_RE.sub("", raw)
    out: list[str] = []
    if path.suffix.lower() in {".html", ".hbs"}:
        for match in _HTML_ATTR_RE.finditer(stripped):
            out.append(match.group(2))
        text = _HTML_TAG_RE.sub(" ", stripped)
        if text.strip():
            out.append(text)
    if path.suffix.lower() == ".js":
        for match in _JS_STRING_RE.finditer(stripped):
            body = match.group("body")
            if _CJK_RE.search(body):
                out.append(body)
    return out


def test_ac_pfm_23_c_end_visible_copy_has_no_jargon() -> None:
    hits: list[str] = []
    for path in _iter_user_files():
        for blob in _visible_strings(path):
            for rx in _FORBIDDEN:
                if rx.search(blob):
                    rel = path.relative_to(ROOT).as_posix()
                    hits.append(f"{rel}: {rx.pattern} ← {blob[:80]!r}")
    assert hits == []
