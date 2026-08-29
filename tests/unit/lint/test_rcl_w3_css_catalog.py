"""RCL W3 · CSS catalog before the first LTE / overlays marker (AC-RCL-17)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.layout_templates.css_gen import (
    LTE_MARKER_TOKEN,
    sync_journal_screens_css,
    sync_portfolio_pages_css,
)
from travelogue.paths import JOURNAL_CSS, JOURNAL_SCREENS_CSS, PORTFOLIO_PAGES_CSS

pytestmark = [pytest.mark.unit]

CATALOG_TOKEN = "RCL-W3-CATALOG"
_FAMILY_RUNTIME = frozenset(
    {
        "journal.css",
        "journal-screens.css",
        "portfolio-pages.css",
    }
)


def _first_comment(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("/*"):
        end = stripped.find("*/")
        assert end != -1
        return stripped[: end + 2]
    if stripped.startswith("/**"):
        end = stripped.find("*/")
        assert end != -1
        return stripped[: end + 2]
    raise AssertionError("file does not start with a comment")


def _catalog_before_marker(text: str) -> None:
    comment = _first_comment(text)
    assert CATALOG_TOKEN in comment
    assert len(comment.splitlines()) <= 10
    marker = text.find(LTE_MARKER_TOKEN)
    if marker != -1:
        assert text.find(CATALOG_TOKEN) < marker


def test_three_css_files_have_catalog_at_top() -> None:
    for path in (JOURNAL_CSS, JOURNAL_SCREENS_CSS, PORTFOLIO_PAGES_CSS):
        _catalog_before_marker(Path(path).read_text(encoding="utf-8"))


def test_catalog_survives_journal_and_portfolio_sync(tmp_path: Path) -> None:
    journal = tmp_path / "journal-screens.css"
    portfolio = tmp_path / "portfolio-pages.css"
    journal.write_text(Path(JOURNAL_SCREENS_CSS).read_text(encoding="utf-8"), encoding="utf-8")
    portfolio.write_text(Path(PORTFOLIO_PAGES_CSS).read_text(encoding="utf-8"), encoding="utf-8")
    sync_journal_screens_css({}, journal_path=journal)
    sync_portfolio_pages_css({}, portfolio_path=portfolio)
    _catalog_before_marker(journal.read_text(encoding="utf-8"))
    _catalog_before_marker(portfolio.read_text(encoding="utf-8"))


def test_no_third_runtime_family_css() -> None:
    names = {p.name for p in Path(JOURNAL_CSS).parent.glob("*.css")}
    runtime = names & {
        "journal.css",
        "journal-screens.css",
        "portfolio-pages.css",
        "journal-screens-family.css",
        "portfolio-screens.css",
    }
    assert runtime == _FAMILY_RUNTIME
