"""Advance Phase 6 rollout gate (G0 → G1 → G2 → G3).

Usage:
  python scripts/phase6_rollout_advance.py --prepare-g1 --write
  python scripts/phase6_rollout_advance.py --start-g1 --apply-config --write
  python scripts/phase6_rollout_advance.py --prepare-g2 --write
  python scripts/phase6_rollout_advance.py --start-g2 --apply-config --write
  python scripts/phase6_rollout_advance.py --prepare-g3 --write
  python scripts/phase6_rollout_advance.py --start-g3 --apply-config --write
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUALITY_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
ROLLOUT_PATH = ROOT / "docs" / "acceptance-records" / "phase6-rollout-log.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ac_passed(quality: dict, ac_id: str) -> bool | None:
    return (quality.get("acChecks") or {}).get(ac_id, {}).get("passed")


def _br_improvement_count(quality: dict) -> int:
    base = quality.get("kpiBaseline") or {}
    p6 = quality.get("kpiPhase6") or {}
    count = 0
    pairs = (
        ("clusterNoiseRatio", "lower"),
        ("layoutRepeatStreak", "lower"),
        ("pipelineTime1kSec", "lower"),
        ("peakMemory1kMb", "lower"),
        ("eventBoundaryF1", "higher"),
        ("coverPreferenceWinrate", "higher"),
    )
    for key, direction in pairs:
        b = base.get(key)
        v = p6.get(key)
        if b is None or v is None:
            continue
        if direction == "lower" and v < b:
            count += 1
        elif direction == "higher" and v > b:
            count += 1
    return count


def _art_ac_pass_count(quality: dict) -> tuple[int, str]:
    art = quality.get("artChecks")
    if isinstance(art, dict):
        checks = art.get("checks")
        if isinstance(checks, dict) and checks:
            return sum(1 for v in checks.values() if v), "artChecks"
        if art.get("passCount") is not None:
            return int(art["passCount"]), "artChecks.passCount"
    proxy = 0
    if _ac_passed(quality, "AC-P6-05"):
        proxy += 1
    if _ac_passed(quality, "AC-P6-04"):
        proxy += 1
    if float((quality.get("kpiPhase6") or {}).get("gravityBalance") or 0) >= 0.85:
        proxy += 1
    return proxy, "fixture_proxy"


def _alerts_clear(rollout: dict) -> bool:
    alerts = rollout.get("alerts") or {}
    return not any(
        bool(alerts.get(key))
        for key in (
            "exportSuccessRateBelow97For24h",
            "pipelineTime1kRegressionAbove15PctFor2d",
            "coverBlindReviewBelowP5Baseline",
        )
    )


def _g3_stability_ok(rollout: dict, quality: dict, *, stable_days: int | None) -> tuple[bool, str, int | None]:
    if not _alerts_clear(rollout):
        return False, "alerts_breached", stable_days

    obs = rollout.setdefault("g2Observation", {})
    if stable_days is not None:
        obs["stableDays"] = stable_days
        return stable_days >= 7, f"stableDays={stable_days}", stable_days

    recorded = obs.get("stableDays")
    if recorded is not None:
        days = int(recorded)
        return days >= 7, f"stableDays={days}", days

    rollup = quality.get("rollup") or {}
    alert_checks = rollup.get("alertChecks") or {}
    fixture_ok = (
        rollup.get("l0Passed") is True
        and not alert_checks.get("pipelineTimeBreached")
        and not alert_checks.get("coverWinrateBreached")
    )
    return fixture_ok, "fixture_proxy_7d_pending", None


def prepare_g1(rollout: dict, quality: dict) -> dict:
    g0_required = ("AC-P6-01", "AC-P6-02", "AC-P6-03", "AC-P6-05", "AC-P6-06", "AC-P6-07", "AC-P6-08")
    g0_ok = all(_ac_passed(quality, ac) is True for ac in g0_required)
    ac04 = _ac_passed(quality, "AC-P6-04")

    g0 = rollout.setdefault("gates", {}).setdefault("G0", {})
    if g0_ok and ac04 is True:
        g0["status"] = "passed"
    elif g0_ok:
        g0["status"] = "passed_automated_pending_blind_review"
    else:
        g0["status"] = "blocked"
    if not g0.get("endAt"):
        g0["endAt"] = _now()

    g1 = rollout.setdefault("gates", {}).setdefault("G1", {})
    if g0_ok and ac04 is not False:
        g1["startAt"] = g1.get("startAt") or _now()
        g1["status"] = "ready_for_10pct"
    else:
        g1["status"] = "blocked"

    entry = {
        "timestamp": _now(),
        "stage": "G1-prep",
        "decision": g1["status"],
        "reason": (quality.get("rollup") or {}).get("summary", ""),
        "operator": "phase6_rollout_advance.py",
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": (quality.get("kpiPhase6") or {}).get("pipelineTime1kSec"),
            "coverPreferenceWinrate": (quality.get("kpiPhase6") or {}).get("coverPreferenceWinrate"),
            "g0AutomatedPassed": g0_ok,
            "acP604Passed": ac04,
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def prepare_g2(rollout: dict, quality: dict) -> dict:
    g1 = rollout.setdefault("gates", {}).setdefault("G1", {})
    g1_status = g1.get("status")
    br_count = _br_improvement_count(quality)
    art_count, art_source = _art_ac_pass_count(quality)
    g1_ok = g1_status in ("active_10pct", "passed")
    metrics_ok = br_count >= 2 and art_count >= 3

    g2 = rollout.setdefault("gates", {}).setdefault("G2", {})
    if g1_ok and metrics_ok:
        g2["startAt"] = g2.get("startAt") or _now()
        g2["status"] = "ready_for_50pct"
        decision = "ready_for_50pct"
        reason = f"G1 active; BR improvements={br_count}; ART-AC={art_count}/5 ({art_source})."
    else:
        g2["status"] = "blocked"
        decision = "blocked"
        reason = (
            f"G1 status={g1_status!r}; BR improvements={br_count}/2; ART-AC={art_count}/5 ({art_source})."
        )

    kpi = quality.get("kpiPhase6") or {}
    entry = {
        "timestamp": _now(),
        "stage": "G2-prep",
        "decision": decision,
        "reason": reason,
        "operator": "phase6_rollout_advance.py",
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": kpi.get("pipelineTime1kSec"),
            "coverPreferenceWinrate": kpi.get("coverPreferenceWinrate"),
            "brImprovementCount": br_count,
            "artAcPassCount": art_count,
            "artAcSource": art_source,
            "g1Status": g1_status,
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def prepare_g3(rollout: dict, quality: dict, *, stable_days: int | None = None) -> dict:
    g2 = rollout.setdefault("gates", {}).setdefault("G2", {})
    g2_status = g2.get("status")
    g2_ok = g2_status in ("active_50pct", "passed")
    stable_ok, stable_source, recorded_days = _g3_stability_ok(rollout, quality, stable_days=stable_days)
    br_count = _br_improvement_count(quality)
    art_count, art_source = _art_ac_pass_count(quality)

    g3 = rollout.setdefault("gates", {}).setdefault("G3", {})
    if g2_ok and stable_ok and br_count >= 2 and art_count >= 3:
        g3["startAt"] = g3.get("startAt") or _now()
        g3["status"] = "ready_for_full"
        decision = "ready_for_full"
        reason = (
            f"G2 active; stability={stable_source}; BR improvements={br_count}; "
            f"ART-AC={art_count}/5 ({art_source})."
        )
    else:
        g3["status"] = "blocked"
        decision = "blocked"
        reason = (
            f"G2 status={g2_status!r}; stability={stable_source}; stableOk={stable_ok}; "
            f"BR={br_count}/2; ART-AC={art_count}/5."
        )

    kpi = quality.get("kpiPhase6") or {}
    entry = {
        "timestamp": _now(),
        "stage": "G3-prep",
        "decision": decision,
        "reason": reason,
        "operator": "phase6_rollout_advance.py",
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": kpi.get("pipelineTime1kSec"),
            "coverPreferenceWinrate": kpi.get("coverPreferenceWinrate"),
            "brImprovementCount": br_count,
            "artAcPassCount": art_count,
            "artAcSource": art_source,
            "g2Status": g2_status,
            "stableDays": recorded_days,
            "stabilitySource": stable_source,
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def start_g3(
    rollout: dict,
    quality: dict,
    *,
    operator: str = "phase6_rollout_advance.py",
    traffic_percent: float = 100.0,
    cohort_salt: str = "p6-g1-2026-05",
) -> dict:
    g3 = rollout.setdefault("gates", {}).setdefault("G3", {})
    status = g3.get("status")
    if status not in ("ready_for_full", "active_full"):
        raise ValueError(f"G3 not ready to start (status={status!r})")

    g2 = rollout.setdefault("gates", {}).setdefault("G2", {})
    if g2.get("status") == "active_50pct":
        g2["status"] = "passed"
        g2["endAt"] = g2.get("endAt") or _now()

    g3["startAt"] = g3.get("startAt") or _now()
    g3["status"] = "active_full"

    kpi = quality.get("kpiPhase6") or {}
    br_count = _br_improvement_count(quality)
    art_count, art_source = _art_ac_pass_count(quality)
    entry = {
        "timestamp": _now(),
        "stage": "G3",
        "decision": "active_full",
        "reason": "G3 full rollout started; all trips receive Phase 6 behavior.",
        "operator": operator,
        "config": {
            "trafficPercent": traffic_percent,
            "cohortSalt": cohort_salt,
        },
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": kpi.get("pipelineTime1kSec"),
            "coverPreferenceWinrate": kpi.get("coverPreferenceWinrate"),
            "brImprovementCount": br_count,
            "artAcPassCount": art_count,
            "artAcSource": art_source,
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def start_g2(
    rollout: dict,
    quality: dict,
    *,
    operator: str = "phase6_rollout_advance.py",
    traffic_percent: float = 50.0,
    cohort_salt: str = "p6-g1-2026-05",
) -> dict:
    g2 = rollout.setdefault("gates", {}).setdefault("G2", {})
    status = g2.get("status")
    if status not in ("ready_for_50pct", "active_50pct"):
        raise ValueError(f"G2 not ready to start (status={status!r})")

    g1 = rollout.setdefault("gates", {}).setdefault("G1", {})
    if g1.get("status") == "active_10pct":
        g1["status"] = "passed"
        g1["endAt"] = g1.get("endAt") or _now()

    g2["startAt"] = g2.get("startAt") or _now()
    g2["status"] = "active_50pct"

    kpi = quality.get("kpiPhase6") or {}
    br_count = _br_improvement_count(quality)
    art_count, art_source = _art_ac_pass_count(quality)
    entry = {
        "timestamp": _now(),
        "stage": "G2",
        "decision": "active_50pct",
        "reason": "G2 50% rollout started; cohort expanded with same cohortSalt.",
        "operator": operator,
        "config": {
            "trafficPercent": traffic_percent,
            "cohortSalt": cohort_salt,
        },
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": kpi.get("pipelineTime1kSec"),
            "coverPreferenceWinrate": kpi.get("coverPreferenceWinrate"),
            "brImprovementCount": br_count,
            "artAcPassCount": art_count,
            "artAcSource": art_source,
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def start_g1(
    rollout: dict,
    quality: dict,
    *,
    operator: str = "phase6_rollout_advance.py",
    traffic_percent: float = 10.0,
    cohort_salt: str = "p6-g1-2026-05",
) -> dict:
    g1 = rollout.setdefault("gates", {}).setdefault("G1", {})
    status = g1.get("status")
    if status not in ("ready_for_10pct", "active_10pct"):
        raise ValueError(f"G1 not ready to start (status={status!r})")

    g1["startAt"] = g1.get("startAt") or _now()
    g1["status"] = "active_10pct"

    kpi = quality.get("kpiPhase6") or {}
    entry = {
        "timestamp": _now(),
        "stage": "G1",
        "decision": "active_10pct",
        "reason": "G1 10% rollout started; trip cohort via phase6.rollout bucketing.",
        "operator": operator,
        "config": {
            "trafficPercent": traffic_percent,
            "cohortSalt": cohort_salt,
        },
        "relatedMetrics": {
            "exportSuccessRate": None,
            "pipelineTime1kSec": kpi.get("pipelineTime1kSec"),
            "coverPreferenceWinrate": kpi.get("coverPreferenceWinrate"),
            "g0AutomatedPassed": True,
            "acP604Passed": _ac_passed(quality, "AC-P6-04"),
        },
    }
    entries = rollout.setdefault("entries", [])
    entries.insert(0, entry)
    rollout["date"] = datetime.now(timezone.utc).date().isoformat()
    return rollout


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance Phase 6 rollout gates")
    parser.add_argument("--prepare-g1", action="store_true")
    parser.add_argument("--start-g1", action="store_true")
    parser.add_argument("--prepare-g2", action="store_true")
    parser.add_argument("--start-g2", action="store_true")
    parser.add_argument("--prepare-g3", action="store_true")
    parser.add_argument("--start-g3", action="store_true")
    parser.add_argument("--stable-days", type=int, default=None, help="with --prepare-g3, record G2 stable observation days")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--apply-config", action="store_true", help="with --start-g*, merge rollout patch into config.yaml")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--traffic-percent", type=float, default=None)
    parser.add_argument("--cohort-salt", default="p6-g1-2026-05")
    parser.add_argument("--quality", type=Path, default=QUALITY_PATH)
    parser.add_argument("--rollout", type=Path, default=ROLLOUT_PATH)
    args = parser.parse_args()

    actions = sum(
        1
        for flag in (
            args.prepare_g1,
            args.start_g1,
            args.prepare_g2,
            args.start_g2,
            args.prepare_g3,
            args.start_g3,
        )
        if flag
    )
    if actions != 1:
        parser.error(
            "exactly one of --prepare-g1, --start-g1, --prepare-g2, --start-g2, "
            "--prepare-g3, --start-g3 is required"
        )

    if not args.quality.is_file():
        print(f"quality record missing: {args.quality}", file=sys.stderr)
        return 2

    quality = _load(args.quality)
    rollout = _load(args.rollout) if args.rollout.is_file() else {"recordId": "phase6-rollout-log"}

    if args.prepare_g1:
        updated = prepare_g1(rollout, quality)
        summary = {
            "g0Status": updated["gates"]["G0"]["status"],
            "g1Status": updated["gates"]["G1"]["status"],
        }
    elif args.prepare_g2:
        updated = prepare_g2(rollout, quality)
        summary = {
            "g1Status": updated["gates"]["G1"]["status"],
            "g2Status": updated["gates"]["G2"]["status"],
        }
    elif args.prepare_g3:
        updated = prepare_g3(rollout, quality, stable_days=args.stable_days)
        summary = {
            "g2Status": updated["gates"]["G2"]["status"],
            "g3Status": updated["gates"]["G3"]["status"],
        }
    elif args.start_g1:
        traffic = 10.0 if args.traffic_percent is None else args.traffic_percent
        try:
            updated = start_g1(
                rollout,
                quality,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        summary = {"g1Status": updated["gates"]["G1"]["status"], "decision": "active_10pct"}
        if args.apply_config:
            sys.path.insert(0, str(ROOT))
            from travelogue.curation.phase6_rollout import apply_g1_rollout_config

            cfg_path = apply_g1_rollout_config(
                args.config,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
            summary["configApplied"] = str(cfg_path)
    elif args.start_g2:
        traffic = 50.0 if args.traffic_percent is None else args.traffic_percent
        try:
            updated = start_g2(
                rollout,
                quality,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        summary = {"g2Status": updated["gates"]["G2"]["status"], "decision": "active_50pct"}
        if args.apply_config:
            sys.path.insert(0, str(ROOT))
            from travelogue.curation.phase6_rollout import apply_g2_rollout_config

            cfg_path = apply_g2_rollout_config(
                args.config,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
            summary["configApplied"] = str(cfg_path)
    else:
        traffic = 100.0 if args.traffic_percent is None else args.traffic_percent
        try:
            updated = start_g3(
                rollout,
                quality,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        summary = {"g3Status": updated["gates"]["G3"]["status"], "decision": "active_full"}
        if args.apply_config:
            sys.path.insert(0, str(ROOT))
            from travelogue.curation.phase6_rollout import apply_g3_rollout_config

            cfg_path = apply_g3_rollout_config(
                args.config,
                traffic_percent=traffic,
                cohort_salt=args.cohort_salt,
            )
            summary["configApplied"] = str(cfg_path)

    print(json.dumps(summary, indent=2))

    if args.write:
        _save(args.rollout, updated)
        print(json.dumps({"written": str(args.rollout)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
