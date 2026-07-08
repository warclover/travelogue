"""Phase 16 P3 gaps: layoutDecisionLog debug merge, deprecated render, collage eval."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.collage_detect_eval import evaluate_fixtures
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_3P_2L_BALANCED
from travelogue.curation.mosaic.log import MosaicWindowLog, format_log_entry
from travelogue.curation.mosaic.render_check import screen_pattern_render_ok
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_merge_mosaic_debug_layout_decision_log_pattern() -> None:
    """PRD §9.3 · rejectedTemplates only in debug layoutDecisionLog merge."""
    raw = MosaicWindowLog(
        rejected_templates=[{"templateId": "screen-portrait-3", "reason": "pattern_disabled"}]
    ).to_dict()
    debug_entry = format_log_entry(raw, "debug")
    window_entry = format_log_entry(raw, "window")
    assert "rejectedTemplates" in debug_entry
    assert "rejectedTemplates" not in window_entry

    curation = {
        "layoutDecisionLog": [{"kind": "layout_search", "step": "pick"}],
        "mosaicDecisionLog": [debug_entry],
    }
    merged = list(curation.get("layoutDecisionLog") or []) + list(
        curation.get("mosaicDecisionLog") or []
    )
    assert len(merged) == 2
    assert merged[1]["rejectedTemplates"][0]["reason"] == "pattern_disabled"


@pytest.mark.unit
def test_deprecated_pattern_css_still_renders_for_legacy_trips() -> None:
    """AC-P16-06 · deprecated 模板旧 trip 仍可渲染（grid CSS 仍在 journal-screens）。"""
    assert screen_pattern_render_ok(PATTERN_MOSAIC_5_3P_2L_BALANCED) is True


@pytest.mark.unit
def test_collage_fixture_eval_meets_baseline() -> None:
    report = evaluate_fixtures(Path("docs/acceptance-records/collage-detect-fixtures.json"))
    assert report["fixtureCount"] >= 18
    assert report["precision"] >= 0.6
    assert report["recall"] >= 0.7
