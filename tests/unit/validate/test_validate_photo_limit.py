"""Manifest photo count limits."""

from travelogue.services.validate import validate_manifest


def test_validate_rejects_too_many_assets() -> None:
    trip = {
        "meta": {"title": "t"},
        "coverAssetId": "a1",
        "assets": [{"id": f"a{i}", "type": "image"} for i in range(3)],
        "chapters": [],
        "pipeline": {"status": "structure_draft"},
    }
    trip["assets"] = [{"id": f"a{i:03d}", "type": "image"} for i in range(251)]
    trip["coverAssetId"] = "a000"
    errors = validate_manifest(trip)
    assert any("E_INGEST_LIMIT_PHOTOS" in e for e in errors)
