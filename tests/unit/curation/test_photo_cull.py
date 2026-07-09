"""Phase 9 · photo cull (Quality Gate)."""



from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from tests._repo_root import repo_root
from travelogue.config import AppConfig, ClusteringConfig, CullConfig, IngestConfig, VisionConfig
from travelogue.curation.asset_quality import apply_layout_eligibility_marks
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import layout_eligible_assets, run_curate
from travelogue.curation.photo_cull import (
    apply_photo_cull,
    cull_stage_hint,
    format_ingest_progress_hint,
    run_photo_cull,
)
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _asset(
    aid: str,
    *,
    sharp: float = 100.0,
    media_class: str = "photo",
    user_tier: str = "material",
    dedupe_group: str | None = None,
    burst_group: str | None = None,
) -> dict:
    a: dict = {
        "id": aid,
        "type": "image",
        "mediaClass": media_class,
        "userTier": user_tier,
        "quality": {"sharpness": sharp},
        "layoutEligible": True,
    }
    if dedupe_group:
        a["dedupeGroupId"] = dedupe_group
    if burst_group:
        a["burstGroupId"] = burst_group
    return a


def _asset_with_face_ratio(aid: str, *, face_ratio: float, sharp: float = 100.0) -> dict:
    a = _asset(aid, sharp=sharp, media_class="photo")
    q = a.setdefault("quality", {})
    if isinstance(q, dict):
        q["faceRatio"] = face_ratio
    return a


def test_pass1_excludes_screenshot_and_blur() -> None:
    cfg = CullConfig(enabled=True, blur_percentile=50.0, sharpness_absolute_min=0.0)
    assets = [
        _asset("sharp", sharp=200.0),
        _asset("blur", sharp=1.0),
        _asset("shot", sharp=100.0, media_class="screenshot"),
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["sharp"]["layoutEligible"] is True
    assert by_id["blur"]["layoutEligible"] is False
    assert by_id["blur"]["excludeReason"] == "blur"
    assert by_id["shot"]["layoutEligible"] is False
    assert by_id["shot"]["excludeReason"] == "media_class"
    assert summary["excludedByReason"]["blur"] == 1
    assert summary["excludedByReason"]["media_class"] == 1


def test_bucketed_blur_thresholds_reduce_cross_bucket_over_kill() -> None:
    assets = [
        _asset("l1", sharp=120.0, media_class="photo"),
        _asset("l2", sharp=110.0, media_class="photo"),
        _asset("p1", sharp=22.0, media_class="archive"),
        _asset("p2", sharp=21.0, media_class="archive"),
    ]
    cfg_global = CullConfig(
        enabled=True,
        blur_percentile=50.0,
        bucketed_blur_thresholds=False,
        sharpness_absolute_min=0.0,
        min_keep=10,
        keep_ratio_floor=0.0,
    )
    global_assets = [dict(a) for a in assets]
    run_photo_cull(global_assets, cfg=cfg_global)
    assert any(a["id"].startswith("p") and not a.get("layoutEligible", True) for a in global_assets)

    cfg_bucketed = CullConfig(
        enabled=True,
        blur_percentile=50.0,
        bucketed_blur_thresholds=True,
        bucketed_blur_min_samples=2,
        sharpness_absolute_min=0.0,
        min_keep=10,
        keep_ratio_floor=0.0,
    )
    bucketed_assets = [dict(a) for a in assets]
    run_photo_cull(bucketed_assets, cfg=cfg_bucketed)
    assert all(a.get("layoutEligible", True) for a in bucketed_assets if a["id"].startswith("p"))


def test_featured_exempt_from_cull() -> None:
    cfg = CullConfig(enabled=True, blur_percentile=50.0)
    assets = [
        _asset("feat", sharp=1.0, user_tier="featured", media_class="screenshot"),
        _asset("mat", sharp=200.0),
    ]
    run_photo_cull(assets, cfg=cfg)
    feat = next(a for a in assets if a["id"] == "feat")
    assert feat["layoutEligible"] is True
    assert "excludeReason" not in feat


def test_format_ingest_progress_hint_merges_cull() -> None:
    assert format_ingest_progress_hint(45, 120, cull_enabled=True) == (
        "正在导入并挑选照片（已处理 45/120 张）"
    )
    assert format_ingest_progress_hint(45, 120, cull_enabled=False) == "已处理 45/120 张"


def test_cull_stage_hint_rules_vs_ml() -> None:
    assert cull_stage_hint(CullConfig(enabled=False)) == ""
    assert cull_stage_hint(CullConfig(enabled=True, mode="rules")) == "正在挑选照片…"
    assert cull_stage_hint(CullConfig(enabled=True, mode="ml")) in (
        "正在挑选照片…",
        "正在评估照片质量…",
    )


def test_culled_assets_retain_source_files(tmp_path: Path) -> None:
    trip_dir = tmp_path / "trip"
    source_dir = trip_dir / "source"
    source_dir.mkdir(parents=True)
    img_path = source_dir / "shot.jpg"
    Image.new("RGB", (2400, 3200), (40, 40, 40)).save(img_path, quality=95)
    trip: dict = {"curation": {}}
    assets = [
        {
            "id": "a1",
            "type": "image",
            "mediaClass": "screenshot",
            "sourceFile": "source/shot.jpg",
            "displayFile": "assets/a1-w800.webp",
            "quality": {"sharpness": 200.0},
            "layoutEligible": True,
        }
    ]
    apply_photo_cull(trip, assets, cfg=AppConfig(cull=CullConfig(enabled=True)))
    assert assets[0]["layoutEligible"] is False
    assert img_path.is_file()


def test_pass2_skips_material_only_groups() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=15,
        keep_ratio_floor=0.80,
        blur_percentile=0.0,
    )
    assets = [
        _asset("m1", sharp=120.0, dedupe_group="g1"),
        _asset("m2", sharp=200.0, dedupe_group="g1"),
        _asset("m3", sharp=180.0, dedupe_group="g1"),
    ]
    run_photo_cull(assets, cfg=cfg)
    assert all(a.get("layoutEligible", True) for a in assets)
    assert not any(a.get("excludeReason") == "duplicate_group" for a in assets)


