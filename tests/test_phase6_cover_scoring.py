"""Phase 6 cover scoring (composition rules + explain)."""

from __future__ import annotations

from travelogue.curation.curate_scoring import (
    build_cover_explain,
    cover_score,
    _cover_rule_of_thirds_multiplier,
)
from travelogue.media.color_metrics import color_richness_multiplier


def _asset(**extra) -> dict:
    base = {
        "id": "a1",
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 100.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    base.update(extra)
    return base


def test_rule_of_thirds_prefers_off_center_subject() -> None:
    centered = _asset(focalPoint={"x": 0.5, "y": 0.5})
    thirds = _asset(focalPoint={"x": 0.33, "y": 0.33})
    assert _cover_rule_of_thirds_multiplier(thirds) > _cover_rule_of_thirds_multiplier(centered)


def test_rule_of_thirds_boosts_cover_score() -> None:
    centered = _asset(focalPoint={"x": 0.5, "y": 0.5})
    thirds = _asset(id="a2", focalPoint={"x": 0.33, "y": 0.66})
    assert cover_score(thirds, "mobile") > cover_score(centered, "mobile")


def test_color_richness_demotes_flat_dark() -> None:
    vivid = color_richness_multiplier(hex_color="#4488cc", mean_luma=0.55)
    dull_dark = color_richness_multiplier(hex_color="#666666", mean_luma=0.18)
    assert vivid > dull_dark


def test_face_bbox_boost_when_sharp_and_salient_box() -> None:
    from travelogue.curation.curate_scoring import _cover_face_bbox_multiplier

    plain = _asset(id="plain", tags=["landscape"], quality={"sharpness": 100.0})
    faced = _asset(
        id="faced",
        tags=["face", "person"],
        quality={"sharpness": 100.0},
        salientBox={"x": 0.3, "y": 0.25, "w": 0.2, "h": 0.22},
    )
    assert _cover_face_bbox_multiplier(faced, median_sharp=80.0) > 1.0
    assert _cover_face_bbox_multiplier(plain, median_sharp=80.0) == 1.0


def test_dull_dark_cover_scores_below_vivid() -> None:
    vivid = _asset(id="vivid", dominantTone="#4488cc", meanLuma=0.55)
    dull = _asset(id="dull", dominantTone="#666666", meanLuma=0.18)
    assert cover_score(vivid, "mobile") > cover_score(dull, "mobile")


def test_pick_cover_prefers_thirds_with_phase6_factors() -> None:
    from travelogue.curation.curate_scoring import pick_cover_asset_id

    assets = [
        _asset(id="center", focalPoint={"x": 0.5, "y": 0.5}),
        _asset(id="thirds", focalPoint={"x": 0.33, "y": 0.66}),
    ]
    p5 = pick_cover_asset_id(assets, export_layout="mobile", enable_phase6_cover_factors=False)
    p6 = pick_cover_asset_id(assets, export_layout="mobile", enable_phase6_cover_factors=True)
    assert p5 == "center"
    assert p6 == "thirds"


def test_build_cover_explain_returns_readable_reasons() -> None:
    asset = _asset(
        tags=["face"],
        dominantTone="#4488cc",
        meanLuma=0.55,
        focalPoint={"x": 0.33, "y": 0.33},
    )
    explain = build_cover_explain(asset, "mobile")
    assert explain
    assert all("reason" in row and "label" in row for row in explain)
