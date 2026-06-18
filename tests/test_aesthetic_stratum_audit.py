"""Tests for stratum audit helpers."""

from __future__ import annotations

from travelogue.curation.aesthetic_stratum_audit import (
    apply_stratum_audit,
    audit_label_strata,
    merged_asset_key,
    remap_rows_for_merged,
)
from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset


def test_merged_asset_key_and_remap():
    row = {"tripId": "demo-a", "assetId": "asset-1", "humanScore": 3, "stratum": "landscape"}
    remapped = remap_rows_for_merged([row])
    assert remapped[0]["assetId"] == merged_asset_key("demo-a", "asset-1")
    assert remapped[0]["_originalAssetId"] == "asset-1"


def test_audit_detects_group_to_landscape(tmp_path):
    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    asset = {
        "id": "asset-1",
        "type": "image",
        "layoutEligible": True,
        "width": 4000,
        "height": 3000,
        "quality": {"faceCount": 3},
        "tags": [],
    }
    assert review_stratum_for_asset(asset) == "landscape"
    (trip_dir / "trip.json").write_text(
        '{"tripId":"demo-x","assets":[' + __import__("json").dumps(asset) + "]}",
        encoding="utf-8",
    )
    rows = [{"assetId": "asset-1", "humanScore": 4, "stratum": "group"}]
    audit = audit_label_strata(trip_dir=trip_dir, label_rows=rows, trip_id="demo-x")
    assert audit["changeCount"] == 1
    updated = apply_stratum_audit({"rows": rows}, audit, audit_note="test")
    assert updated["rows"][0]["stratum"] == "landscape"
    assert updated["rows"][0]["stratumAuto"] == "group"