def test_pass2_material_only_groups_collapse_when_strict_enabled() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        recalc_strict_groups=True,
    )
    assets = [
        _asset("m1", sharp=120.0, dedupe_group="g1"),
        _asset("m2", sharp=200.0, dedupe_group="g1"),
        _asset("m3", sharp=180.0, dedupe_group="g1"),
    ]
    run_photo_cull(assets, cfg=cfg)
    kept = [a for a in assets if a.get("layoutEligible", True)]
    assert len(kept) == 1
    assert kept[0]["id"] == "m2"
    dropped = [a for a in assets if not a.get("layoutEligible", True)]
    assert all(a.get("excludeReason") == "duplicate_group" for a in dropped)


def test_pass2_group_keeps_one_material_and_all_featured() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0)
    assets = [
        _asset("f1", sharp=150.0, user_tier="featured", dedupe_group="g1"),
        _asset("m1", sharp=120.0, dedupe_group="g1"),
        _asset("m2", sharp=200.0, dedupe_group="g1"),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["f1"]["layoutEligible"] is True
    assert by_id["m2"]["layoutEligible"] is True
    assert by_id["m1"]["layoutEligible"] is False
    assert by_id["m1"]["excludeReason"] == "duplicate_group"


def test_pass3_skipped_when_pool_at_floor() -> None:
    cfg = CullConfig(enabled=True, min_keep=15, keep_ratio_floor=0.80)
    assets = [_asset(f"a{i}", sharp=100.0 + float(i)) for i in range(10)]
    summary = run_photo_cull(assets, cfg=cfg)
    assert summary["pass3Skipped"] == "pool_at_or_below_floor"
    assert summary["layoutEligibleCount"] == 10


def test_apply_photo_cull_writes_trip_curation() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0)
    trip: dict = {"curation": {}}
    ingest_stats: dict = {}
    assets = [
        _asset("a1", sharp=200.0),
        _asset("a2", sharp=1.0, media_class="screenshot"),
    ]
    summary = apply_photo_cull(trip, assets, cfg=AppConfig(cull=cfg), ingest_stats=ingest_stats)
    assert trip["curation"]["cullUserLine"].startswith("经挑选")
    assert "cullSummary" in trip["curation"]
    assert summary["cullUserLine"] == trip["curation"]["cullUserLine"]
    assert summary["failOpen"] is False
    assert ingest_stats.get("cull_fail_open") is False
    assert ingest_stats.get("cull_l1_ml_fallback_rate") in (0.0, 1.0)
    assert 0.0 <= float(ingest_stats.get("cull_l2_branch_fallback_rate") or 0.0) <= 1.0
    assert ingest_stats.get("cull_l3_fail_open_rate") == 0.0
    assert "a2" in trip["curation"]["excludedByCullAssetIds"]


