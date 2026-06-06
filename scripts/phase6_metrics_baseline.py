"""Phase 6 metrics summary and AC threshold checks.

Usage:
  python scripts/phase6_metrics_baseline.py --summary
  python scripts/phase6_metrics_baseline.py --summary --write
  python scripts/phase6_metrics_baseline.py --fixture-noise --write
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
FIXTURE_MANIFEST = ROOT / "tests" / "fixtures" / "clustering" / "golden-mixed-scenes" / "assets-manifest.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pct_drop(base: float | None, cur: float | None) -> float | None:
    if base is None or cur is None or base == 0:
        return None
    return (base - cur) / base * 100.0


def _pct_lift(base: float | None, cur: float | None) -> float | None:
    if base is None or cur is None or base == 0:
        return None
    return (cur - base) / base * 100.0


def _lt(a: float | None, b: float) -> bool | None:
    if a is None:
        return None
    return a < b


def _gte(a: float | None, b: float) -> bool | None:
    if a is None:
        return None
    return a >= b


def _thresholds():
    from travelogue.config import get_config

    cfg = get_config()
    return cfg.phase6.ac, cfg.phase6.alerts


def compute_fixture_cluster_noise(manifest: Path = FIXTURE_MANIFEST) -> dict[str, float]:
    """Compare DBSCAN (P5) vs HDBSCAN (P6) noise ratio on CI golden fixture."""
    pytest = __import__("pytest")
    sklearn = pytest.importorskip("sklearn")

    del sklearn  # only used for importorskip side effect

    payload = _load_json(manifest)
    assets = payload.get("assets") or []
    from travelogue.curation.scene_clusters import _cluster_labels, cluster_noise_ratio
    from travelogue.vision.clip_encoder import ClipEncoder

    enc = ClipEncoder()
    embed = enc.embed_assets(assets)
    import numpy as np

    mat = np.asarray(embed.vectors, dtype=np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    mat = mat / norms

    db_labels, _, _ = _cluster_labels(mat, algorithm="dbscan", eps=0.08, min_samples_eff=3)
    hdb_labels, _, _ = _cluster_labels(mat, algorithm="hdbscan", eps=0.08, min_samples_eff=3)
    return {
        "fixture": manifest.parent.name,
        "assetCount": len(embed.asset_ids),
        "clusterNoiseRatioDbscan": round(cluster_noise_ratio(embed.asset_ids, db_labels), 4),
        "clusterNoiseRatioHdbscan": round(cluster_noise_ratio(embed.asset_ids, hdb_labels), 4),
    }


def summarize(path: Path, write_back: bool) -> int:
    data = _load_json(path)
    base = data.get("kpiBaseline") or {}
    cur = data.get("kpiPhase6") or {}
    ac_cfg, alert_cfg = _thresholds()
    ac = data.setdefault("acChecks", {})

    noise_drop = _pct_drop(base.get("clusterNoiseRatio"), cur.get("clusterNoiseRatio"))
    f1_lift = _pct_lift(base.get("eventBoundaryF1"), cur.get("eventBoundaryF1"))
    repeat_drop = _pct_drop(base.get("layoutRepeatStreak"), cur.get("layoutRepeatStreak"))
    time_reg = _pct_lift(base.get("pipelineTime1kSec"), cur.get("pipelineTime1kSec"))
    mem_reg = _pct_lift(base.get("peakMemory1kMb"), cur.get("peakMemory1kMb"))

    ac.setdefault("AC-P6-02", {})["clusterNoiseRatioDropPct"] = noise_drop
    ac["AC-P6-02"]["passed"] = _gte(noise_drop, ac_cfg.cluster_noise_ratio_drop_pct)

    ac.setdefault("AC-P6-03", {})["eventBoundaryF1LiftPct"] = f1_lift
    ac["AC-P6-03"]["passed"] = _gte(f1_lift, ac_cfg.event_boundary_f1_lift_pct)

    ac.setdefault("AC-P6-05", {})["layoutRepeatStreakDropPct"] = repeat_drop
    ac["AC-P6-05"]["passed"] = _gte(repeat_drop, ac_cfg.layout_repeat_streak_drop_pct)

    ac.setdefault("AC-P6-06", {})["timeRegressionPct"] = time_reg
    ac["AC-P6-06"]["memoryRegressionPct"] = mem_reg
    ac["AC-P6-06"]["passed"] = (
        _lt(time_reg, ac_cfg.pipeline_time_regression_pct)
        and _lt(mem_reg, ac_cfg.peak_memory_regression_pct)
    )

    alerts = {
        "exportSuccessRateMin": alert_cfg.export_success_rate_min,
        "pipelineTimeRegressionAlertPct": alert_cfg.pipeline_time_regression_alert_pct,
        "coverPreferenceWinrateMin": alert_cfg.cover_preference_winrate_min,
        "pipelineTimeBreached": _gte(time_reg, alert_cfg.pipeline_time_regression_alert_pct),
        "coverWinrateBreached": (
            cur.get("coverPreferenceWinrate") is not None
            and cur.get("coverPreferenceWinrate") < alert_cfg.cover_preference_winrate_min
        ),
    }

    summary = {
        "clusterNoiseRatioDropPct": noise_drop,
        "eventBoundaryF1LiftPct": f1_lift,
        "layoutRepeatStreakDropPct": repeat_drop,
        "timeRegressionPct": time_reg,
        "memoryRegressionPct": mem_reg,
        "thresholds": {
            "ac": {
                "clusterNoiseRatioDropPct": ac_cfg.cluster_noise_ratio_drop_pct,
                "eventBoundaryF1LiftPct": ac_cfg.event_boundary_f1_lift_pct,
                "layoutRepeatStreakDropPct": ac_cfg.layout_repeat_streak_drop_pct,
                "pipelineTimeRegressionPct": ac_cfg.pipeline_time_regression_pct,
                "peakMemoryRegressionPct": ac_cfg.peak_memory_regression_pct,
            },
            "alerts": alerts,
        },
        "ac": {
            "AC-P6-02": ac["AC-P6-02"].get("passed"),
            "AC-P6-03": ac["AC-P6-03"].get("passed"),
            "AC-P6-05": ac["AC-P6-05"].get("passed"),
            "AC-P6-06": ac["AC-P6-06"].get("passed"),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if write_back:
        data.setdefault("rollup", {})["alertChecks"] = alerts
        _save_json(path, data)

    if all(v is True for v in summary["ac"].values()):
        return 0
    if any(v is False for v in summary["ac"].values()):
        return 1
    return 0


def write_fixture_noise(path: Path, manifest: Path) -> int:
    stats = compute_fixture_cluster_noise(manifest)
    data = _load_json(path) if path.is_file() else {"recordId": "phase6-quality-eval"}
    data.setdefault("kpiBaseline", {})["clusterNoiseRatio"] = stats["clusterNoiseRatioDbscan"]
    data.setdefault("kpiPhase6", {})["clusterNoiseRatio"] = stats["clusterNoiseRatioHdbscan"]
    data["date"] = date.today().isoformat()
    runs = data.setdefault("runs", [])
    runs.append({"kind": "fixture_cluster_noise", **stats})
    ac = data.setdefault("acChecks", {}).setdefault("AC-P6-02", {})
    drop = _pct_drop(stats["clusterNoiseRatioDbscan"], stats["clusterNoiseRatioHdbscan"])
    ac_cfg, _ = _thresholds()
    ac["clusterNoiseRatioDropPct"] = drop
    ac["passed"] = _gte(drop, ac_cfg.cluster_noise_ratio_drop_pct)
    ac.setdefault("notes", "")
    ac["notes"] = f"fixture={stats['fixture']} assets={stats['assetCount']}"
    _save_json(path, data)
    print(json.dumps({"written": str(path), **stats, "clusterNoiseRatioDropPct": drop}, indent=2))
    return summarize(path, write_back=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 metrics summary")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--fixture-noise", action="store_true")
    parser.add_argument("--fixture", type=Path, default=FIXTURE_MANIFEST)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.fixture_noise:
        return write_fixture_noise(args.record, args.fixture)
    if not args.summary:
        parser.error("--summary or --fixture-noise is required")
    try:
        return summarize(args.record, write_back=args.write)
    except FileNotFoundError as exc:
        print(f"record not found: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
