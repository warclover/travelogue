"""LTE synthetic probe regression (AC-P16-07)."""

from __future__ import annotations

import pytest

from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_lte_probe_regress_runs_without_crash() -> None:
    from scripts.lte_probe_regress import run_probe_regress

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    payload = run_probe_regress(engine)
    assert payload["probeCount"] > 0
    assert "warnings" in payload
    assert "samples" in payload