def test_cull_disabled_leaves_assets() -> None:
    cfg = CullConfig(enabled=False)
    trip: dict = {"curation": {}}
    assets = [_asset("a1", sharp=1.0, media_class="screenshot")]
    summary = apply_photo_cull(trip, assets, cfg=AppConfig(cull=cfg))
    assert summary["enabled"] is False
    assert assets[0]["layoutEligible"] is True


def test_layout_eligible_assets_excludes_culled() -> None:
    trip = {
        "assets": [
            {"id": "in", "type": "image", "layoutEligible": True},
            {"id": "out", "type": "image", "layoutEligible": False, "excludeReason": "blur"},
        ]
    }
    ids = [a["id"] for a in layout_eligible_assets(trip)]
    assert ids == ["in"]


def test_dual_folder_featured_all_eligible(tmp_path: Path) -> None:
    root = tmp_path / "album"
    feat = root / "精选"
    mat = root / "素材上传"
    feat.mkdir(parents=True)
    mat.mkdir(parents=True)
    stamp = time.time()
    for i in range(2):
        path = feat / f"f{i}.jpg"
        Image.new("RGB", (2400, 3200), (200, 100 + i * 10, 50)).save(path, quality=95)
        os.utime(path, (stamp + i, stamp + i))
    for i in range(6):
        path = mat / f"m{i}.jpg"
        Image.new("RGB", (2400, 3200), (80, 120 + i * 5, 160)).save(path, quality=95)
        os.utime(path, (stamp + 10 + i, stamp + 10 + i))
    trips = tmp_path / "trips"
    trip_json = create_trip("dual-cull", trips)
    trip_dir = trips / "dual-cull"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=root, dedupe=False)
    featured = [a for a in trip["assets"] if a.get("userTier") == "featured"]
    assert len(featured) == 2
    assert all(a.get("layoutEligible", True) for a in featured)


def test_featured_low_res_stays_eligible() -> None:
    trip: dict = {"curation": {}}
    assets = [
        {
            "id": "feat",
            "type": "image",
            "userTier": "featured",
            "nativeWidth": 900,
            "nativeHeight": 700,
            "width": 900,
            "height": 700,
            "layoutEligible": True,
        },
    ] + [
        {
            "id": f"ok{i}",
            "type": "image",
            "nativeWidth": 3200,
            "nativeHeight": 2400,
            "width": 3200,
            "height": 2400,
            "layoutEligible": True,
        }
        for i in range(5)
    ]
    apply_layout_eligibility_marks(
        trip,
        assets,
        cfg=IngestConfig(min_long_edge_layout_px=800),
        app_cfg=AppConfig(cull=CullConfig(featured_exempt_low_res=True)),
    )
    feat = next(a for a in assets if a["id"] == "feat")
    assert feat["layoutEligible"] is True
    assert feat.get("quality", {}).get("lowResSuspected") is True
    assert "feat" not in (trip.get("curation") or {}).get("excludedLowResAssetIds", [])


