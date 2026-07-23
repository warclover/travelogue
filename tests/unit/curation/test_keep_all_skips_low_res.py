"""QFX · keep_all 预处理合同：回填 + 清标 + 跳硬丢（禁 mock 整函数假绿）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PIL import Image

from travelogue.curation.curate import _curate_preflight
from travelogue.curation.curate_preprocess import (
    clear_low_resolution_marks,
    run_curation_preprocess,
)


def _write_tiny_jpeg(path: Path, *, w: int = 64, h: int = 48) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), color="#808080").save(path, format="JPEG")


def _trip_with_disk_assets(tmp_path: Path, *, intent: dict, marked: bool = False) -> dict:
    assets = []
    for i in range(4):
        rel = f"a{i}.jpg"
        _write_tiny_jpeg(tmp_path / rel)
        asset = {
            "id": f"a{i}",
            "type": "image",
            "sourceFile": rel,
            "takenAt": "2024-05-01T10:00:00",
            "layoutEligible": False if marked else True,
        }
        if marked:
            asset["excludeReason"] = "low_resolution"
        assets.append(asset)
    return {
        "tripId": "t-keep-all",
        "intent": intent,
        "meta": {"title": "测试"},
        "assets": assets,
        "pipeline": {},
        "curation": {"excludedLowResAssetIds": ["a0", "a1", "a2", "a3"]} if marked else {},
    }


def test_clear_low_resolution_marks_restores_eligibility() -> None:
    trip = {
        "assets": [
            {
                "id": "a0",
                "layoutEligible": False,
                "excludeReason": "low_resolution",
            }
        ],
        "curation": {"excludedLowResAssetIds": ["a0"]},
    }
    assert clear_low_resolution_marks(trip) == 1
    assert trip["assets"][0]["layoutEligible"] is True
    assert "excludeReason" not in trip["assets"][0]
    assert "excludedLowResAssetIds" not in trip["curation"]


def test_keep_all_backfills_and_skips_hard_drop(tmp_path: Path) -> None:
    """AC-13/26：keep_all 仍回填尺寸、清旧标，且不硬丢低清。"""
    trip = _trip_with_disk_assets(
        tmp_path,
        intent={"photoKeepMode": "keep_all", "photoCullEnabled": False},
        marked=True,
    )
    warn = run_curation_preprocess(trip, trip_dir=tmp_path)
    assert warn is None
    for asset in trip["assets"]:
        assert asset.get("nativeWidth") == 64
        assert asset.get("nativeHeight") == 48
        assert asset.get("layoutEligible") is True
        assert asset.get("excludeReason") != "low_resolution"
    assert "excludedLowResAssetIds" not in (trip.get("curation") or {})


def test_recommended_still_hard_drops_low_res(tmp_path: Path) -> None:
    """与 asset_quality 合同一致：≥6 张时绝对低清被硬丢。"""
    assets = []
    for i in range(5):
        rel = f"big{i}.jpg"
        _write_tiny_jpeg(tmp_path / rel, w=3000, h=2000)
        assets.append(
            {
                "id": f"big{i}",
                "type": "image",
                "sourceFile": rel,
                "takenAt": "2024-05-01T10:00:00",
                "layoutEligible": True,
            }
        )
    rel_tiny = "tiny.jpg"
    _write_tiny_jpeg(tmp_path / rel_tiny, w=64, h=48)
    assets.append(
        {
            "id": "tiny",
            "type": "image",
            "sourceFile": rel_tiny,
            "takenAt": "2024-05-01T10:00:00",
            "layoutEligible": True,
        }
    )
    trip = {
        "tripId": "t-rec",
        "intent": {"photoKeepMode": "recommended"},
        "meta": {"title": "测试"},
        "assets": assets,
        "pipeline": {},
        "curation": {},
    }
    run_curation_preprocess(trip, trip_dir=tmp_path)
    tiny = next(a for a in trip["assets"] if a["id"] == "tiny")
    assert tiny.get("excludeReason") == "low_resolution"
    assert tiny.get("layoutEligible") is False
    assert "tiny" in (trip["curation"].get("excludedLowResAssetIds") or [])


def test_preflight_orchestrates_preprocess_for_keep_all(tmp_path: Path) -> None:
    trip = _trip_with_disk_assets(
        tmp_path,
        intent={"photoKeepMode": "keep_all"},
        marked=True,
    )
    called = {"n": 0}

    def _spy(trip_arg, **kwargs):
        called["n"] += 1
        return run_curation_preprocess(trip_arg, **kwargs)

    with patch(
        "travelogue.curation.curate_preprocess.run_curation_preprocess",
        side_effect=_spy,
    ):
        with patch(
            "travelogue.curation.time_outlier.apply_time_outlier_marks",
            return_value=[],
        ):
            with patch(
                "travelogue.curation.time_segments.cluster_time_segments",
                return_value=[],
            ):
                with patch(
                    "travelogue.curation.curate.layout_eligible_assets",
                    return_value=list(trip["assets"]),
                ):
                    with patch(
                        "travelogue.curation.curate.sync_trip_covers",
                        return_value="a0",
                    ):
                        _curate_preflight(
                            trip,
                            export_layout="web",
                            layout_engine=None,
                            trip_dir=tmp_path,
                            cfg=None,
                            saved_memory_anchors=[],
                        )
    assert called["n"] == 1
    assert all(a.get("nativeWidth") for a in trip["assets"])
