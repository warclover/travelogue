"""P1 · single-portrait mixed window scorer tie-break."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
from travelogue.curation.mosaic.pattern_catalog import default_registry
from travelogue.curation.mosaic.scorer import score_candidate


def _asset(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "quality": {"sharpness": 0.8},
    }


def test_main_portrait_3land_gets_single_portrait_bonus(monkeypatch):
    from travelogue.config.layout import UsageRulesConfig

    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=False))
    patched = replace(base, layout=layout)
    monkeypatch.setattr("travelogue.config.get_config", lambda: patched)
    monkeypatch.setattr(
        "travelogue.curation.usage_rules.evaluator.get_config",
        lambda: patched,
    )
    aspects = {
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "p1": "portrait",
    }
    assets_map = {
        "l0": _asset("l0", w=3000, h=1687),
        "l1": _asset("l1", w=3000, h=1687),
        "l2": _asset("l2", w=3000, h=1687),
        "l3": _asset("l3", w=3000, h=1687),
        "p1": _asset("p1", w=1200, h=1800),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        list(aspects.keys()),
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    pat = default_registry()[PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND]
    screen = build_screen(pat, ordered, assets_map=assets_map)
    cfg_on = replace(get_config().mosaic, prefer_five_slot_single_portrait=True)
    cfg_off = replace(get_config().mosaic, prefer_five_slot_single_portrait=False)
    on = score_candidate(screen, aspects=aspects, assets_by_id=assets_map, cfg=cfg_on)
    off = score_candidate(screen, aspects=aspects, assets_by_id=assets_map, cfg=cfg_off)
    assert on.total > off.total
    assert "R_SINGLE_PORTRAIT_3LAND" in on.reason_codes