def test_incremental_ingest_reculls_full_trip(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    stamp = time.time()
    for i in range(4):
        path = album / f"p{i}.jpg"
        Image.new("RGB", (2400, 3200), (30 + i * 20, 50, 70)).save(path, quality=95)
        os.utime(path, (stamp + i * 10, stamp + i * 10))
    trips = tmp_path / "trips"
    trip_json = create_trip("recull", trips)
    trip_dir = trips / "recull"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    first_summary = dict((trip.get("curation") or {}).get("cullSummary") or {})
    assert first_summary.get("scanned") == 4

    path = album / "p4.jpg"
    Image.new("RGB", (2400, 3200), (200, 80, 40)).save(path, quality=95)
    os.utime(path, (stamp + 50, stamp + 50))
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, incremental=True)
    second_summary = (trip.get("curation") or {}).get("cullSummary") or {}
    assert len(trip["assets"]) == 5
    assert second_summary.get("scanned") == len(trip["assets"])


def test_recull_preserves_non_cull_exclusions() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0)
    assets = [
        {
            "id": "lowres",
            "type": "image",
            "mediaClass": "photo",
            "layoutEligible": False,
            "excludeReason": "low_resolution",
            "quality": {"sharpness": 180.0},
        },
        _asset("ok", sharp=200.0),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["lowres"]["layoutEligible"] is False
    assert by_id["lowres"]["excludeReason"] == "low_resolution"
    assert by_id["ok"]["layoutEligible"] is True


def test_ac_p9_02_golden_signoff_keep_ratio() -> None:
    """AC-P9-02 · golden signoff 登记：cull 层保留率 ≥ floor 或 pass3 跳过。"""
    path = repo_root(__file__) / "docs/acceptance-records/phase9-golden-cull-signoff.json"
    if not path.is_file():
        pytest.skip("phase9-golden-cull-signoff.json missing")
    from travelogue.config import CullConfig

    data = json.loads(path.read_text(encoding="utf-8"))
    default_floor = CullConfig().keep_ratio_floor
    for run in data.get("runs") or []:
        trip_id = str(run.get("tripId") or "")
        metrics = run.get("metrics") or {}
        scanned = int(metrics.get("scanned") or 0)
        assert scanned > 0, trip_id
        assert metrics.get("curateSmokeOk") is True, trip_id
        floor = float(metrics.get("keepRatioFloor") or default_floor)
        if metrics.get("floorMet") or metrics.get("pass3Skipped"):
            continue
        line = str(metrics.get("cullUserLine") or "")
        match = re.search(r"经挑选\s*(\d+)", line)
        if match:
            cull_ratio = int(match.group(1)) / scanned
            assert cull_ratio >= floor, f"{trip_id} cull layer {cull_ratio:.4f}"
            continue
        ratio = float(metrics.get("nonFeaturedKeepRatio") or 0)
        assert ratio >= floor, f"{trip_id} final ratio {ratio:.4f}"


def test_cull_fail_open_restores_eligible(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("cull exploded")

    monkeypatch.setattr("travelogue.curation.photo_cull.run_photo_cull", _boom)
    trip: dict = {"curation": {}}
    assets = [
        _asset("a1", sharp=1.0, media_class="screenshot"),
        _asset("a2", sharp=200.0),
    ]
    ingest_stats: dict = {}
    summary = apply_photo_cull(
        trip,
        assets,
        cfg=AppConfig(cull=CullConfig(enabled=True)),
        ingest_stats=ingest_stats,
    )
    assert all(a.get("layoutEligible", True) for a in assets)
    assert all("excludeReason" not in a for a in assets)
    assert summary.get("failOpen") is True
    assert summary.get("error")
    assert summary.get("failOpenRateL3") == 1.0
    assert ingest_stats.get("cull_fail_open") is True
    assert ingest_stats.get("cull_l1_ml_fallback_rate") == 0.0
    assert ingest_stats.get("cull_l2_branch_fallback_rate") == 0.0
    assert ingest_stats.get("cull_l3_fail_open_rate") == 1.0
    assert trip["curation"]["cullSummary"].get("error")
    assert trip["curation"]["cullSummary"].get("failOpenRateL3") == 1.0


def test_keep_ratio_floor_or_pass3_skip() -> None:
    cfg = CullConfig(enabled=True, min_keep=15, keep_ratio_floor=0.80)
    assets = [_asset(f"a{i:03d}", sharp=50.0 + float(i)) for i in range(100)]
    summary = run_photo_cull(assets, cfg=cfg)
    n_scan = 100
    non_feat = sum(
        1 for a in assets if a.get("layoutEligible", True) and a.get("userTier") != "featured"
    )
    floor = int(summary.get("floorTargetNonFeatured") or 0)
    if summary.get("pass3Skipped"):
        assert non_feat >= len(assets) or summary["pass3Skipped"] == "pool_at_or_below_floor"
    else:
        assert non_feat >= max(floor, int(cfg.keep_ratio_floor * n_scan))


def test_pass3_weights_from_config_affect_rank() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=1.0,
        score_media_weight_rules=0.0,
    )
    assets = [
        _asset("a-sharp", sharp=200.0, media_class="archive"),
        _asset("a-media", sharp=30.0, media_class="photo"),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["a-sharp"]["layoutEligible"] is True
    assert by_id["a-media"]["layoutEligible"] is False
    assert by_id["a-media"]["excludeReason"] == "cull_quota"


def test_branch_score_prefers_portrait_when_face_ratio_high() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=0.0,
        score_media_weight_rules=0.0,
        score_branch_weight_portrait=1.0,
        score_branch_weight_landscape=0.0,
    )
    assets = [
        _asset_with_face_ratio("portrait", face_ratio=0.35, sharp=90.0),
        _asset_with_face_ratio("landscape", face_ratio=0.01, sharp=90.0),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["portrait"]["layoutEligible"] is True
    assert by_id["landscape"]["layoutEligible"] is False
    assert by_id["portrait"]["quality"]["cullBranch"] == "portrait"


def test_summary_includes_branch_ratios() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0)
    assets = [
        _asset_with_face_ratio("p", face_ratio=0.3, sharp=120.0),
        _asset_with_face_ratio("g", face_ratio=0.12, sharp=120.0),
        _asset_with_face_ratio("l", face_ratio=0.01, sharp=120.0),
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    assert "branchPortraitRatio" in summary
    assert "branchLandscapeRatio" in summary
    assert "branchGrayRatio" in summary
    assert float(summary.get("cpuMs", 0.0)) >= 0.0
    assert "branchFallbackRateL2" in summary
    assert "branchFallbackByReasonL2" in summary
    assert summary.get("failOpenRateL3") == 0.0


def test_pass3_applies_threshold_without_breaking_floor() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=3,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=1.0,
        score_media_weight_rules=0.0,
        score_threshold=0.95,
    )
    assets = [_asset(f"a{i}", sharp=10.0 + i) for i in range(6)]
    summary = run_photo_cull(assets, cfg=cfg)
    kept = [a for a in assets if a.get("layoutEligible", True)]
    assert len(kept) == 3
    assert summary.get("scoreThreshold") == 0.95


def test_pass3_applies_topk_ratio_without_breaking_floor() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=2,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=1.0,
        score_media_weight_rules=0.0,
        score_topk_ratio=0.4,
    )
    assets = [_asset(f"a{i}", sharp=10.0 + i) for i in range(10)]
    summary = run_photo_cull(assets, cfg=cfg)
    kept = [a for a in assets if a.get("layoutEligible", True)]
    assert len(kept) == 4
    assert summary.get("scoreTopkRatio") == 0.4


