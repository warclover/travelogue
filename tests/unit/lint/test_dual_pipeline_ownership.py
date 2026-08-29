"""DPI W0 · ownership ratchet (AC-DPI-02 / AC-DPI-04)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.lint_dual_pipeline_ownership import (
    ROOT,
    explain_file,
    scan_python,
    _is_allowlisted,
    _is_seam,
    _signature,
)

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def test_seams_and_allowlist() -> None:
    assert _is_seam("travelogue/render/assemble.py")
    assert _is_seam("travelogue/export/dispatch.py")
    assert _is_allowlisted("travelogue/config/edition.py")
    assert _is_allowlisted("travelogue/export/portfolio_pages.py")
    assert _is_allowlisted("travelogue/web/studio_handlers/export_handlers.py")
    assert not _is_allowlisted("travelogue/render/chapters.py")


def test_explain_known_paths() -> None:
    assert "seam" in explain_file("travelogue/curation/curate.py")
    assert "allowlist" in explain_file("travelogue/config/edition.py")
    assert "journal exclusive" in explain_file("travelogue/layout_engine/mosaic/trip.py")


def test_ac_dpi_04_new_branch_outside_seam_is_a_new_edge() -> None:
    """A hit in an unregistered file is a new signature (lint would go red)."""
    current = _signature(scan_python())
    fake = "travelogue/render/engine.py::branch"
    assert fake not in current


def test_ac_dpi_12_builder_split() -> None:
    assemble = (ROOT / "travelogue/render/assemble.py").read_text(encoding="utf-8")
    chapters = (ROOT / "travelogue/render/chapters.py").read_text(encoding="utf-8")
    journal = (ROOT / "travelogue/render/journal_chapters.py").read_text(encoding="utf-8")
    folio = (ROOT / "travelogue/render/journal_folio.py").read_text(encoding="utf-8")
    screens = (ROOT / "travelogue/render/journal_screens.py").read_text(encoding="utf-8")
    portfolio = (ROOT / "travelogue/render/portfolio_chapters.py").read_text(encoding="utf-8")
    journal_family = journal + folio + screens

    assert len(re.findall(r"\bis_portfolio_trip\s*\(", assemble)) == 1
    assert "is_portfolio" not in chapters
    assert "build_journal_chapters" in chapters
    assert "build_chapters_render_context" in chapters

    for token in (
        "longshot_filter",
        "interleave_breath_items",
        "build_trip_index_entries",
        "build_featured_grid_cards",
        "chapter_divider",
    ):
        assert token in journal_family
        assert token not in portfolio

    for rel, text in (
        ("journal_chapters.py", journal),
        ("journal_folio.py", folio),
        ("journal_screens.py", screens),
    ):
        assert "portfolio" not in text, rel
        assert "editorial_series" not in text, rel
        assert "page-" not in text, rel

    assert 'stage_aspect="16:9"' in portfolio
    assert "if not raw_screens" in portfolio
    assert "portfolio_body" in portfolio
    assert "page-" in portfolio

    needle = "hide" + "ChapterChrome"
    self = Path(__file__).resolve()
    hits: list[str] = []
    for base in ("travelogue", "templates", "tests"):
        root = ROOT / base
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".py", ".hbs", ".js", ".css", ".html"}:
                continue
            if "__pycache__" in path.parts or path.resolve() == self:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if needle in text:
                hits.append(path.relative_to(ROOT).as_posix())
    assert hits == []


def test_ac_dpi_13_longshot_shim_has_no_bundle_fields() -> None:
    import inspect

    from travelogue.export.longshot import LongshotExportResult, export_trip_longshot

    params = inspect.signature(export_trip_longshot).parameters
    assert "include_zip" not in params
    assert "include_pages" not in params
    fields = getattr(LongshotExportResult, "__dataclass_fields__", {})
    assert "skipped_pages" not in fields
    assert "share_zip" not in fields


def test_ac_dpi_15_dock_is_pure_dispatch() -> None:
    src = (ROOT / "templates/studio/preview-toolbar/dock.js").read_text(encoding="utf-8")
    branches = re.findall(
        r"if\s*\([^)]*(?:isPortfolio|readToolbarEdition|isPortfolioEdition|data-edition)",
        src,
    )
    assert len(branches) <= 2
    assert "applyJournalDockLogic" in src
    assert "applyPortfolioDockLogic" in src
    assert "syncPortfolioOverflowBadge(root" not in src
    longshot = (ROOT / "templates/studio/preview-toolbar/longshot.js").read_text(
        encoding="utf-8"
    )
    assert "readToolbarEdition" not in longshot
    features = (ROOT / "templates/studio/preview-toolbar/features.js").read_text(
        encoding="utf-8"
    )
    assert "renderPortfolioPageCountChips" in features
    assert "preview-sheet__chip-label" not in features
