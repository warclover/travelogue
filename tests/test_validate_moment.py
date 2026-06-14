"""Phase 23 · validate_trip moment field rules."""

from __future__ import annotations

from travelogue.services.validate import validate_trip


def _trip_with_moment() -> dict:
    return {
        "tripId": "moment-validate",
        "meta": {"title": "测试"},
        "coverAssetId": "cover",
        "momentAssetId": "moment",
        "assets": [
            {"id": "cover", "type": "image"},
            {"id": "moment", "type": "image"},
            {"id": "other", "type": "image"},
        ],
        "chapters": [
            {"index": 1, "patternId": "open", "title": "一", "items": [], "screens": []},
            {"index": 2, "patternId": "gallery", "title": "二", "items": [], "screens": []},
            {"index": 3, "patternId": "close", "title": "三", "items": [], "screens": []},
        ],
        "curation": {"momentPoolIds": ["moment", "other"]},
        "pipeline": {"status": "structure_draft"},
    }


def test_validate_moment_ok() -> None:
    errs = [e for e in validate_trip(_trip_with_moment(), level="manifest") if "moment" in e.lower()]
    assert not errs


def test_validate_moment_not_in_pool() -> None:
    trip = _trip_with_moment()
    trip["curation"]["momentPoolIds"] = ["other"]
    errs = validate_trip(trip, level="manifest")
    assert any("not in curation.momentPoolIds" in e for e in errs)


def test_validate_moment_equals_cover() -> None:
    trip = _trip_with_moment()
    trip["momentAssetId"] = "cover"
    trip["curation"]["momentPoolIds"] = ["cover", "moment"]
    errs = validate_trip(trip, level="manifest")
    assert any("must not equal cover" in e for e in errs)
