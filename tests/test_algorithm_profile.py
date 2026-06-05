"""Algorithm freshness profile + stale detection."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.config import AppConfig, CullConfig
from travelogue.curation.algorithm_profile import (
    PROFILE_VERSION,
    assess_algorithm_freshness,
    cull_config_stale,
    expected_profile,
    maybe_refresh_cull,
    preview_outputs_stale,
    should_recull_on_curate,
    write_curate_profile,
    write_ingest_profile,
)
from travelogue.curation.curate import run_curate


def _image(aid: str, *, aesthetic: bool = True) -> dict:
    asset = {"id": aid, "type": "image", "layoutEligible": True, "takenAt": "2025-04-01T10:00:00Z"}
    if aesthetic:
        asset["quality"] = {
            "aesthetic": {
                "version": expected_profile()["aestheticVersion"],
                "overall": 0.5,
                "confidence": 0.6,
                "source": "rules",
                "dims": {},
                "signals": {},
            }
        }
    return asset


def test_expected_profile_includes_version_keys():
    profile = expected_profile()
    assert profile["profileVersion"] == PROFILE_VERSION
    assert "aestheticVersion" in profile
    assert "coverScoringHash" in profile
    assert "cullKeepRatioFloor" in profile


def test_write_ingest_profile_records_snapshot():
    trip: dict = {"curation": {}}
    profile = write_ingest_profile(trip)
    assert trip["curation"]["algorithmProfile"]["ingestedAt"]
    assert profile["cullKeepRatioFloor"] == expected_profile()["cullKeepRatioFloor"]


def test_write_curate_profile_merges_layout():
    trip = {"curation": {"algorithmProfile": {"ingestedAt": "2025-01-01T00:00:00Z"}}, "layoutEngine": "screens"}
    profile = write_curate_profile(trip, export_layout="mobile", layout_engine="screens")
    assert profile["curatedAt"]
    assert profile["exportLayout"] == "mobile"
    assert profile["layoutEngine"] == "screens"


def test_cull_config_stale_when_floor_raised():
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.9))
    trip = {"curation": {"algorithmProfile": {"cullKeepRatioFloor": 0.8}}}
    assert cull_config_stale(trip, app_cfg=cfg) is True


def test_cull_config_stale_false_when_floor_matches():
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.9))
    trip = {"curation": {"algorithmProfile": {"cullKeepRatioFloor": 0.9}}}
    assert cull_config_stale(trip, app_cfg=cfg) is False


def test_assess_algorithm_freshness_flags_aesthetic_gap():
    trip = {"assets": [_image("a1", aesthetic=False)], "curation": {}}
    out = assess_algorithm_freshness(trip)
    assert out["aestheticStale"] is True
    assert out["algorithmStale"] is True
    assert out["staleHint"]


def test_preview_outputs_stale_when_trip_newer(tmp_path: Path):
    import os

    preview = tmp_path / "preview.jpg"
    preview.write_bytes(b"jpeg")
    old = time.time() - 100
    os.utime(preview, (old, old))
    assert preview_outputs_stale(tmp_path, trip_mtime=old) is False
    assert preview_outputs_stale(tmp_path, trip_mtime=time.time()) is True


def test_should_recull_on_curate_respects_flags():
    trip = {"curation": {"algorithmProfile": {"cullKeepRatioFloor": 0.8}}}
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.9))
    assert should_recull_on_curate(trip, refresh_algorithms=True, app_cfg=cfg) is True
    assert should_recull_on_curate(trip, refresh_algorithms=False, app_cfg=cfg) is False
    assert should_recull_on_curate(trip, refresh_algorithms=None, app_cfg=cfg) is True


def test_maybe_refresh_cull_skips_when_fresh():
    trip = {"assets": [_image("a1")], "curation": {"algorithmProfile": {"cullKeepRatioFloor": 0.9}}}
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.9))
    assert maybe_refresh_cull(trip, app_cfg=cfg) is None


def test_maybe_refresh_cull_runs_when_stale():
    trip = {
        "assets": [_image("a1"), _image("a2"), _image("a3"), _image("a4"), _image("a5")],
        "curation": {"algorithmProfile": {"cullKeepRatioFloor": 0.8}},
        "meta": {"title": "t", "dateStart": "2025-04-01", "dateEnd": "2025-04-03"},
    }
    cfg = AppConfig(cull=CullConfig(enabled=True, keep_ratio_floor=0.9))
    with patch("travelogue.curation.photo_cull.apply_photo_cull", return_value={"enabled": True}) as mocked:
        summary = maybe_refresh_cull(trip, app_cfg=cfg)
    mocked.assert_called_once()
    assert summary == {"enabled": True}


def test_run_curate_writes_algorithm_profile(tmp_path: Path):
    trip = {
        "assets": [
            _image(f"a{i}") for i in range(1, 6)
        ],
        "meta": {"title": "t", "dateStart": "2025-04-01", "dateEnd": "2025-04-03"},
        "curation": {},
        "pipeline": {},
    }
    for i, asset in enumerate(trip["assets"], start=1):
        asset["takenAt"] = f"2025-04-0{i}T12:00:00Z"
    run_curate(trip, export_layout="mobile", apply_layout=False, trip_dir=tmp_path)
    profile = trip["curation"]["algorithmProfile"]
    assert profile.get("curatedAt")
    assert profile.get("cullKeepRatioFloor") is not None


def test_list_studio_trips_exposes_algorithm_stale(tmp_path: Path):
    trip_dir = tmp_path / "algo-stale"
    trip_dir.mkdir()
    trip = {
        "meta": {"title": "Stale"},
        "assets": [{"id": "x", "type": "image"}],
        "chapters": [{"id": "ch1", "screens": []}],
        "updatedAt": "2025-06-01T00:00:00Z",
    }
    (trip_dir / "trip.json").write_text(json.dumps(trip), encoding="utf-8")
    from travelogue.web.studio_trips import list_studio_trips

    rows = list_studio_trips(tmp_path)
    assert len(rows) == 1
    assert rows[0]["algorithmStale"] is True
    assert rows[0]["aestheticStale"] is True
