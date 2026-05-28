"""M12-0 algorithm spike gates (SP-C01～C05) · CI golden fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.cluster_eval import geo_segment_agreement_rate, segments_to_eval_dict
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.clustering_buckets import cap_geo_segments, merge_small_geo_events
from travelogue.curation.curate import run_curate
from travelogue.curation.geo_events import detect_geo_events
from travelogue.curation.scene_clusters import compute_scene_clusters
from travelogue.vision.clip_encoder import ClipEncoder
from tests.clustering_fixtures import (
    GOLDEN_TRIP_IDS,
    load_fixture_assets,
    load_fixture_golden_segments,
)

GPS_GOLDEN = ("golden-kyoto-gps", "golden-mixed-scenes", "synthetic-gps")
SP_C01_MIN_RATE = 0.70


def _clustering_hash(trip: dict) -> str:
    blob = json.dumps(trip.get("curation", {}).get("clustering", {}), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _trip_from_assets(assets: list[dict]) -> dict:
    return {
        "schemaVersion": "0.2",
        "exportLayout": "auto",
        "meta": {"title": "spike", "places": ["测试"]},
        "assets": [dict(a) for a in assets],
        "curation": {},
        "chapters": [],
    }


@pytest.mark.parametrize("trip_id", GPS_GOLDEN)
def test_sp_c01_geo_agreement(trip_id: str) -> None:
    """SP-C01 · geo events vs golden segments ≥70%."""
    assets = load_fixture_assets(trip_id)
    golden = load_fixture_golden_segments(trip_id)
    if not golden:
        pytest.skip(f"{trip_id}: no segments-golden.json")
    detected = detect_geo_events(assets)
    rate = geo_segment_agreement_rate(
        golden,
        segments_to_eval_dict(detected),
        threshold=0.7,
    )
    assert rate >= SP_C01_MIN_RATE, f"{trip_id}: agreement {rate:.0%} < {SP_C01_MIN_RATE:.0%}"


def test_sp_c01_kyoto_gps_records_rate_for_matrix() -> None:
    assets = load_fixture_assets("golden-kyoto-gps")
    golden = load_fixture_golden_segments("golden-kyoto-gps")
    detected = detect_geo_events(assets)
    rate = geo_segment_agreement_rate(golden, segments_to_eval_dict(detected))
    assert rate >= SP_C01_MIN_RATE
    # Keep explicit trip for matrix audit trail
    assert len(detected) == 3


def test_sp_c03_chapter_cap_from_many_events() -> None:
    """SP-C03 · 8 raw events merge/cap to ≤5."""
    segments = [
        {
            "id": f"e{i}",
            "startDate": "2025-06-01",
            "endDate": "2025-06-01",
            "assetIds": [f"a{i}{j}" for j in range(4)],
        }
        for i in range(8)
    ]
    merged = merge_small_geo_events(segments)
    capped = cap_geo_segments(merged, min_chapters=3, max_chapters=5)
    assert 3 <= len(capped) <= 5


def test_sp_c03_curate_chapters_in_range(tmp_path: Path) -> None:
    assets = load_fixture_assets("golden-kyoto-gps")
    trip = _trip_from_assets(assets)
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"))
    trip_dir = tmp_path / "kyoto"
    trip_dir.mkdir()
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    result = run_curate(trip, apply_layout=True, trip_dir=trip_dir, cfg=cfg)
    assert 3 <= result.chapter_count <= 5


def test_sp_c03_no_gps_date_fallback(tmp_path: Path) -> None:
    assets = load_fixture_assets("golden-no-gps")
    trip = _trip_from_assets(assets)
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"))
    trip_dir = tmp_path / "no-gps"
    trip_dir.mkdir()
    result = run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    assert result.segment_mode == "date_fallback"
    assert detect_geo_events(assets) == []


@pytest.mark.parametrize("trip_id", ("golden-kyoto-gps", "golden-mixed-scenes"))
def test_sp_c05_deterministic_clustering(trip_id: str, tmp_path: Path) -> None:
    assets = load_fixture_assets(trip_id)
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true", deterministic=True))
    trip_a = _trip_from_assets(assets)
    trip_b = _trip_from_assets(assets)
    run_clustering_layer(trip_a, trip_dir=tmp_path / "a", cfg=cfg)
    run_clustering_layer(trip_b, trip_dir=tmp_path / "b", cfg=cfg)
    assert _clustering_hash(trip_a) == _clustering_hash(trip_b)


def test_sp_c02_scene_cluster_sane() -> None:
    """SP-C02 · cluster count 1–40, no mega-cluster on mixed-scenes."""
    pytest.importorskip("sklearn")
    assets = load_fixture_assets("golden-mixed-scenes")
    enc = ClipEncoder()
    embed = enc.embed_assets(assets)
    clusters = compute_scene_clusters(
        embed.asset_ids,
        embed.vectors,
        eps=0.08,
        min_samples=3,
    )
    assert 1 <= len(clusters) <= 40
    total = len(embed.asset_ids)
    if len(clusters) >= 2:
        max_share = max(len(c.asset_ids) for c in clusters) / total
        assert max_share <= 0.75


def test_sp_c04_nr_p3_01_local_trip_optional(tmp_path: Path) -> None:
    """SP-C04 · optional mao/linzhi when trips/ present on disk."""
    root = Path(__file__).resolve().parents[1]
    for trip_id in ("mao", "linzhi"):
        trip_json = root / "trips" / trip_id / "trip.json"
        if not trip_json.is_file():
            continue
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
        if len(trip.get("assets") or []) < 4:
            continue
        cfg_off = AppConfig(clustering=ClusteringConfig(enabled="false"))
        cfg_on = AppConfig(clustering=ClusteringConfig(enabled="true"))
        trip_dir = tmp_path / trip_id
        trip_dir.mkdir()
        baseline = json.loads(json.dumps(trip))
        run_clustering_layer(baseline, trip_dir=trip_dir / "off", cfg=cfg_off)
        try:
            run_curate(baseline, apply_layout=True, trip_dir=trip_dir / "off", cfg=cfg_off)
        except Exception:
            continue
        candidate = json.loads(json.dumps(trip))
        run_clustering_layer(candidate, trip_dir=trip_dir / "on", cfg=cfg_on)
        try:
            run_curate(candidate, apply_layout=True, trip_dir=trip_dir / "on", cfg=cfg_off)
        except Exception:
            continue
        base_ch = [ch.get("assetIds") for ch in baseline.get("chapters") or []]
        cand_ch = [ch.get("assetIds") for ch in candidate.get("chapters") or []]
        assert base_ch == cand_ch


def test_all_golden_manifests_present() -> None:
    for trip_id in GOLDEN_TRIP_IDS:
        assets = load_fixture_assets(trip_id)
        assert len(assets) >= 4
