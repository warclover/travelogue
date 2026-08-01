"""LTN PRD gap close · AC-C-01 strict, AC-C-02 e2e, AC-C-07 parity/burst, weekly G-LTN-07."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

from travelogue.config import get_config
from travelogue.curation.curate import run_curate
from travelogue.layout_contract.active_set import inventory_report
from travelogue.layout_engine.contract.geometry_features import (
    compute_raw_geometry_features,
)
from travelogue.layout_engine.mosaic.ltn_isolation import (
    IsolationFailedWindow,
    compare_ac_c01_to_baseline,
    compute_ac_c01_on_trip,
    isolation_failed_mcs_windows,
    portrait3_after_failed_mcs5_rate_strict,
)
from travelogue.layout_engine.mosaic.ltn_weekly import (
    burst_pass_rate,
    compute_ltn_weekly_metrics,
    content_screen_count,
    scroll_longshot_slot_conservation_rate,
)
from travelogue.layout_engine.planner.screen_planner import (
    _flush_portrait_pending,
    _tile_portrait_run,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "ltn"
DOGFOOD = FIXTURES / "trip.ltn_dogfood_hero_chapter.json"
POS = FIXTURES / "trip.ltn_oracle_positive.json"
NEG = FIXTURES / "trip.ltn_oracle_negative.json"
BASELINE = FIXTURES / "ac_c01_baseline.json"


def _count_qualifying_heroes(chapters: list[dict]) -> int:
    from travelogue.layout_contract.ltn_dogfood import is_hero_mosaic_screen

    n = 0
    for ch in chapters or []:
        for sc in ch.get("screens") or []:
            if not isinstance(sc, dict) or not is_hero_mosaic_screen(sc):
                continue
            pid = str(sc.get("patternId") or "")
            cov = compute_raw_geometry_features(pid).get("heroCoverageRatio")
            if cov is not None and float(cov) >= 0.55:
                n += 1
    return n


def test_ac_c01_strict_counts_adjacent_stack3():
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": "a0"}],
                },
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "a1"},
                        {"assetId": "a2"},
                        {"assetId": "a3"},
                    ],
                },
            ]
        }
    ]
    failed = [
        IsolationFailedWindow(
            start=0, size=5, asset_ids=("a1", "a2", "a3", "a4", "a5")
        )
    ]
    aspects = {f"a{i}": "landscape" for i in range(6)}
    assets = {f"a{i}": {"id": f"a{i}", "width": 1600, "height": 900} for i in range(6)}
    with patch(
        "travelogue.layout_engine.mosaic.ltn_isolation.isolation_failed_mcs_windows",
        return_value=failed,
    ):
        rate = portrait3_after_failed_mcs5_rate_strict(
            chapters,
            ordered_ids=[f"a{i}" for i in range(6)],
            aspects=aspects,  # type: ignore[arg-type]
            assets_map=assets,
        )
    assert rate == 1.0


def test_ac_c01_strict_ignores_far_shared_stack():
    """Share without reading-order adjacency must not count."""
    chapters = [
        {
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a0"}]},
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a1"}]},
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a2"}]},
                # Non-breath spacer so content-screen index gap > 1
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "spacer"}]},
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "a3"},
                        {"assetId": "x"},
                        {"assetId": "y"},
                    ],
                },
            ]
        }
    ]
    failed = [
        IsolationFailedWindow(
            start=0, size=5, asset_ids=("a0", "a1", "a2", "a3", "a4")
        )
    ]
    aspects = {f"a{i}": "landscape" for i in range(5)}
    aspects.update({"x": "portrait", "y": "portrait", "spacer": "landscape"})
    assets = {k: {"id": k, "width": 100, "height": 100} for k in aspects}
    with patch(
        "travelogue.layout_engine.mosaic.ltn_isolation.isolation_failed_mcs_windows",
        return_value=failed,
    ):
        rate = portrait3_after_failed_mcs5_rate_strict(
            chapters,
            ordered_ids=["a0", "a1", "a2", "a3", "a4"],
            aspects=aspects,  # type: ignore[arg-type]
            assets_map=assets,
        )
    assert rate == 0.0


def test_ac_c01_strict_excludes_tiler_person_triple():
    chapters = [
        {
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a0"}]},
                {
                    "patternId": "screen-portrait-3",
                    "layoutHint": "person-triple",
                    "slots": [
                        {"assetId": "a1"},
                        {"assetId": "a2"},
                        {"assetId": "a3"},
                    ],
                },
            ]
        }
    ]
    failed = [
        IsolationFailedWindow(
            start=0, size=5, asset_ids=("a1", "a2", "a3", "a4", "a5")
        )
    ]
    aspects = {f"a{i}": "portrait" for i in range(6)}
    assets = {f"a{i}": {"id": f"a{i}", "width": 900, "height": 1200} for i in range(6)}
    with patch(
        "travelogue.layout_engine.mosaic.ltn_isolation.isolation_failed_mcs_windows",
        return_value=failed,
    ):
        rate = portrait3_after_failed_mcs5_rate_strict(
            chapters,
            ordered_ids=[f"a{i}" for i in range(6)],
            aspects=aspects,  # type: ignore[arg-type]
            assets_map=assets,
        )
    assert rate == 0.0


def test_ac_c01_isolation_smoke_on_h9_fixture():
    trip = json.loads(POS.read_text(encoding="utf-8"))
    report = compute_ac_c01_on_trip(trip)
    assert report["ac"] == "AC-C-01"
    assert "failedWindowCount" in report
    assert "withinAbsoluteBand" in report
    assert report["ok"] is None  # no baseline → relative ok unset
    assert report["rate"] is None or isinstance(report["rate"], float)


def test_ac_c01_compute_reuses_single_isolation_pass():
    trip = json.loads(POS.read_text(encoding="utf-8"))
    with patch(
        "travelogue.layout_engine.mosaic.ltn_isolation.isolation_failed_mcs_windows",
        wraps=isolation_failed_mcs_windows,
    ) as mocked:
        compute_ac_c01_on_trip(trip)
    assert mocked.call_count == 1


def test_ac_c01_baseline_relative_gate():
    assert compare_ac_c01_to_baseline(0.4, 1.0)["ok"] is True
    assert compare_ac_c01_to_baseline(0.6, 1.0)["ok"] is False
    blob = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert blob["reduceFactor"] == 0.5
    base = blob["baselines"]["fixture-synthetic"]
    assert compare_ac_c01_to_baseline(0.5, base)["ok"] is True


def test_ac_c07_parity_tail_tiler_groups():
    assert _tile_portrait_run(3) == [3]
    assert sum(_tile_portrait_run(5)) == 5
    assert sum(_tile_portrait_run(7)) == 7
    assert 1 not in _tile_portrait_run(5)


def test_ac_c07_parity_tail_flush_emits_portrait3():
    aspects = {f"p{i}": "portrait" for i in range(3)}
    assets = {
        f"p{i}": {
            "id": f"p{i}",
            "width": 900,
            "height": 1200,
            "tags": [],
        }
        for i in range(3)
    }
    pending = ["p0", "p1", "p2"]
    screens = _flush_portrait_pending(
        pending, aspects, assets_map=assets, force=True  # type: ignore[arg-type]
    )
    assert pending == []
    assert any(sc.get("patternId") == "screen-portrait-3" for sc in screens)
    aids = [
        sl.get("assetId")
        for sc in screens
        for sl in (sc.get("slots") or [])
    ]
    assert set(aids) == {"p0", "p1", "p2"}


def test_ac_c07_burst_no_dup_prefers_burst_template_not_penalized():
    from travelogue.layout_engine.mosaic.scorer import _duplicate_density_penalty

    ids = [f"b{i}" for i in range(4)]
    assets = {
        aid: {"id": aid, "burstGroupId": "burst-x", "quality": {"sharpness": 0.5}}
        for aid in ids
    }
    with patch(
        "travelogue.layout_engine.mosaic.scorer.template_prefers_burst",
        return_value=True,
    ):
        assert (
            _duplicate_density_penalty(
                ids, assets, pattern_id="screen-mosaic-4-hero-70-sidebar"
            )
            == 0.0
        )
    with patch(
        "travelogue.layout_engine.mosaic.scorer.template_prefers_burst",
        return_value=False,
    ):
        assert (
            _duplicate_density_penalty(
                ids, assets, pattern_id="screen-landscape-4"
            )
            == 0.8
        )


def test_weekly_gltn07_metrics_on_dogfood_fixture():
    trip = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    m = compute_ltn_weekly_metrics(trip)
    assert m["screenCount"] == content_screen_count(trip["chapters"])
    assert m["screenCount"] == 5
    assert m["scrollLongshotSlotConservationRate"] == 1.0
    assert "burstPassRate" in m
    # Strict C01 is opt-in (expensive)
    assert "portrait3AfterFailedMcs5RateStrict" not in m
    m2 = compute_ltn_weekly_metrics(trip, include_ac_c01_strict=True)
    assert m2.get("portrait3AfterFailedMcs5RateStrict") is None or isinstance(
        m2.get("portrait3AfterFailedMcs5RateStrict"), float
    )


def test_burst_pass_rate_null_without_1p_geometry():
    trip = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    rate = burst_pass_rate(trip, burst_seconds=1800.0)
    assert rate is None or 0.0 <= rate <= 1.0


def test_e1_schema_mosaic_not_in_active_field():
    from datetime import date

    report = inventory_report(today=date(2026, 7, 20))
    assert isinstance(report.get("schemaMosaicNotInActive"), list)
    assert report["ok"] is True


def test_ac_c02_h9_positive_recurate_hero_or_explainable(tmp_path):
    """AC-C-02 positive: hero∈[1,2] when emit succeeds; else fail-loud MCS log."""
    trip = copy.deepcopy(json.loads(POS.read_text(encoding="utf-8")))
    trip["pipeline"] = {"status": "structure_draft"}
    trip["intent"] = {**(trip.get("intent") or {}), "layoutDensity": "balanced"}
    cfg = get_config()
    run_curate(
        trip,
        apply_layout=True,
        trip_dir=tmp_path,
        cfg=cfg,
        export_layout="web",
        layout_engine="screens",
    )
    heroes = _count_qualifying_heroes(trip.get("chapters") or [])
    assert heroes <= 2
    if heroes >= 1:
        return
    logs = (trip.get("curation") or {}).get("mosaicDecisionLog") or []
    assert logs, "oracle-positive must attempt MCS when hero=0"
    # Bare fallbackUsed is not enough — require fail-loud reason or rejects.
    assert any(
        isinstance(lg, dict)
        and (
            lg.get("fallbackReason")
            in ("mcs_all_sizes_failed", "no_candidates", "low_score")
            or (
                lg.get("fallbackUsed")
                and (lg.get("rejectedTemplates") or lg.get("geometryRejectedTemplates"))
            )
        )
        for lg in logs
    )


def test_ac_c02_h9_negative_used_zero(tmp_path):
    trip = copy.deepcopy(json.loads(NEG.read_text(encoding="utf-8")))
    trip["pipeline"] = {"status": "structure_draft"}
    cfg = get_config()
    run_curate(
        trip,
        apply_layout=True,
        trip_dir=tmp_path,
        cfg=cfg,
        export_layout="web",
        layout_engine="screens",
    )
    heroes = _count_qualifying_heroes(trip.get("chapters") or [])
    assert heroes == 0


def test_ac_c02_qualifying_hero_coverage_gate_on_dogfood():
    """Hero screens counted for AC-C-02 must clear main area ≥0.55 when known."""
    trip = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    n = _count_qualifying_heroes(trip["chapters"])
    assert n == 1
    pid = "screen-mosaic-4-hero-70-sidebar"
    cov = compute_raw_geometry_features(pid).get("heroCoverageRatio")
    assert cov is not None and float(cov) >= 0.55


def test_ac_c02_unknown_coverage_not_qualifying():
    """Patterns without geometry coverage must not inflate hero counts."""
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-mosaic-unknown-no-geometry",
                    "slots": [{"assetId": "a", "role": "main"}],
                }
            ]
        }
    ]
    with patch(
        "travelogue.layout_contract.ltn_dogfood.is_hero_mosaic_screen",
        return_value=True,
    ), patch(
        "travelogue.layout_engine.contract.geometry_features.compute_raw_geometry_features",
        return_value={"heroCoverageRatio": None},
    ):
        assert _count_qualifying_heroes(chapters) == 0


def test_scroll_longshot_conservation_on_dogfood():
    trip = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    assert scroll_longshot_slot_conservation_rate(trip["chapters"]) == 1.0
