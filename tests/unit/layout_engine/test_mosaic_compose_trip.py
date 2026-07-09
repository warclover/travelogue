"""compose_trip uses mosaic deterministic_strict when enabled."""

from __future__ import annotations

from dataclasses import replace

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens
from travelogue.config import get_config
from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS
from travelogue.layout_engine.mosaic.trip import compose_trip


def test_compose_trip_forwards_mosaic_deterministic(monkeypatch):
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    captured: dict = {}

    def _fake_maybe(*_args, **kwargs):
        captured["deterministic_strict"] = kwargs.get("deterministic_strict")
        return legacy, {"replanApplied": False, "decisionLogs": []}

    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_search.maybe_replan_chapters",
        _fake_maybe,
    )
    base = get_config()
    app_cfg = replace(
        base,
        mosaic=replace(base.mosaic, enabled=True, deterministic_strict=True),
        clustering=replace(base.clustering, deterministic_strict=False),
    )
    _, meta = compose_trip(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        app_cfg=app_cfg,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
    )
    assert captured["deterministic_strict"] is True
    assert meta.get("mosaicEnabled") is True
    assert meta.get("mosaicScorerVersion")
