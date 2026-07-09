"""P0/P1/P2 gap closure tests (Phase 16 PRD audit follow-up)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.phase16_template_eval import compare_ac15_thresholds, evaluate_registry
from travelogue.layout_engine.mosaic.diversity import rerank_scored_candidates_dpp
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled
from travelogue.layout_templates.css_stale import trip_layout_css_stale
from travelogue.layout_templates.geometry_solidify import solidify_screen_geometry
from travelogue.layout_templates.layout_admin import layout_quota_warnings
from travelogue.layout_templates.p17_research import hungarian_slot_assignment
from travelogue.layout_templates.primitive import uniform_grid_primitive
from travelogue.layout_templates.registry import get_engine, reset_engine_cache_for_tests
from travelogue.templating.metrics import _bound_metric_labels


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_primitive_yaml_ids_registered() -> None:
    engine = get_engine()
    for tid in ("screen-portrait-1", "screen-landscape-1", "screen-portrait-2"):
        tpl = engine.get(tid)
        assert tpl.status == "ga"
        assert tpl.photo_count_max >= 1


@pytest.mark.unit
def test_geometry_solidify_includes_gap() -> None:
    tpl = get_engine().get("screen-mosaic-5-hero-3-2-plus-4")
    screen = {"patternId": tpl.id, "slots": [{"slot": 0, "assetId": "a1"}]}
    solidify_screen_geometry(screen, tpl.id)
    assert screen["layoutGeometry"].get("gap") == tpl.stage.gap


@pytest.mark.unit
def test_css_stale_skips_when_geometry_solidified(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    data = {
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-2p3l-equal",
                        "layoutGeometry": {
                            "cols": [1, 1, 1],
                            "rows": [1, 1, 1],
                            "gridClass": "layout-screen__grid--missing",
                        },
                    }
                ]
            }
        ]
    }
    (trip_dir / "journal-screens.css").write_text("/* empty */", encoding="utf-8")
    assert trip_layout_css_stale(trip_dir, data) is False


@pytest.mark.unit
def test_dpp_prefers_diverse_pattern() -> None:
    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate

    state = ScreenLayoutPlannerState(nine_min=0, nine_max=9)
    state.pattern_counts = {"screen-portrait-3": 2}

    def _cand(pid: str, score: float):
        return (
            ScreenCandidate(
                pattern_id=pid,
                ordered_asset_ids=["a", "b", "c"],
                screen={"patternId": pid, "slots": []},
                hard_valid=True,
            ),
            score,
            [],
        )

    scored = [
        _cand("screen-portrait-3", 0.9),
        _cand("screen-mosaic-5-2p3l-equal", 0.9),
    ]
    reranked = rerank_scored_candidates_dpp(scored, layout_state=state)
    assert reranked[0][0].pattern_id == "screen-mosaic-5-2p3l-equal"


@pytest.mark.unit
def test_compare_ac15_thresholds_passes_on_dogfood() -> None:

    from scripts.phase16_template_eval import DEFAULT_DOGFOOD_DIR

    report = evaluate_registry(trips_dir=DEFAULT_DOGFOOD_DIR)
    ac15 = compare_ac15_thresholds(report)
    assert report["dogfood"]["tripCount"] >= 3
    assert ac15["ok"] is True


@pytest.mark.unit
def test_hungarian_slot_assignment_min_cost() -> None:
    assets = [1.78, 0.75, 1.33]
    slots = [1.78, 0.67, 1.5]
    perm = hungarian_slot_assignment(assets, slots)
    assert sorted(perm) == [0, 1, 2]
    assert _ar_cost(assets[perm[0]], slots[0]) <= 0.2


def _ar_cost(a: float, s: float) -> float:
    return abs(a - s) / max(a, s)


@pytest.mark.unit
def test_uniform_grid_primitive_shape() -> None:
    tpl = uniform_grid_primitive(template_id="test-uniform-2x2", cols=2, rows=2, slot_count=4)
    assert tpl.kind == "primitive"
    assert len(tpl.slots) == 4
    assert tpl.stage.cols == (1.0, 1.0)


@pytest.mark.unit
def test_metric_label_cardinality_bounds() -> None:
    out = _bound_metric_labels(
        {
            "templateRegistryVersion": "abcdef0123456789abcdef0123456789",
            "rolloutPercent": 37,
            "templateId": "screen-portrait-3",
        }
    )
    assert len(out["templateRegistryVersion"]) == 16
    assert out["rolloutBucket"] == 30


@pytest.mark.unit
def test_layout_quota_warnings_list() -> None:
    warnings = layout_quota_warnings()
    assert isinstance(warnings, list)


@pytest.mark.unit
def test_mosaic_pattern_disabled_via_lte_adapter() -> None:
    assert mosaic_pattern_disabled("screen-mosaic-5-3portrait-2land-balanced") is True


@pytest.mark.unit
def test_per_template_telemetry_emit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.util import template_metrics as metrics_mod

    metrics_path = tmp_path / "metrics.jsonl"
    monkeypatch.setattr(metrics_mod, "metrics_path", lambda: metrics_path)

    from travelogue.layout_engine.mosaic.telemetry import record_per_template_layout_metrics

    record_per_template_layout_metrics(
        trip_id="t1",
        chapters=[{"screens": [{"patternId": "screen-portrait-3"}]}],
        mosaic_logs=[
            {
                "winnerPatternId": "screen-portrait-3",
                "candidatesCount": 3,
                "slotArMatchScore": 0.12,
                "winnerScore": 0.78,
                "faceCropProxy": True,
            },
            {
                "winnerPatternId": "screen-portrait-3",
                "candidatesCount": 2,
                "winnerScore": 0.82,
            },
        ],
    )
    lines = metrics_path.read_text(encoding="utf-8").strip().splitlines()
    names = {json.loads(line)["name"] for line in lines}
    assert "layout.template.exposure_count" in names
    assert "layout.template.slot_ar_distance_p50" in names
    assert "layout.template.win_score_p50" in names
    assert "layout.template.face_crop_proxy_rate" in names


@pytest.mark.unit
def test_aggregate_layout_template_metrics_rollup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.templating import metrics as metrics_mod

    metrics_path = tmp_path / "metrics.jsonl"
    monkeypatch.setattr(metrics_mod, "metrics_path", lambda: metrics_path)
    from travelogue.templating.metrics import record_template_metric

    record_template_metric(
        "layout.template.exposure_count",
        templateId="screen-portrait-3",
        value=2,
    )
    record_template_metric(
        "layout.template.exposure_share",
        templateId="screen-portrait-3",
        value=0.5,
    )
    record_template_metric(
        "layout.template.win_score_p50",
        templateId="screen-portrait-3",
        value=0.8,
    )
    rollup = metrics_mod.aggregate_layout_template_metrics(window_hours=24)
    assert rollup["templates"]
    row = rollup["templates"][0]
    assert row["templateId"] == "screen-portrait-3"
    assert row["exposureCount"] == 2
    assert row["winScoreP50"] == 0.8
    dashboard = metrics_mod.aggregate_metrics(window_hours=24)
    assert "layoutTemplates" in dashboard
    assert dashboard["layoutTemplates"]["templates"][0]["templateId"] == "screen-portrait-3"
