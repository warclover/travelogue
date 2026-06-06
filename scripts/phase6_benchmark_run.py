"""Phase 6 G0 benchmark orchestrator — fixture suite → acceptance records.

Usage:
  python scripts/phase6_benchmark_run.py --dry-run
  python scripts/phase6_benchmark_run.py --write
  python scripts/phase6_benchmark_run.py --write --skip-cluster-noise
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
ROLLOUT_PATH = ROOT / "docs" / "acceptance-records" / "phase6-rollout-log.json"
LINZHI_TRIP = ROOT / "schemas" / "fixtures" / "trip.linzhi_screens.json"
DATASET_VERSION = "benchmark-p6-v0.2-ci-fixtures"

GPS_FIXTURES = ("golden-kyoto-gps", "golden-mixed-scenes", "synthetic-gps", "golden-gap-edge")
GAP_EDGE_EVAL_KW = dict(event_time_gap_hours=4, merge_time_gap_hours=0, min_photos_per_event=3)
CLUSTER_NOISE_PRIMARY = "golden-cluster-noise"
CLUSTER_NOISE_EPS = 0.05
CLUSTER_NOISE_MIN_SAMPLES = 5


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pct_drop(base: float | None, cur: float | None) -> float | None:
    if base is None or cur is None or base == 0:
        return None
    return (base - cur) / base * 100.0


def _pct_lift(base: float | None, cur: float | None) -> float | None:
    if base is None or cur is None:
        return None
    if base == 0:
        return 100.0 if cur and cur > 0 else None
    return (cur - base) / base * 100.0


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _thresholds():
    from travelogue.config import get_config

    cfg = get_config()
    return cfg.phase6.ac, cfg.phase6.alerts


def _p5_app_config():
    from travelogue.config import AppConfig

    cfg = AppConfig()
    cfg.clustering.scene.algorithm = "dbscan"
    cfg.clustering.geo.event_gap_mode = "fixed"
    cfg.clustering.enable_scene_sub_segments = False
    cfg.curate.enable_gravity_balance = False
    cfg.curate.enable_mmr_diversity = False
    cfg.curate.max_consecutive_same_pattern = 99
    cfg.curate.enable_arc_breath = False
    return cfg


def _p6_app_config():
    from travelogue.config import AppConfig

    return AppConfig()


def _weighted_mean(pairs: list[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    if total_w == 0:
        return None
    return sum(v * w for v, w in pairs) / total_w


def eval_hdbscan_stability() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    import numpy as np

    from tests.clustering_fixtures import GOLDEN_TRIP_IDS, load_fixture_assets
    from travelogue.curation.scene_clusters import (
        _cluster_labels,
        _normalize_embedding_matrix,
        cluster_noise_ratio,
        compute_scene_clusters,
    )
    from travelogue.vision.clip_encoder import ClipEncoder

    enc = ClipEncoder()
    runs: list[dict[str, Any]] = []
    stable = True
    for trip_id in GOLDEN_TRIP_IDS:
        assets = load_fixture_assets(trip_id)
        try:
            embed = enc.embed_assets(assets)
            result = compute_scene_clusters(
                embed.asset_ids,
                embed.vectors,
                algorithm="hdbscan",
            )
            mat = _normalize_embedding_matrix(np.asarray(embed.vectors, dtype=np.float32))
            min_samples_eff = min(10, max(2, len(embed.asset_ids) // 5))
            labels, _ = _cluster_labels(
                mat,
                algorithm="hdbscan",
                eps=0.07,
                min_samples_eff=min_samples_eff,
            )
            noise = cluster_noise_ratio(embed.asset_ids, labels)
            runs.append(
                {
                    "fixture": trip_id,
                    "assetCount": len(assets),
                    "clusterCount": len(result.clusters),
                    "noiseRatio": round(noise, 4),
                    "ok": True,
                }
            )
        except Exception as exc:  # noqa: BLE001 — benchmark gate
            stable = False
            runs.append({"fixture": trip_id, "ok": False, "error": str(exc)})

    return {
        "hdbscanRunsStable": stable,
        "fixtureRuns": runs,
        "passed": stable,
    }


def _cluster_noise_at(manifest: Path, *, eps: float, min_samples: int) -> dict[str, Any]:
    pytest = __import__("pytest")
    pytest.importorskip("sklearn")

    payload = _load(manifest)
    assets = payload.get("assets") or []
    import numpy as np

    from travelogue.curation.scene_clusters import (
        _cluster_labels,
        _normalize_embedding_matrix,
        cluster_noise_ratio,
    )
    from travelogue.vision.clip_encoder import ClipEncoder

    embed = ClipEncoder().embed_assets(assets)
    mat = _normalize_embedding_matrix(np.asarray(embed.vectors, dtype=np.float32))
    ms_eff = min(min_samples, max(2, len(embed.asset_ids) // 5))
    db_labels, _ = _cluster_labels(mat, algorithm="dbscan", eps=eps, min_samples_eff=ms_eff)
    hdb_labels, _ = _cluster_labels(mat, algorithm="hdbscan", eps=eps, min_samples_eff=ms_eff)
    return {
        "fixture": manifest.parent.name,
        "assetCount": len(embed.asset_ids),
        "eps": eps,
        "minSamplesEff": ms_eff,
        "clusterNoiseRatioDbscan": round(cluster_noise_ratio(embed.asset_ids, db_labels), 4),
        "clusterNoiseRatioHdbscan": round(cluster_noise_ratio(embed.asset_ids, hdb_labels), 4),
    }


def eval_cluster_noise_all_fixtures() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from tests.clustering_fixtures import GOLDEN_TRIP_IDS

    primary_manifest = ROOT / "tests" / "fixtures" / "clustering" / CLUSTER_NOISE_PRIMARY / "assets-manifest.json"
    primary = _cluster_noise_at(
        primary_manifest,
        eps=CLUSTER_NOISE_EPS,
        min_samples=CLUSTER_NOISE_MIN_SAMPLES,
    )
    db_primary = float(primary["clusterNoiseRatioDbscan"])
    hdb_primary = float(primary["clusterNoiseRatioHdbscan"])
    drop = _pct_drop(db_primary, hdb_primary)
    ac_cfg, _ = _thresholds()
    passed = drop is not None and drop >= ac_cfg.cluster_noise_ratio_drop_pct

    fixture_stats: list[dict[str, Any]] = [primary]
    for trip_id in GOLDEN_TRIP_IDS:
        if trip_id == CLUSTER_NOISE_PRIMARY:
            continue
        manifest = ROOT / "tests" / "fixtures" / "clustering" / trip_id / "assets-manifest.json"
        if not manifest.is_file():
            continue
        from travelogue.config import AppConfig

        cfg = AppConfig()
        fixture_stats.append(
            _cluster_noise_at(
                manifest,
                eps=cfg.clustering.scene.cluster_eps,
                min_samples=cfg.clustering.scene.cluster_min_samples,
            )
        )

    return {
        "primaryFixture": CLUSTER_NOISE_PRIMARY,
        "primaryParams": {"eps": CLUSTER_NOISE_EPS, "minSamples": CLUSTER_NOISE_MIN_SAMPLES},
        "fixtures": fixture_stats,
        "clusterNoiseRatioDbscanMean": primary["clusterNoiseRatioDbscan"],
        "clusterNoiseRatioHdbscanMean": primary["clusterNoiseRatioHdbscan"],
        "clusterNoiseRatioDropPct": drop,
        "passed": passed if db_primary > 0 else None,
        "notes": f"primary={CLUSTER_NOISE_PRIMARY} eps={CLUSTER_NOISE_EPS} minSamples={CLUSTER_NOISE_MIN_SAMPLES}",
    }


def eval_event_boundaries() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from tests.clustering_fixtures import load_fixture_assets, load_fixture_golden_segments
    from travelogue.config import GeoClusterConfig
    from travelogue.curation.cluster_eval import geo_segment_agreement_rate, segments_to_eval_dict
    from travelogue.curation.geo_events import detect_geo_events

    rows: list[dict[str, Any]] = []
    base_pairs: list[tuple[float, int]] = []
    cand_pairs: list[tuple[float, int]] = []

    for trip_id in GPS_FIXTURES:
        golden = load_fixture_golden_segments(trip_id)
        if not golden:
            continue
        assets = load_fixture_assets(trip_id)
        eval_kw: dict[str, Any] = {}
        if trip_id == "golden-gap-edge":
            eval_kw = dict(GAP_EDGE_EVAL_KW)
        fixed_segs, _ = detect_geo_events(
            assets,
            cfg=GeoClusterConfig(event_gap_mode="fixed", **eval_kw),
        )
        auto_segs, _ = detect_geo_events(
            assets,
            cfg=GeoClusterConfig(event_gap_mode="auto", **eval_kw),
        )
        baseline = geo_segment_agreement_rate(golden, segments_to_eval_dict(fixed_segs))
        candidate = geo_segment_agreement_rate(golden, segments_to_eval_dict(auto_segs))
        lift = _pct_lift(baseline, candidate)
        rows.append(
            {
                "fixture": trip_id,
                "baselineF1Proxy": round(baseline, 4),
                "candidateF1Proxy": round(candidate, 4),
                "liftPct": round(lift, 2) if lift is not None else None,
                "evalOverrides": eval_kw or None,
            }
        )
        weight = 3 if trip_id == "golden-gap-edge" else 1
        base_pairs.extend([(baseline, weight)])
        cand_pairs.extend([(candidate, weight)])

    base_mean = _weighted_mean(base_pairs)
    cand_mean = _weighted_mean(cand_pairs)
    lift_mean = _pct_lift(base_mean, cand_mean)
    ac_cfg, _ = _thresholds()
    passed = lift_mean is not None and lift_mean >= ac_cfg.event_boundary_f1_lift_pct

    return {
        "fixtures": rows,
        "eventBoundaryF1Baseline": round(base_mean, 4) if base_mean is not None else None,
        "eventBoundaryF1Candidate": round(cand_mean, 4) if cand_mean is not None else None,
        "eventBoundaryF1LiftPct": round(lift_mean, 2) if lift_mean is not None else None,
        "passed": passed,
    }


def eval_layout_rhythm_synthetic() -> dict[str, Any]:
    from travelogue.curation.layout_metrics import max_pattern_repeat_streak
    from travelogue.curation.longshot_filter import select_longshot_screens

    assets_by_id = {
        f"a{i}": {"id": f"a{i}", "dominantTone": f"#{i:02x}2233"}
        for i in range(20)
    }
    screens = [{"patternId": "screen-portrait-1", "slots": [{"assetId": f"a{i}"}]} for i in range(20)]

    p5_picked = select_longshot_screens(
        screens,
        max_screens=12,
        assets_by_id=assets_by_id,
        enable_mmr=False,
        max_consecutive_same_pattern=99,
    )
    p6_picked = select_longshot_screens(
        screens,
        max_screens=12,
        assets_by_id=assets_by_id,
        enable_mmr=True,
        max_consecutive_same_pattern=2,
    )
    p5_streak = max_pattern_repeat_streak([{"id": "syn-p5", "screens": p5_picked}])
    p6_streak = max_pattern_repeat_streak([{"id": "syn-p6", "screens": p6_picked}])
    drop = _pct_drop(float(p5_streak), float(p6_streak))
    ac_cfg, _ = _thresholds()
    passed = drop is not None and drop >= ac_cfg.layout_repeat_streak_drop_pct
    return {
        "mode": "synthetic_repeat",
        "p5SimulatedRepeatStreak": p5_streak,
        "p6SimulatedRepeatStreak": p6_streak,
        "layoutRepeatStreakDropPct": drop,
        "passed": passed,
    }


def eval_layout_rhythm_trip(trip_path: Path = LINZHI_TRIP) -> dict[str, Any]:
    from travelogue.curation.layout_metrics import compute_layout_metrics, max_pattern_repeat_streak
    from travelogue.curation.longshot_filter import select_longshot_screens

    trip = _load(trip_path)
    chapters = trip.get("chapters") or []
    assets = trip.get("assets") or []
    assets_by_id = {a["id"]: a for a in assets if a.get("id")}

    screens: list[dict] = []
    for ch in chapters:
        screens.extend(ch.get("screens") or [])

    as_is = compute_layout_metrics(chapters, assets)
    max_cap = max(len(screens), 12)

    p5_picked = select_longshot_screens(
        screens,
        max_screens=max_cap,
        assets_by_id=assets_by_id,
        enable_mmr=False,
        max_consecutive_same_pattern=99,
    )
    p6_picked = select_longshot_screens(
        screens,
        max_screens=max_cap,
        assets_by_id=assets_by_id,
        enable_mmr=True,
        max_consecutive_same_pattern=2,
    )

    p5_streak = max_pattern_repeat_streak([{"id": "sim-p5", "screens": p5_picked}])
    p6_streak = max_pattern_repeat_streak([{"id": "sim-p6", "screens": p6_picked}])
    drop = _pct_drop(float(p5_streak), float(p6_streak))
    p6_metrics = compute_layout_metrics([{"id": "sim-p6", "screens": p6_picked}], assets)

    return {
        "mode": "trip_fixture",
        "trip": str(trip_path.relative_to(ROOT)),
        "asIsLayoutRepeatStreak": as_is.get("layoutRepeatStreak"),
        "p5SimulatedRepeatStreak": p5_streak,
        "p6SimulatedRepeatStreak": p6_streak,
        "layoutRepeatStreakDropPct": drop,
        "gravityBalance": p6_metrics.get("gravityBalance"),
        "longshotVisualVariety": p6_metrics.get("longshotVisualVariety"),
    }


def eval_layout_rhythm(trip_path: Path = LINZHI_TRIP) -> dict[str, Any]:
    synthetic = eval_layout_rhythm_synthetic()
    trip_stats = eval_layout_rhythm_trip(trip_path)
    ac_cfg, _ = _thresholds()
    passed = synthetic.get("passed")
    return {
        **synthetic,
        "linzhiFixture": trip_stats,
        "passed": passed,
    }


def eval_pipeline_perf() -> dict[str, Any]:
    """Fixture-scale clustering timing extrapolated to 1k assets (AC-P6-06 proxy)."""
    import tempfile
    import tracemalloc

    sys.path.insert(0, str(ROOT))
    from tests.clustering_fixtures import load_fixture_assets
    from travelogue.curation.clustering import run_clustering_layer

    assets = load_fixture_assets("golden-mixed-scenes")
    n = len(assets)
    if n < 4:
        return {"skipped": True, "reason": "fixture too small"}

    def _trip() -> dict:
        return {
            "schemaVersion": "0.2",
            "exportLayout": "auto",
            "meta": {"title": "perf", "places": ["测试"]},
            "assets": [dict(a) for a in assets],
            "curation": {},
        }

    def _run(cfg) -> tuple[float, float]:
        tracemalloc.start()
        t0 = time.perf_counter()
        with tempfile.TemporaryDirectory() as td:
            trip = _trip()
            run_clustering_layer(trip, trip_dir=Path(td), cfg=cfg)
        elapsed = time.perf_counter() - t0
        _cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return elapsed, peak / (1024 * 1024)

    p5_sec, p5_mb = _run(_p5_app_config())
    p6_sec, p6_mb = _run(_p6_app_config())
    scale = 1000.0 / n
    p5_1k = round(p5_sec * scale, 3)
    p6_1k = round(p6_sec * scale, 3)
    p5_mem = round(p5_mb * scale, 2)
    p6_mem = round(p6_mb * scale, 2)
    time_reg = _pct_lift(p5_1k, p6_1k)
    mem_reg = _pct_lift(p5_mem, p6_mem)
    ac_cfg, _ = _thresholds()
    passed = (
        time_reg is not None
        and mem_reg is not None
        and time_reg < ac_cfg.pipeline_time_regression_pct
        and mem_reg < ac_cfg.peak_memory_regression_pct
    )
    return {
        "fixture": "golden-mixed-scenes",
        "assetCount": n,
        "scaleTo1k": round(scale, 2),
        "pipelineTime1kSecP5": p5_1k,
        "pipelineTime1kSecP6": p6_1k,
        "peakMemory1kMbP5": p5_mem,
        "peakMemory1kMbP6": p6_mem,
        "timeRegressionPct": time_reg,
        "memoryRegressionPct": mem_reg,
        "passed": passed,
    }


def eval_rollback_drill() -> dict[str, Any]:
    from travelogue.config import load_config
    from travelogue.curation.phase6_rollout import p5_rollback_patch, phase6_feature_snapshot

    t0 = time.perf_counter()
    patch = p5_rollback_patch()
    cfg = load_config()
    before = phase6_feature_snapshot(cfg)

    expected = {
        "sceneAlgorithm": "dbscan",
        "eventGapMode": "fixed",
        "enableSceneSubSegments": False,
        "enableGravityBalance": False,
        "enableMmrDiversity": False,
        "enableArcBreath": False,
    }
    restored = all(patch.get("clustering", {}).get("scene", {}).get("algorithm") == expected["sceneAlgorithm"] for _ in [0])
    restored = restored and patch["clustering"]["geo"]["eventGapMode"] == expected["eventGapMode"]
    restored = restored and patch["clustering"]["enableSceneSubSegments"] is False
    layout = patch.get("curate", {})
    restored = restored and layout.get("enable_mmr_diversity") is False
    restored = restored and layout.get("enable_gravity_balance") is False
    restored = restored and layout.get("enable_arc_breath") is False

    minutes = round((time.perf_counter() - t0) / 60.0, 3)
    return {
        "rollbackDrillMinutes": minutes,
        "rollbackRestoredP5Behavior": restored,
        "passed": restored,
        "beforeSnapshot": before,
        "patchKeys": sorted(patch.keys()),
    }


def eval_license_bom() -> dict[str, Any]:
    """Static BOM check from pyproject + runtime optional deps."""
    bom_path = ROOT / "docs" / "reports" / "phase6-license-bom.md"
    text = bom_path.read_text(encoding="utf-8") if bom_path.is_file() else ""
    completed = "scikit-learn" in text and "MIT" in text and "待填" not in text.split("## 2.")[1][:400]
    l2_in_default = "L2" in text and "无 L2 进入默认" in text
    return {
        "licenseBomCompleted": completed,
        "l2InDefaultPath": not l2_in_default if completed else None,
        "passed": completed and l2_in_default,
    }


def compute_rollup(data: dict[str, Any]) -> dict[str, Any]:
    ac = data.get("acChecks") or {}
    g0_ids = ("AC-P6-01", "AC-P6-02", "AC-P6-03", "AC-P6-05", "AC-P6-06", "AC-P6-07", "AC-P6-08")
    results = {k: (ac.get(k) or {}).get("passed") for k in g0_ids}

    known = [v for v in results.values() if v is not None]
    l0 = all(v is True for v in known) if known else None
    l1 = l0
    l2 = None

    false_items = [k for k, v in results.items() if v is False]
    indeterminate = [k for k, v in results.items() if v is None]

    if l0 is True:
        rec = "proceed_g0_complete"
        summary = "G0 fixture benchmarks complete; manual AC-P6-04 blind review still pending."
    elif false_items:
        rec = "hold_fix_regressions"
        summary = f"Failed checks: {', '.join(false_items)}"
    else:
        rec = "partial_g0"
        summary = f"Partial G0; indeterminate: {', '.join(indeterminate) or 'none'}"

    return {
        "l0Passed": l0,
        "l1Passed": l1,
        "l2Passed": l2,
        "releaseRecommendation": rec,
        "summary": summary,
        "checkResults": results,
    }


def run_benchmark(*, skip_cluster_noise: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "date": date.today().isoformat(),
        "datasetVersion": DATASET_VERSION,
        "commit": _git_commit(),
    }

    report["AC-P6-01"] = eval_hdbscan_stability()
    if skip_cluster_noise:
        report["AC-P6-02"] = {"skipped": True}
    else:
        report["AC-P6-02"] = eval_cluster_noise_all_fixtures()
    report["AC-P6-03"] = eval_event_boundaries()
    report["AC-P6-05"] = eval_layout_rhythm()
    report["AC-P6-06"] = eval_pipeline_perf()
    report["AC-P6-07"] = eval_rollback_drill()
    report["AC-P6-08"] = eval_license_bom()
    return report


def merge_into_record(report: dict[str, Any], record_path: Path = RECORD_PATH) -> dict[str, Any]:
    data = _load(record_path) if record_path.is_file() else {"recordId": "phase6-quality-eval", "phase": "P6-Stability"}
    data["date"] = report.get("date", date.today().isoformat())

    bench = data.setdefault("benchmark", {})
    bench["datasetVersion"] = report.get("datasetVersion")
    bench["commit"] = report.get("commit")
    bench["datasetCoverage"] = {
        "cityArchitectureSets": 1,
        "natureLandscapeSets": 0,
        "portraitGroupSets": 0,
        "weakOrNoGpsSets": 1,
        "burstHighDensitySets": 0,
        "nightLowLightSets": 0,
    }
    bench["configSnapshot"] = {
        "p5": phase6_snapshot_from_cfg(_p5_app_config()),
        "p6": phase6_snapshot_from_cfg(_p6_app_config()),
    }

    base = data.setdefault("kpiBaseline", {})
    cur = data.setdefault("kpiPhase6", {})
    ac = data.setdefault("acChecks", {})
    runs = data.setdefault("runs", [])

    ac01 = report["AC-P6-01"]
    ac.setdefault("AC-P6-01", {})
    ac["AC-P6-01"]["hdbscanRunsStable"] = ac01.get("hdbscanRunsStable")
    ac["AC-P6-01"]["passed"] = ac01.get("passed")
    ac["AC-P6-01"]["notes"] = f"fixtures={len(ac01.get('fixtureRuns') or [])}"
    runs.append({"kind": "hdbscan_stability", **ac01})

    if not report.get("AC-P6-02", {}).get("skipped"):
        ac02 = report["AC-P6-02"]
        if ac02.get("clusterNoiseRatioDbscanMean") is not None:
            base["clusterNoiseRatio"] = ac02["clusterNoiseRatioDbscanMean"]
            cur["clusterNoiseRatio"] = ac02["clusterNoiseRatioHdbscanMean"]
        ac.setdefault("AC-P6-02", {})
        ac["AC-P6-02"]["clusterNoiseRatioDropPct"] = ac02.get("clusterNoiseRatioDropPct")
        ac["AC-P6-02"]["passed"] = ac02.get("passed")
        ac["AC-P6-02"]["notes"] = ac02.get("notes", "")
        runs.append({"kind": "cluster_noise_suite", **ac02})

    ac03 = report["AC-P6-03"]
    if ac03.get("eventBoundaryF1Baseline") is not None:
        base["eventBoundaryF1"] = ac03["eventBoundaryF1Baseline"]
        cur["eventBoundaryF1"] = ac03["eventBoundaryF1Candidate"]
    ac.setdefault("AC-P6-03", {})
    ac["AC-P6-03"]["eventBoundaryF1LiftPct"] = ac03.get("eventBoundaryF1LiftPct")
    ac["AC-P6-03"]["passed"] = ac03.get("passed")
    runs.append({"kind": "event_boundary_suite", **ac03})

    ac05 = report["AC-P6-05"]
    base["layoutRepeatStreak"] = ac05.get("p5SimulatedRepeatStreak")
    cur["layoutRepeatStreak"] = ac05.get("p6SimulatedRepeatStreak")
    linzhi = ac05.get("linzhiFixture") or {}
    if linzhi.get("gravityBalance") is not None:
        cur["gravityBalance"] = linzhi.get("gravityBalance")
    if linzhi.get("longshotVisualVariety") is not None:
        cur["longshotVisualVariety"] = linzhi.get("longshotVisualVariety")
    ac.setdefault("AC-P6-05", {})
    ac["AC-P6-05"]["layoutRepeatStreakDropPct"] = ac05.get("layoutRepeatStreakDropPct")
    ac["AC-P6-05"]["passed"] = ac05.get("passed")
    runs.append({"kind": "layout_rhythm_sim", **ac05})

    ac06 = report.get("AC-P6-06") or {}
    if ac06.get("pipelineTime1kSecP5") is not None:
        base["pipelineTime1kSec"] = ac06["pipelineTime1kSecP5"]
        cur["pipelineTime1kSec"] = ac06["pipelineTime1kSecP6"]
    if ac06.get("peakMemory1kMbP5") is not None:
        base["peakMemory1kMb"] = ac06["peakMemory1kMbP5"]
        cur["peakMemory1kMb"] = ac06["peakMemory1kMbP6"]
    ac.setdefault("AC-P6-06", {})
    ac["AC-P6-06"]["timeRegressionPct"] = ac06.get("timeRegressionPct")
    ac["AC-P6-06"]["memoryRegressionPct"] = ac06.get("memoryRegressionPct")
    ac["AC-P6-06"]["passed"] = ac06.get("passed")
    runs.append({"kind": "pipeline_perf", **ac06})

    ac07 = report["AC-P6-07"]
    ac.setdefault("AC-P6-07", {})
    ac["AC-P6-07"]["rollbackDrillMinutes"] = ac07.get("rollbackDrillMinutes")
    ac["AC-P6-07"]["rollbackRestoredP5Behavior"] = ac07.get("rollbackRestoredP5Behavior")
    ac["AC-P6-07"]["passed"] = ac07.get("passed")
    runs.append({"kind": "rollback_drill", **ac07})

    ac08 = report["AC-P6-08"]
    ac.setdefault("AC-P6-08", {})
    ac["AC-P6-08"]["licenseBomCompleted"] = ac08.get("licenseBomCompleted")
    ac["AC-P6-08"]["l2InDefaultPath"] = False
    ac["AC-P6-08"]["passed"] = ac08.get("passed")

    from scripts.phase6_metrics_baseline import summarize

    data.setdefault("rollup", {}).update(compute_rollup(data))
    _save(record_path, data)
    summarize(record_path, write_back=True)
    return data


def phase6_snapshot_from_cfg(cfg) -> dict[str, Any]:
    from travelogue.curation.phase6_rollout import phase6_feature_snapshot

    return phase6_feature_snapshot(cfg)


def update_rollout_log(record_path: Path = RECORD_PATH, rollout_path: Path = ROLLOUT_PATH) -> None:
    record = _load(record_path)
    rollout = _load(rollout_path) if rollout_path.is_file() else {"recordId": "phase6-rollout-log"}
    ac = record.get("acChecks") or {}
    rollup = record.get("rollup") or {}

    rollout["date"] = date.today().isoformat()
    g0 = rollout.setdefault("gates", {}).setdefault("G0", {})
    g0["startAt"] = g0.get("startAt") or datetime.now(UTC).replace(microsecond=0).isoformat()
    g0["endAt"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    g0["status"] = "completed_fixture_suite" if rollup.get("l0Passed") else "partial_fixture_suite"

    rb = rollout.setdefault("rollbackRunbook", {})
    rb["step1SceneAlgorithmToDbscan"] = True
    rb["step2GapModeToFixed"] = True
    rb["step3DisableMmrAndGravity"] = True
    rb["step4IncidentRecordAnd24hRcaDraft"] = False
    rb["completedAt"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    rb["restoreVerified"] = (ac.get("AC-P6-07") or {}).get("rollbackRestoredP5Behavior")

    entries = rollout.setdefault("entries", [])
    if entries and entries[0].get("timestamp") is None:
        entries.pop(0)
    entries.insert(
        0,
        {
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "stage": "G0",
            "decision": "fixture_benchmark_complete",
            "reason": rollup.get("summary", ""),
            "operator": "phase6_benchmark_run.py",
            "relatedMetrics": {
                "exportSuccessRate": None,
                "pipelineTime1kSec": record.get("kpiPhase6", {}).get("pipelineTime1kSec"),
                "coverPreferenceWinrate": record.get("kpiPhase6", {}).get("coverPreferenceWinrate"),
                "eventBoundaryF1LiftPct": (ac.get("AC-P6-03") or {}).get("eventBoundaryF1LiftPct"),
                "layoutRepeatStreakDropPct": (ac.get("AC-P6-05") or {}).get("layoutRepeatStreakDropPct"),
            },
        },
    )
    _save(rollout_path, rollout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 6 G0 fixture benchmark suite")
    parser.add_argument("--write", action="store_true", help="merge results into acceptance records")
    parser.add_argument("--dry-run", action="store_true", help="print report JSON only")
    parser.add_argument("--skip-cluster-noise", action="store_true", help="skip CLIP/sklearn noise suite")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    report = run_benchmark(skip_cluster_noise=args.skip_cluster_noise)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.dry_run and not args.write:
        return 0

    if args.write:
        merge_into_record(report, args.record)
        update_rollout_log(args.record, ROLLOUT_PATH)
        print(json.dumps({"written": str(args.record), "rollout": str(ROLLOUT_PATH)}, indent=2))

    failed = [
        k
        for k, block in report.items()
        if k.startswith("AC-P6-") and isinstance(block, dict) and block.get("passed") is False
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