def test_rank_tie_break_uses_sharpness_before_id() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=0.0,
        score_media_weight_rules=0.0,
        score_topk_ratio=0.5,
    )
    assets = [
        _asset("b", sharp=200.0),
        _asset("a", sharp=10.0),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["b"]["layoutEligible"] is True
    assert by_id["a"]["layoutEligible"] is False


def test_branch_fallback_l2_face_signal_missing_counted() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0, portrait_quality_enabled=True)
    assets = [
        _asset_with_face_ratio("p", face_ratio=0.3, sharp=120.0),
        _asset("x", sharp=120.0),
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    assert summary.get("branchFallbackRateL2") == 0.5
    by_reason = summary.get("branchFallbackByReasonL2") or {}
    assert by_reason.get("face_signal_missing") == 1


def test_branch_fallback_l2_gray_zone_counted() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0, portrait_quality_enabled=True)
    assets = [
        _asset_with_face_ratio("g", face_ratio=0.12, sharp=120.0),
        _asset_with_face_ratio("p", face_ratio=0.3, sharp=120.0),
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    assert summary.get("branchFallbackRateL2") == 0.5
    by_reason = summary.get("branchFallbackByReasonL2") or {}
    assert by_reason.get("gray_zone") == 1


def test_branch_fallback_l2_branch_disabled_is_full_ratio() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        portrait_quality_enabled=False,
    )
    assets = [
        _asset_with_face_ratio("a", face_ratio=0.3, sharp=120.0),
        _asset("b", sharp=120.0),
        _asset("c", sharp=120.0),
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    assert summary.get("branchFallbackRateL2") == 1.0
    by_reason = summary.get("branchFallbackByReasonL2") or {}
    assert by_reason.get("branch_disabled") == 3


def test_duplicate_group_penalty_changes_rank() -> None:
    cfg = CullConfig(
        enabled=True,
        min_keep=1,
        keep_ratio_floor=0.0,
        score_sharpness_weight_rules=0.8,
        score_media_weight_rules=0.2,
        score_duplicate_group_penalty=0.2,
    )
    assets = [
        _asset("a1", sharp=100.0, media_class="photo", dedupe_group="g1"),
        _asset("a2", sharp=98.0, media_class="photo", dedupe_group="g1"),
        _asset("b1", sharp=98.0, media_class="photo"),
    ]
    run_photo_cull(assets, cfg=cfg)
    by_id = {a["id"]: a for a in assets}
    assert by_id["a2"]["layoutEligible"] is False
    assert by_id["a2"]["excludeReason"] == "cull_quota"
    assert by_id["a2"].get("quality", {}).get("cullScore", 1.0) < by_id["b1"].get("quality", {}).get("cullScore", 0.0)


def test_ingest_cull_summary_includes_post_low_res_counts(tmp_path: Path) -> None:
    album = tmp_path / "album-lowres"
    album.mkdir()
    stamp = time.time()
    for i in range(5):
        path = album / f"ok{i}.jpg"
        Image.new("RGB", (2400, 3200), (40 + i * 20, 60, 80)).save(path, quality=95)
        os.utime(path, (stamp + i * 10, stamp + i * 10))
    low = album / "low.jpg"
    Image.new("RGB", (700, 700), (30, 30, 30)).save(low, quality=95)
    os.utime(low, (stamp + 60, stamp + 60))

    trips = tmp_path / "trips"
    trip_json = create_trip("lowres-metrics", trips)
    trip_dir = trips / "lowres-metrics"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)

    cull = (trip.get("curation") or {}).get("cullSummary") or {}
    pre = int(cull.get("layoutEligibleCount") or 0)
    final = int(cull.get("finalLayoutEligibleCount") or 0)
    assert pre >= final >= 0
    assert "finalNonFeaturedEligibleCount" in cull
    assert "finalNonFeaturedKeepRatio" in cull
    low_res_ids = (trip.get("curation") or {}).get("excludedLowResAssetIds") or []
    if low_res_ids:
        assert final < pre


