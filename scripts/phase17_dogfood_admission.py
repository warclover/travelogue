"""Phase 17 dogfood admission · shadow metrics + rollout-log update.

Usage:
  python scripts/phase17_dogfood_admission.py
  python scripts/phase17_dogfood_admission.py --fixture golden-mixed-scenes --append-rollout
  python scripts/phase17_dogfood_admission.py --fixture golden-p17-mixed-person --append-rollout --strict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from scripts.phase17_golden_metrics import (
    AC_SPECS,
    _cfg_lse_enabled,
    _cfg_with_capabilities,
)
from travelogue.layout_engine.golden_probe import merge_gates, run_ac_probe
from travelogue.layout_engine.metrics import (
    assets_map_from_trip,
    compute_layout_golden_metrics,
    curate_trip_chapters,
    evaluate_ac_delta,
)
from travelogue.layout_engine.sandbox import cfg_lse_sandbox_pair, sandbox_replay_trip

ROLLOUT_PATH = ROOT / "docs" / "acceptance-records" / "p17-rollout-log.json"
DEFAULT_DOGFOOD_FIXTURES = (
    "golden-mixed-scenes",
    "golden-p17-mixed-person",
)
CAPABILITY_AC_IDS = ("AC-P17-16", "AC-P17-17", "AC-P17-18")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _load_trip(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _capability_probe_results(
    trip: dict,
    ac_eval: dict[str, Any],
) -> tuple[dict[str, bool | None], dict[str, dict[str, Any]]]:
    base_cfg = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    gates: dict[str, bool | None] = {}
    probes: dict[str, dict[str, Any]] = {}
    for ac_id in CAPABILITY_AC_IDS:
        base_caps, cand_caps = AC_SPECS[ac_id]
        baseline_cfg = _cfg_with_capabilities(base_cfg, **base_caps)
        candidate_cfg = _cfg_with_capabilities(base_cfg, **cand_caps)
        curate_gate = ac_eval.get(ac_id) or {}
        probe = run_ac_probe(
            trip,
            ac_id,
            baseline_cfg=baseline_cfg,
            candidate_cfg=candidate_cfg,
        )
        probes[ac_id] = probe
        merged = merge_gates(curate_gate, probe)
        gates[ac_id] = merged.get("passed")
    return gates, probes


def _face_delta_pp_from_probes(
    curate_delta: float | None,
    probes: dict[str, dict[str, Any]],
) -> float | None:
    if curate_delta is not None and curate_delta > 0:
        return curate_delta
    probe16 = probes.get("AC-P17-16") or {}
    lift = probe16.get("rankingLiftPp")
    if lift is None:
        lift = probe16.get("salientDeltaPp")
    if lift is not None and float(lift) > 0:
        return float(lift)
    return curate_delta


def observe_trip(
    trip: dict,
    *,
    trip_id: str,
    work_dir: Path,
) -> dict[str, Any]:
    base_cfg = _cfg_for_mode("p3_full")
    baseline_cfg, candidate_cfg = cfg_lse_sandbox_pair(base_cfg)
    assets = assets_map_from_trip(trip)

    report = sandbox_replay_trip(
        trip,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        work_dir=work_dir / "sandbox",
    )
    base_chapters = curate_trip_chapters(
        trip, work_dir=work_dir / "baseline", cfg=baseline_cfg
    )
    cand_chapters = curate_trip_chapters(
        trip, work_dir=work_dir / "candidate", cfg=candidate_cfg
    )
    base_metrics = compute_layout_golden_metrics(base_chapters, assets)
    cand_metrics = compute_layout_golden_metrics(cand_chapters, assets)
    ac_eval = evaluate_ac_delta(base_metrics, cand_metrics)
    dogfood = ac_eval.get("dogfood") or {}
    capability_gates, probes = _capability_probe_results(trip, ac_eval)
    face_delta_pp = _face_delta_pp_from_probes(
        dogfood.get("face_intact_delta_pp"),
        probes,
    )

    return {
        "tripId": trip_id,
        "observedAt": _now(),
        "diffRate": report.get("diffRate"),
        "changedCount": (report.get("diff") or {}).get("changedCount"),
        "baselineMetrics": base_metrics,
        "candidateMetrics": cand_metrics,
        "faceIntactBaseline": base_metrics.get("layout.mixed.face_intact_rate"),
        "faceIntactCandidate": cand_metrics.get("layout.mixed.face_intact_rate"),
        "faceIntactDeltaPp": face_delta_pp,
        "capabilityProbes": {
            ac_id: {
                "passed": (probes.get(ac_id) or {}).get("passed"),
                "measurable": (probes.get(ac_id) or {}).get("measurable"),
            }
            for ac_id in CAPABILITY_AC_IDS
        },
        "patternDiversityP50Baseline": dogfood.get("pattern_diversity_p50_baseline"),
        "patternDiversityP50Candidate": dogfood.get("pattern_diversity_p50_candidate"),
        "patternDiversityOk": dogfood.get("pattern_diversity_ok"),
        "gates": capability_gates,
    }


def collect_trip_dirs(trips_dir: Path) -> list[Path]:
    if not trips_dir.is_dir():
        return []
    return sorted(p for p in trips_dir.glob("*/trip.json") if p.is_file())


def aggregate_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    face_deltas = [
        o["faceIntactDeltaPp"]
        for o in observations
        if o.get("faceIntactDeltaPp") is not None
    ]
    diversity_ok = [o.get("patternDiversityOk") for o in observations if "patternDiversityOk" in o]
    diff_rates = [o.get("diffRate") for o in observations if o.get("diffRate") is not None]
    ac_gate_summary: dict[str, bool | None] = {}
    for ac_id in CAPABILITY_AC_IDS:
        vals = [(o.get("gates") or {}).get(ac_id) for o in observations]
        vals = [v for v in vals if v is not None]
        if vals:
            ac_gate_summary[ac_id] = all(vals)
        else:
            ac_gate_summary[ac_id] = None
    return {
        "tripCount": len(observations),
        "faceIntactDeltaPpMedian": (
            round(sorted(face_deltas)[len(face_deltas) // 2], 2) if face_deltas else None
        ),
        "patternDiversityOkRate": (
            round(sum(1 for x in diversity_ok if x) / len(diversity_ok), 4)
            if diversity_ok
            else None
        ),
        "diffRateMedian": (
            round(sorted(diff_rates)[len(diff_rates) // 2], 4) if diff_rates else None
        ),
        "capabilityGates": ac_gate_summary,
    }


def append_rollout_log(
    observations: list[dict[str, Any]],
    *,
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    if ROLLOUT_PATH.is_file():
        rollout = json.loads(ROLLOUT_PATH.read_text(encoding="utf-8"))
    else:
        rollout = {"schemaVersion": "1", "observations": [], "gates": {}}

    entry = {
        "recordedAt": _now(),
        "commit": _git_commit(),
        "aggregate": aggregate,
        "trips": observations,
    }
    rollout.setdefault("observations", []).append(entry)
    if not rollout.get("startedAt"):
        rollout["startedAt"] = _now()

    for ac_id in CAPABILITY_AC_IDS:
        passed = (aggregate.get("capabilityGates") or {}).get(ac_id)
        if passed is not None:
            rollout.setdefault("gates", {}).setdefault(ac_id, {"passed": None})
            rollout["gates"][ac_id]["passed"] = passed

    face_med = aggregate.get("faceIntactDeltaPpMedian")
    diversity_ok = aggregate.get("patternDiversityOkRate")
    cap_gates = aggregate.get("capabilityGates") or {}
    caps_ok = all(v is not False for v in cap_gates.values() if v is not None)
    if caps_ok and (diversity_ok is None or diversity_ok >= 1.0):
        if face_med is None or face_med >= 3.0:
            rollout.setdefault("gates", {}).setdefault(
                "dogfood_admission",
                {"label": "shadow capability+diversity", "passed": None},
            )
            rollout["gates"]["dogfood_admission"]["passed"] = True

    ROLLOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROLLOUT_PATH.write_text(json.dumps(rollout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rollout


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 dogfood admission observer")
    parser.add_argument("--trips-dir", type=Path, help="Directory of trip folders with assets")
    parser.add_argument("--fixture", action="append", help="Fixture trip id (repeatable)")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "p17-dogfood")
    parser.add_argument("--append-rollout", action="store_true", help="Append to p17-rollout-log.json")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when dogfood gates fail")
    args = parser.parse_args()

    fixture_ids = list(args.fixture or [])
    if not fixture_ids and not args.trips_dir:
        fixture_ids = list(DEFAULT_DOGFOOD_FIXTURES)

    observations: list[dict[str, Any]] = []
    args.work_dir.mkdir(parents=True, exist_ok=True)

    for fid in fixture_ids:
        trip = load_fixture_trip(fid)
        observations.append(
            observe_trip(trip, trip_id=fid, work_dir=args.work_dir / fid)
        )

    if args.trips_dir:
        for trip_json in collect_trip_dirs(args.trips_dir):
            trip = _load_trip(trip_json)
            if not trip or not (trip.get("assets") or []):
                continue
            tid = str(trip.get("tripId") or trip_json.parent.name)
            observations.append(
                observe_trip(trip, trip_id=tid, work_dir=args.work_dir / tid)
            )

    if not observations:
        print(json.dumps({"error": "no trips observed"}, ensure_ascii=False, indent=2))
        return 1

    aggregate = aggregate_observations(observations)
    payload = {
        "emittedAt": _now(),
        "commit": _git_commit(),
        "aggregate": aggregate,
        "observations": observations,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.append_rollout:
        append_rollout_log(observations, aggregate=aggregate)

    if args.strict:
        for ac_id in CAPABILITY_AC_IDS:
            passed = (aggregate.get("capabilityGates") or {}).get(ac_id)
            if passed is False:
                return 1
        face_med = aggregate.get("faceIntactDeltaPpMedian")
        if face_med is not None and face_med < 3.0:
            return 1
        div_rate = aggregate.get("patternDiversityOkRate")
        if div_rate is not None and div_rate < 1.0:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
