"""PRD-P9-F1 · photo cull user opt-out policy."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.config import AppConfig, CullConfig
from travelogue.curation.algorithm_profile import should_recull_on_curate
from travelogue.curation.photo_cull import apply_photo_cull, photo_cull_enabled_for_trip
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip import apply_intent
from travelogue.services.trip_factory import create_trip


def _asset(aid: str, *, eligible: bool = True) -> dict:
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": eligible,
        "quality": {"sharpness": 0.5},
        "mediaClass": "photo",
    }


def test_photo_cull_enabled_for_trip_defaults_true() -> None:
    trip = {"intent": {"version": "1"}}
    assert photo_cull_enabled_for_trip(trip, app_cfg=AppConfig(cull=CullConfig(enabled=True)))


def test_photo_cull_enabled_for_trip_respects_false_intent() -> None:
    trip = {"intent": {"photoCullEnabled": False}}
    assert not photo_cull_enabled_for_trip(trip, app_cfg=AppConfig(cull=CullConfig(enabled=True)))


def test_photo_cull_enabled_for_trip_config_off() -> None:
    trip = {"intent": {"photoCullEnabled": True}}
    assert not photo_cull_enabled_for_trip(trip, app_cfg=AppConfig(cull=CullConfig(enabled=False)))


def test_apply_photo_cull_user_disabled_skips_and_marks_summary() -> None:
    assets = [_asset("a1"), _asset("a2")]
    trip = {"intent": {"photoCullEnabled": False}}
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.5, min_keep=1))

    summary = apply_photo_cull(trip, assets, cfg=cfg)

    assert summary["enabled"] is False
    assert summary["userDisabled"] is True
    assert summary["configDisabled"] is False
    assert summary["layoutEligibleCount"] == 2
    assert trip["curation"]["cullSummary"]["userDisabled"] is True
    assert "cullUserLine" not in trip.get("curation", {})


def test_apply_photo_cull_config_disabled_marks_config_disabled() -> None:
    trip = {"intent": {"photoCullEnabled": False}}
    cfg = AppConfig(cull=CullConfig(enabled=False))
    summary = apply_photo_cull(trip, [_asset("a1")], cfg=cfg)
    assert summary["configDisabled"] is True
    assert summary.get("userDisabled") is False


def test_should_recull_on_curate_false_when_user_disabled() -> None:
    trip = {"intent": {"photoCullEnabled": False}}
    with patch(
        "travelogue.curation.algorithm_profile.cull_config_stale",
        return_value=True,
    ):
        assert not should_recull_on_curate(
            trip,
            app_cfg=AppConfig(cull=CullConfig(enabled=True)),
        )


def test_apply_intent_photo_cull_enabled() -> None:
    trip: dict = {}
    apply_intent(trip, photo_cull_enabled=False)
    assert trip["intent"]["photoCullEnabled"] is False
    apply_intent(trip, photo_cull_enabled=True)
    assert trip["intent"]["photoCullEnabled"] is True
    apply_intent(trip, photo_cull_enabled=None)
    assert "photoCullEnabled" not in trip["intent"]
    assert photo_cull_enabled_for_trip(trip)


def _album_with_tiny(tmp_path: Path, *, good: int = 5) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base_t = time.time() - 3600
    for i in range(good):
        path = album / f"p{i:02d}.jpg"
        Image.new("RGB", (2400, 3200), (30 + i * 17, 50 + i * 11, 70 + i * 13)).save(
            path, quality=95
        )
        os.utime(path, (base_t + i * 60, base_t + i * 60))
    tiny = album / "tiny.jpg"
    Image.new("RGB", (2000, 1500), (200, 100, 50)).save(tiny, quality=95)
    os.utime(tiny, (base_t + good * 60, base_t + good * 60))
    return album


@pytest.mark.integration
def test_low_res_still_excluded_when_user_cull_disabled(tmp_path: Path) -> None:
    """F1-1i / AC-F1-12 · cull off 时低清门仍降 M，cull 不剔非低清。"""
    trips = tmp_path / "trips"
    trip_json = create_trip("cull-off-lowres", trips, title="用户关 cull")
    trip_dir = trips / "cull-off-lowres"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    trip.setdefault("intent", {})["photoCullEnabled"] = False

    ingest_into_trip(trip, trip_dir, from_dir=_album_with_tiny(tmp_path), dedupe=False)

    cull_summary = (trip.get("curation") or {}).get("cullSummary") or {}
    assert cull_summary.get("userDisabled") is True
    assert cull_summary.get("enabled") is False
    assert "cullUserLine" not in (trip.get("curation") or {})

    n = len(trip["assets"])
    m = sum(1 for a in trip["assets"] if a.get("layoutEligible", True))
    assert n == 6
    assert m == 5
    assert m < n
    assert cull_summary.get("finalLayoutEligibleCount") == 5
    tiny = next(a for a in trip["assets"] if a.get("nativeWidth") == 2000)
    assert tiny["layoutEligible"] is False
    assert tiny["excludeReason"] == "low_resolution"


def test_trip_schema_accepts_photo_cull_enabled_intent() -> None:
    import json
    from pathlib import Path

    from travelogue.services.validate import validate_trip

    fixture = repo_root(__file__) / "schemas" / "fixtures" / "trip.render_golden.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    intent = trip.setdefault("intent", {})
    intent["version"] = intent.get("version") or "1"
    intent["photoCullEnabled"] = False
    errors = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert errors == []
