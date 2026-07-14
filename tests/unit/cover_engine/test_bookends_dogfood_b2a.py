"""T-B2A-07 · synthetic dogfood (≥5 trips): no cover reuse + degraded when tiny."""

from __future__ import annotations

from travelogue.cover_engine.api import maybe_resolve_closing_after_layout, resolve_closing
from travelogue.domain.closing_view import cover_ids_to_exclude, resolve_closing_asset_id


def _img(aid: str, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": 1600,
        "height": 900,
        "userTier": "featured",
        "sharpness": 0.75,
        "aesthetic": {"overall": 0.6},
        "dominantTone": "#556677",
    }
    base.update(extra)
    return base


def _trip(trip_id: str, assets: list[dict], screens: list[str], *, cover: str) -> dict:
    return {
        "tripId": trip_id,
        "exportLayout": "web",
        "coverAssetId": cover,
        "assets": assets,
        "chapters": [
            {"id": "ch-01", "screens": [{"slots": [{"assetId": aid} for aid in screens]}]}
        ],
        "curation": {},
        "meta": {"coverOpeningStyle": "veil-footer"},
    }


def _dogfood_trips() -> list[dict]:
    return [
        _trip(
            "df-01",
            [_img("c1"), _img("a"), _img("b"), _img("u", dominantTone="#334455")],
            ["a", "b"],
            cover="c1",
        ),
        _trip(
            "df-02",
            [_img("c2", width=1200, height=1600), _img("l1"), _img("l2")],
            ["l1", "l2"],
            cover="c2",
        ),
        _trip(
            "df-03-tiny",
            [_img("only")],
            ["only"],
            cover="only",
        ),
        _trip(
            "df-04",
            [
                _img("cover4"),
                _img("s1"),
                _img("s2"),
                _img("spare4", dominantTone="#223344"),
            ],
            ["s1", "s2", "cover4"],
            cover="cover4",
        ),
        _trip(
            "df-05",
            [
                _img(
                    "face",
                    width=1200,
                    height=1600,
                    faceCount=1,
                    faces=[{"bbox": {"x": 0.2, "y": 0.15, "w": 0.55, "h": 0.55}}],
                ),
                _img("road", dominantTone="#445566"),
                _img("dusk", dominantTone="#1a1a2e", tags=["evening"]),
            ],
            ["road"],
            cover="face",
        ),
    ]


def test_dogfood_five_trips_no_cover_reuse() -> None:
    trips = _dogfood_trips()
    assert len(trips) >= 5
    degraded = 0
    for trip in trips:
        decision = resolve_closing(trip, layout="web", force=True)
        covers = cover_ids_to_exclude(trip)
        if decision.closing_asset_id is None:
            degraded += 1
            assert decision.degraded is True
        else:
            assert decision.closing_asset_id not in covers
        # domain helper must agree: never returns cover
        assets = {a["id"]: a for a in trip["assets"]}
        picked = resolve_closing_asset_id(trip, assets, prefer_landscape=True)
        if picked:
            assert picked not in covers


def test_dogfood_maybe_resolve_hook_idempotent() -> None:
    trip = _dogfood_trips()[0]
    first = maybe_resolve_closing_after_layout(trip, layout="web")
    assert first is not None
    second = maybe_resolve_closing_after_layout(trip, layout="web")
    assert second is None  # already written
    covers = cover_ids_to_exclude(trip)
    cid = trip["curation"].get("closingAssetId")
    if cid:
        assert cid not in covers
