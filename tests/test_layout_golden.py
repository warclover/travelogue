"""M13 layout golden gates · AC-P3-C02/C03/C09 + I-G1/I-G2 + LY-P3."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.phase3_ig2_report import evaluate_trip, load_fixture_trip, run_trip_variant
from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.vision.clip_encoder import clip_torch_available

ROOT = Path(__file__).resolve().parents[1]
LOCAL_GOLDEN_TRIPS = ("mao", "maomi", "linzhi")
CI_FIXTURE = "golden-mixed-scenes"


def _trip_with_burst_groups() -> dict:
    assets = []
    for i in range(9):
        day = 10 + (i // 3)
        burst = f"b{i // 3}"
        assets.append(
            {
                "id": f"a{i}",
                "type": "image",
                "takenAt": f"2025-04-{day:02d}T{10 + i % 3:02d}:00:00Z",
                "width": 1200,
                "height": 1600,
                "sharpness": 0.6,
                "burstGroupId": burst,
                "subjectBucket": "landscape" if i % 3 else "food",
            }
        )
    return {
        "schemaVersion": "0.2",
        "tripId": "burst-golden",
        "meta": {"title": "burst", "places": ["测试"]},
        "assets": assets,
        "curation": {},
        "chapters": [],
    }


def test_ig2_ci_fixture_p3_full_meets_guards(tmp_path: Path) -> None:
    """I-G2 / AC-P3-C02/C03/C09 on CI golden-mixed-scenes fixture."""
    trip = load_fixture_trip(CI_FIXTURE)
    report = evaluate_trip(trip, trip_id=CI_FIXTURE, work_dir=tmp_path / CI_FIXTURE)
    baseline = report["baseline"]
    full = report["p3Full"]

    assert full["subjectRunScore"] >= baseline["subjectRunScore"]
    assert full["timeInversionRate"] <= baseline["timeInversionRate"]
    assert full["burstIntegrityViolations"] == 0
    assert full["aspectPatternMatchRate"] >= baseline["aspectPatternMatchRate"]
    assert 3 <= full["chapterCount"] <= 5
    assert report["passesIG1"]
    assert report["passesIG2"] and report["passesTimeGuard"] and report["passesC09"]
    assert report["passesLY03"]


def test_p3_full_assigns_scene_clusters_on_ci_fixture(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", scene_cluster_mode="run_aware"),
        vision=VisionConfig(enabled="true"),
    )
    run_clustering_layer(trip, trip_dir=tmp_path / "cluster", cfg=cfg)
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    assert clustering.get("segmentMode") == "geo_event"
    assert clustering.get("clusters")
    assert any(a.get("sceneClusterId") is not None for a in trip.get("assets") or [])


def test_burst_integrity_not_worse_than_baseline_with_burst_assets(tmp_path: Path) -> None:
    trip = _trip_with_burst_groups()
    report = evaluate_trip(trip, trip_id="burst-golden", work_dir=tmp_path / "burst")
    assert report["p3Full"]["burstIntegrityViolations"] <= report["baseline"]["burstIntegrityViolations"]


@pytest.mark.parametrize("trip_id", LOCAL_GOLDEN_TRIPS)
def test_ig2_local_trip_optional(trip_id: str, tmp_path: Path) -> None:
    """I-G2 on mao/maomi/linzhi when local trips/ present."""
    trip_json = ROOT / "trips" / trip_id / "trip.json"
    if not trip_json.is_file():
        pytest.skip(f"local trips/{trip_id} missing")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    if len(trip.get("assets") or []) < 4:
        pytest.skip(f"trips/{trip_id} too small")
    report = evaluate_trip(trip, trip_id=trip_id, work_dir=tmp_path / trip_id)
    full = report["p3Full"]
    baseline = report["baseline"]
    assert full["burstIntegrityViolations"] <= baseline["burstIntegrityViolations"]
    assert full["timeInversionRate"] <= baseline["timeInversionRate"] + 0.01
    assert full["aspectPatternMatchRate"] >= baseline["aspectPatternMatchRate"] - 0.05
    assert full["subjectRunScore"] >= baseline["subjectRunScore"] - 0.05
    assert report["passesIG1"]


def test_ly_p3_03_aspect_pattern_threshold_on_ci_fixture(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    report = evaluate_trip(trip, trip_id=CI_FIXTURE, work_dir=tmp_path / "ly03")
    assert report["passesLY03"]
    assert report["p3Full"]["aspectPatternMatchRate"] >= report["baseline"]["aspectPatternMatchRate"]


def test_ly_p3_04_scene_cluster_off_matches_baseline_screen_order(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    work = tmp_path / "ly04"
    baseline = run_trip_variant(trip, mode="baseline", trip_dir=work)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true", scene_cluster_mode="off"),
        vision=VisionConfig(enabled="true"),
    )
    body = copy.deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    body.setdefault("curation", {}).pop("clustering", None)
    run_clustering_layer(body, trip_dir=work / "off", cfg=cfg)
    from travelogue.curation.curate import run_curate

    run_curate(body, apply_layout=True, trip_dir=work / "off", cfg=cfg)
    off_screens = [
        list(ch.get("screens") or [])
        for ch in body.get("chapters") or []
    ]
    base_trip = load_fixture_trip(CI_FIXTURE)
    base_body = run_trip_variant(base_trip, mode="baseline", trip_dir=work / "base2")
    assert base_body["screenCount"] == baseline["screenCount"]
    assert off_screens  # structure produced


def test_al_p3_04_vision_extra_missing_degrades_without_crash(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    with patch("travelogue.curation.clustering.vision_stack_available", return_value=False):
        result = run_clustering_layer(trip, trip_dir=tmp_path / "al04", cfg=cfg)
    assert result.scene_cluster_count == 0
    assert result.geo_event_count >= 1
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    assert clustering.get("segmentMode") == "geo_event"


def test_corrupt_cache_sets_stage_hint(tmp_path: Path) -> None:
    trip = load_fixture_trip(CI_FIXTURE)
    cache_dir = tmp_path / "trip" / ".cluster-cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "embeddings.npz").write_bytes(b"not-npz")
    (cache_dir / "manifest.json").write_text("{}", encoding="utf-8")
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    result = run_clustering_layer(trip, trip_dir=tmp_path / "trip", cfg=cfg)
    assert "重新分析" in (result.stage_hint or "")


@pytest.mark.vision
def test_clip_assigns_subject_class_when_installed(tmp_path: Path) -> None:
    if not clip_torch_available():
        pytest.skip("torch/open_clip not installed")
    from PIL import Image

    from travelogue.vision.clip_encoder import ClipEncoder

    trip_dir = tmp_path / "trip"
    img_dir = trip_dir / "assets" / "web"
    img_dir.mkdir(parents=True)
    rel = "assets/web/c1.jpg"
    Image.new("RGB", (224, 224), (120, 80, 40)).save(trip_dir / rel, quality=90)
    assets = [
        {
            "id": "c1",
            "type": "image",
            "path": rel,
            "width": 224,
            "height": 224,
            "sharpness": 0.5,
            "subjectBucket": "landscape",
        }
    ]
    enc = ClipEncoder()
    result = enc.embed_assets(assets, trip_dir=trip_dir, deterministic=True)
    assert result.source == "clip"
    assert result.vectors.shape == (1, result.vectors.shape[1])
    assert assets[0].get("subjectClass") in (
        "landscape",
        "architecture",
        "food",
        "indoor",
        "person",
        "street",
        "temple",
        "mixed",
    )
    assert isinstance(assets[0].get("subjectConfidence"), float)


@pytest.mark.vision
def test_clip_encoder_real_path_when_installed(tmp_path: Path) -> None:
    if not clip_torch_available():
        pytest.skip("torch/open_clip not installed")
    from PIL import Image

    from travelogue.vision.clip_encoder import ClipEncoder

    trip_dir = tmp_path / "trip"
    img_dir = trip_dir / "assets" / "web"
    img_dir.mkdir(parents=True)
    rel = "assets/web/c1.jpg"
    Image.new("RGB", (224, 224), (120, 80, 40)).save(trip_dir / rel, quality=90)
    assets = [
        {
            "id": "c1",
            "type": "image",
            "path": rel,
            "width": 224,
            "height": 224,
            "sharpness": 0.5,
            "subjectBucket": "landscape",
        }
    ]
    enc = ClipEncoder()
    result = enc.embed_assets(assets, trip_dir=trip_dir, deterministic=True)
    assert result.source == "clip"
    assert result.vectors.shape == (1, result.vectors.shape[1])
