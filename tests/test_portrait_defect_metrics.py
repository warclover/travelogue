"""P3-4 · portrait defect metrics on key slots."""

from __future__ import annotations

from travelogue.curation.portrait_defect_metrics import (
    aggregate_defect_rates,
    analyze_slot_defects,
    asset_has_portrait_defect,
    collect_key_slot_asset_ids,
    compare_to_baseline,
    portrait_defect_tags,
)


def _portrait_asset(aid: str, *, eyes: float = 0.9, sharp: float = 800.0) -> dict:
    return {
        "id": aid,
        "type": "image",
        "tags": ["person", "face"],
        "faces": [{"bbox": [0, 0, 10, 10]}],
        "quality": {
            "sharpness": 300.0,
            "portrait": {
                "eyesOpenScore": eyes,
                "faceSharpness": sharp,
                "confidence": 0.7,
            },
        },
    }


def test_portrait_defect_tags_closed_eyes():
    ok = _portrait_asset("ok")
    bad = _portrait_asset("bad", eyes=0.1)
    assert portrait_defect_tags(ok) == []
    assert "closed_eyes" in portrait_defect_tags(bad)


def test_portrait_defect_tags_blur_face():
    blurry = _portrait_asset("blur", sharp=30.0)
    assert "blur_face" in portrait_defect_tags(blurry)


def test_collect_key_slot_asset_ids():
    trip = {
        "coverAssetId": "c1",
        "coverByLayout": {"web": "c2"},
        "momentAssetId": "m1",
        "curation": {"chapterHeroAssetIds": {"ch-01": "h1"}},
        "chapters": [{"curation": {"heroAssetId": "h2"}}],
    }
    slots = collect_key_slot_asset_ids(trip)
    assert set(slots["cover"]) == {"c1", "c2"}
    assert set(slots["hero"]) == {"h1", "h2"}
    assert slots["moment"] == ["m1"]


def test_analyze_slot_defects_counts_cover():
    trip = {
        "tripId": "demo",
        "coverAssetId": "good",
        "assets": [
            _portrait_asset("good"),
            _portrait_asset("bad", eyes=0.05),
        ],
    }
    rep = analyze_slot_defects(trip)
    cover = rep["slots"]["cover"]
    assert cover["scorableCount"] == 1
    assert cover["defectCount"] == 0
    assert cover["defectRate"] == 0.0


def test_analyze_slot_defects_detects_bad_cover():
    trip = {
        "tripId": "demo",
        "coverAssetId": "bad",
        "assets": [_portrait_asset("bad", eyes=0.05)],
    }
    rep = analyze_slot_defects(trip)
    assert rep["slots"]["cover"]["defectCount"] == 1
    assert asset_has_portrait_defect(_portrait_asset("bad", eyes=0.05))


def test_aggregate_and_baseline_compare():
    current_trips = [
        {
            "slots": {
                "cover": {"scorableCount": 2, "defectCount": 0, "defectRate": 0.0},
                "hero": {"scorableCount": 1, "defectCount": 1, "defectRate": 1.0},
                "moment": {"scorableCount": 0, "defectCount": 0, "defectRate": None},
            }
        }
    ]
    baseline = {
        "aggregate": {
            "cover": {"defectRate": 0.5},
            "hero": {"defectRate": 1.0},
            "moment": {"defectRate": None},
            "all": {"defectRate": 0.67},
        }
    }
    agg = aggregate_defect_rates(current_trips)
    assert agg["cover"]["defectRate"] == 0.0
    cmp = compare_to_baseline(agg, baseline)
    assert cmp["passed"] is True
    assert cmp["bySlot"]["cover"]["passed"] is True