def test_cull_explain_written_for_excluded_assets() -> None:
    cfg = CullConfig(enabled=True, blur_percentile=50.0, enable_cull_explain=True)
    assets = [
        _asset("sharp", sharp=200.0),
        _asset("blur", sharp=1.0),
    ]
    run_photo_cull(assets, cfg=cfg)
    blur = next(a for a in assets if a["id"] == "blur")
    assert blur.get("excludeReason") == "blur"
    assert "cullExplain" in (blur.get("quality") or {})


def test_max_photos_exceeded_warn_only() -> None:
    cfg = CullConfig(enabled=True, min_keep=1, keep_ratio_floor=0.0, max_photos_warn_only=True)
    assets = [_asset(f"f{i}", sharp=100.0, user_tier="featured") for i in range(260)]
    summary = run_photo_cull(assets, cfg=cfg, max_photos=250)
    assert summary["maxPhotosExceeded"] is True
    assert summary["layoutEligibleCount"] == 260
    assert "warnMessage" in summary


def test_clustering_embed_skips_culled_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: list[str] = []

    def _fake_prepare(_trip_dir, assets, _encoder, **_kwargs):
        captured.extend(str(a.get("id")) for a in assets)
        plan = MagicMock()
        plan.cache_hit_ratio.return_value = 1.0
        plan.mode = "reuse"
        plan.change_ratio = 0.0
        plan.new_ids = []
        plan.removed_ids = []
        bundle = MagicMock()
        bundle.asset_ids = []
        bundle.vectors = []
        bundle.source = "clip"
        bundle.model = "test"
        return bundle, plan

    monkeypatch.setattr(
        "travelogue.curation.clustering.prepare_scene_embeddings",
        _fake_prepare,
    )
    monkeypatch.setattr("travelogue.curation.clustering.vision_stack_available", lambda: True)
    monkeypatch.setattr("travelogue.curation.clustering.clip_torch_available", lambda: True)
    monkeypatch.setattr("travelogue.curation.clustering.clip_weights_likely_cached", lambda **_k: True)
    monkeypatch.setattr(
        "travelogue.curation.clustering.get_clip_encoder",
        lambda _cfg: MagicMock(last_embed_stats=None),
    )
    monkeypatch.setattr(
        "travelogue.curation.clustering.embedding_cache_is_corrupt",
        lambda _d: False,
    )

    trip = {
        "assets": [
            {
                "id": "culled",
                "type": "image",
                "layoutEligible": False,
                "takenAt": "2025-04-01T10:00:00Z",
            },
            {
                "id": "keep",
                "type": "image",
                "layoutEligible": True,
                "takenAt": "2025-04-01T11:00:00Z",
                "geo": {"lat": 35.0, "lon": 139.0},
            },
        ],
        "curation": {},
        "meta": {"title": "t", "dateStart": "2025-04-01", "dateEnd": "2025-04-02"},
    }
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true", auto_min_photos=1, auto_min_eligible_ratio=0.0),
    )
    run_clustering_layer(trip, trip_dir=tmp_path / "trip", cfg=cfg)
    assert captured == ["keep"]


@pytest.mark.integration
def test_nr_p9_01_clustering_off_cull_on_curate_smoke(ingested_trip) -> None:
    _ws, trip = ingested_trip
    cfg = AppConfig(clustering=ClusteringConfig(enabled="false"), cull=CullConfig(enabled=True))
    run_curate(trip, export_layout="mobile", cfg=cfg)
    assert len(trip.get("chapters") or []) >= 3
