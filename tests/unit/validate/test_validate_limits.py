"""Manifest limit rules VR-L06/L07/L08 and VR-M03."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.validate import validate_trip

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "schemas" / "fixtures"


def _base_trip() -> dict:
    return json.loads((FIXTURES / "trip.copy_locked.json").read_text(encoding="utf-8"))


def test_vr_l07_trip_video_cap():
    trip = _base_trip()
    for i in range(4):
        trip["assets"].append(
            {
                "id": f"vid-{i}",
                "type": "video",
                "width": 1280,
                "height": 720,
            }
        )
    errs = validate_trip(trip, level="manifest")
    assert any("VR-L07" in e for e in errs)


def test_vr_m03_chapter_video_cap():
    trip = _base_trip()
    trip["assets"].append(
        {"id": "vid-a", "type": "video", "width": 1280, "height": 720}
    )
    trip["assets"].append(
        {"id": "vid-b", "type": "video", "width": 1280, "height": 720}
    )
    ch = trip["chapters"][1]
    ch["items"].extend(
        [
            {"type": "media-card", "assetId": "vid-a", "layout": {}},
            {"type": "media-card", "assetId": "vid-b", "layout": {}},
        ]
    )
    errs = validate_trip(trip, level="manifest")
    assert any("VR-M03" in e for e in errs)
