"""Phase 16 follow-up gaps: fit layer, pattern_catalog, collage 2-panel, P17 stub."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.curation.mosaic.lte_adapter import resolve_slot_fit
from travelogue.curation.mosaic.pattern_catalog import LEGACY_MOSAIC_REGISTRY_IDS, default_registry
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.p17_research import hungarian_slot_assignment
from travelogue.layout_templates.registry import reset_engine_cache_for_tests
from scripts.collage_detect_eval import evaluate_fixtures


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_default_registry_generated_from_lte() -> None:
    reg = default_registry()
    assert set(reg) == set(LEGACY_MOSAIC_REGISTRY_IDS) & set(reg)
    assert reg["screen-portrait-3"].slot_count == 3


@pytest.mark.unit
def test_resolve_slot_fit_reads_yaml_portrait_auto() -> None:
    fit = resolve_slot_fit("screen-portrait-3", 0, "portrait", {"id": "a1"})
    assert fit in ("cover", "contain")


@pytest.mark.unit
def test_solidify_writes_fit_from_lte() -> None:
    screen = {
        "patternId": "screen-mosaic-5-hero-3-2-plus-4",
        "slots": [{"slot": 0, "assetId": "a1", "role": "main"}],
    }
    solidify_screen_geometry(screen, screen["patternId"])
    assert screen["slots"][0].get("fit") in ("cover", "contain", "auto")


@pytest.mark.unit
def test_collage_2panel_fixture_passes() -> None:
    report = evaluate_fixtures(Path("docs/acceptance-records/collage-detect-fixtures.json"))
    row = next(r for r in report["rows"] if r["id"] == "synthetic-2panel-collage")
    assert row["ok"] is True


@pytest.mark.unit
def test_p17_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        hungarian_slot_assignment([], [])
