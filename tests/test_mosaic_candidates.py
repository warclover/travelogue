"""Phase 15 mosaic candidate generation."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_mixed_aspects_trip
from travelogue.config import MosaicConfig, get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.curation.mosaic.candidates import generate_window_candidates
from travelogue.curation.mosaic.constants import (
    PATTERN_LANDSCAPE_9,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
)
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.usage_rules.context import build_window_context


def _five_assets():
    kinds = ["portrait", "portrait", "landscape", "landscape", "landscape"]
    aspects = {}
    assets_map = {}
    for i, kind in enumerate(kinds):
        aid = f"a{i}"
        aspects[aid] = kind
        assets_map[aid] = {
            "id": aid,
            "width": 1600 if kind == "landscape" else 900,
            "height": 900 if kind == "landscape" else 1600,
            "takenAt": "2024-06-01T10:00:00Z",
            "layoutEligible": True,
        }
    return aspects, assets_map


def test_generate_window_candidates_multiple_patterns(lte_pattern_enabled):
    aspects, assets_map = _five_assets()
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(5,))
    cands = generate_window_candidates(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3600.0,
    )
    assert len(cands) >= 1
    pids = {c.pattern_id for c in cands}
    assert all(p.startswith("screen-mosaic-5-") for p in pids)


def test_time_gap_still_yields_candidates_lower_score(lte_pattern_enabled):
    """Soft time: far-apart assets still get candidates (scored lower in planner)."""
    aspects, assets_map = _five_assets()
    assets_map["a3"]["takenAt"] = "2024-06-01T12:00:00Z"
    assets_map["a4"]["takenAt"] = "2024-06-01T13:00:00Z"
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(5,), min_candidate_score=0.0)
    cands = generate_window_candidates(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3.0,
    )
    assert cands


def test_generate_mixed_four_window_includes_p2_l2():
    buckets, aspects, assets = build_mixed_aspects_trip()
    assets_map = {a["id"]: a for a in assets}
    mixed_four = buckets[0] + [assets[3]["id"]] if len(assets) > 3 else buckets[0] + ["p-extra"]
    if len(mixed_four) < 4:
        mixed_four = ["p1", "p2", "l1", "l2"]
        for aid in mixed_four:
            aspects.setdefault(aid, "portrait" if aid.startswith("p") else "landscape")
            assets_map.setdefault(aid, {"id": aid, "width": 900, "height": 1600, "takenAt": "2024-06-01T10:00:00Z"})
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(4,))
    cands = generate_window_candidates(
        mixed_four[:4],
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=3600.0,
    )
    pids = {c.pattern_id for c in cands}
    assert PATTERN_PORTRAIT_2_LANDSCAPE_2 in pids


def test_window_has_candidates_requires_geometry_valid():
    from travelogue.curation.mosaic.hook import window_has_candidates

    buckets, aspects, assets = build_mixed_aspects_trip()
    assets_map = {a["id"]: a for a in assets}
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(3, 4))
    window4 = buckets[0] + [assets[3]["id"]] if len(buckets[0]) == 3 else buckets[0]
    assert not window_has_candidates(
        window4[:4],
        aspects,
        assets_map,
        size=4,
        cfg=cfg,
        burst_seconds=3600.0,
        median_sharp=None,
    )
    assert window_has_candidates(
        buckets[0],
        aspects,
        assets_map,
        size=3,
        cfg=cfg,
        burst_seconds=3600.0,
        median_sharp=None,
    )


def test_window_has_candidates_aligns_with_usage_filter(monkeypatch):
    """Probe must apply the same usage-rule filter as compose (PRD §7.1)."""
    from travelogue.curation.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )
    from travelogue.curation.mosaic.hook import window_has_candidates

    aspects = {f"a{i}": "landscape" for i in range(9)}
    assets_map = {
        f"a{i}": {
            "id": f"a{i}",
            "width": 3000,
            "height": 1687,
            "takenAt": "2024-06-01T10:00:00Z",
            "quality": {"sharpness": 0.8},
        }
        for i in range(9)
    }
    ids = [f"a{i}" for i in range(9)]
    cfg = MosaicConfig(enabled=True, enabled_window_sizes=(9,))
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.last_was_dense_collage = True
    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=True))
    patched = replace(base, layout=layout)
    monkeypatch.setattr("travelogue.config.get_config", lambda: patched)
    monkeypatch.setattr(
        "travelogue.curation.usage_rules.evaluator.get_config",
        lambda: patched,
    )
    ctx = build_window_context(ids, aspects, assets_map, layout_state=st, median_sharp=0.5)
    bundle = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg, window_ctx=ctx, median_sharp=0.5
    )
    expected = any(c.hard_valid for c in bundle.candidates)
    assert window_has_candidates(
        ids,
        aspects,
        assets_map,
        size=9,
        cfg=cfg,
        burst_seconds=3600.0,
        median_sharp=0.5,
        layout_state=st,
    ) == expected
    assert any(c.pattern_id == PATTERN_LANDSCAPE_9 for c in bundle.candidates if c.hard_valid)
