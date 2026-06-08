"""AC-P17-20 / AC-P17-26 · measurable golden metrics on synthetic chapters."""

from __future__ import annotations

from travelogue.layout_engine.metrics import (
    evaluate_ac_delta,
    highlight_main_quality_delta_pp,
    same_person_run_lengths,
)
from travelogue.layout_engine.segment_order import optimize_bucket_asset_ids


def _assets_with_quality(n: int, *, person_every: int = 2) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(n):
        aid = f"a{i:02d}"
        out[aid] = {
            "id": aid,
            "width": 1200,
            "height": 1600 if i % 2 == 0 else 900,
            "quality": {"sharpness": 0.2 + (i % 10) * 0.07, "aesthetic": 0.3 + (i % 8) * 0.06},
            "tags": ["person"] if i % person_every == 0 else ["scenery"],
        }
    return out


def _chapter_from_order(order: list[str], *, pattern: str = "screen-portrait-1") -> list[dict]:
    screens = []
    for aid in order:
        screens.append(
            {
                "patternId": pattern,
                "slots": [{"assetId": aid, "fit": "cover", "displayAspect": 0.75}],
            }
        )
    return [{"id": "ch-01", "items": [{"assetId": a} for a in order], "screens": screens}]


def test_ac_p17_26_highlight_quality_delta_measurable() -> None:
    assets: dict[str, dict] = {}
    order: list[str] = []
    for i in range(10):
        aid = f"low{i:02d}"
        order.append(aid)
        assets[aid] = {
            "id": aid,
            "width": 1200,
            "height": 900,
            "quality": {"sharpness": 0.15, "aesthetic": 0.2},
            "tags": [],
        }
    for i in range(5):
        aid = f"hi{i:02d}"
        order.append(aid)
        assets[aid] = {
            "id": aid,
            "width": 1200,
            "height": 1600,
            "quality": {"sharpness": 0.95, "aesthetic": 0.92},
            "tags": ["person"],
        }
    chapters = _chapter_from_order(order)
    delta_pp = highlight_main_quality_delta_pp(chapters, assets)
    assert delta_pp is not None
    assert delta_pp >= 8.0


def test_ac_p17_26_cover_asset_not_in_chapter_order() -> None:
    """Highlight detection uses chapter order only; cover pool stays separate."""
    assets = _assets_with_quality(12)
    assets["cover-1"] = {
        "id": "cover-1",
        "width": 1600,
        "height": 900,
        "quality": {"sharpness": 0.99, "aesthetic": 0.99},
        "tags": ["scenery"],
    }
    order = list(_assets_with_quality(12).keys())
    windows_asset_ids: set[str] = set()
    from travelogue.layout_engine.highlight_windows import detect_highlight_windows
    from travelogue.layout_engine.quality_features import build_quality_pool

    pool = build_quality_pool(list(assets.values()))
    for window in detect_highlight_windows(order, assets, quality=pool, max_windows=2):
        windows_asset_ids.update(window)
    assert "cover-1" not in windows_asset_ids


def test_ac_p17_20_segment_order_improves_run_length() -> None:
    assets: dict[str, dict] = {}
    order: list[str] = []
    for i in range(6):
        pid = f"p{i}"
        sid = f"s{i}"
        order.extend([pid, sid])
        assets[pid] = {"id": pid, "tags": ["person"]}
        assets[sid] = {"id": sid, "tags": ["scenery"]}
    base_runs = same_person_run_lengths(order, assets)
    opt_order = optimize_bucket_asset_ids(order, assets, max_segment_len=30)
    opt_runs = same_person_run_lengths(opt_order, assets)
    import statistics

    assert statistics.median(base_runs) <= 1.5
    assert max(opt_runs or [0]) >= max(base_runs or [0])


def test_ac_p17_20_evaluate_ac_delta_gate() -> None:
    base_m = {
        "layout.mixed.face_intact_rate": None,
        "layout.mixed.salient_retention_p50": None,
        "layout.beat.hero_first_screen_rate": None,
        "layout.tone.adjacent_delta_e_p50": None,
        "layout.chapter.pattern_diversity_p50": None,
        "layout.segment.same_person_run_p50": 2.0,
    }
    cand_m = dict(base_m)
    cand_m["layout.segment.same_person_run_p50"] = 3.0
    ac = evaluate_ac_delta(base_m, cand_m).get("AC-P17-20") or {}
    assert ac.get("measurable") is True
    assert ac.get("passed") is True
