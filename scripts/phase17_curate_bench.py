"""Phase 17 curate performance bench · AC-P17-28 (LSE ≤ +15% vs P16 baseline).

Usage:
  python scripts/phase17_curate_bench.py
  python scripts/phase17_curate_bench.py --fixture golden-mixed-scenes --check
  python scripts/phase17_curate_bench.py --write
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "p17-curate-perf.json"
SPIKE_PATH = ROOT / "docs" / "acceptance-records" / "p17-perf-spike.json"
PERF_BUDGET_PCT = 15.0


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


def delta_pct(baseline_ms: float, candidate_ms: float) -> float | None:
    if baseline_ms <= 0:
        return None
    return round((candidate_ms - baseline_ms) / baseline_ms * 100.0, 2)


def within_budget(baseline_ms: float, candidate_ms: float, budget_pct: float = PERF_BUDGET_PCT) -> bool:
    pct = delta_pct(baseline_ms, candidate_ms)
    return pct is not None and pct <= budget_pct


def _prepare_trip(trip: dict) -> dict:
    body = deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    body.setdefault("curation", {}).pop("clustering", None)
    for asset in body.get("assets") or []:
        asset.pop("sceneClusterId", None)
        asset.pop("clusterSource", None)
    return body


def _run_curate_once(trip: dict, *, work_dir: Path, cfg: Any) -> float:
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    body = _prepare_trip(trip)
    t0 = time.perf_counter()
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    return time.perf_counter() - t0


def bench_curate_pair(
    trip: dict,
    *,
    work_dir: Path,
    baseline_cfg: Any,
    candidate_cfg: Any,
    repeats: int = 2,
) -> dict[str, Any]:
    base_times: list[float] = []
    cand_times: list[float] = []
    for i in range(max(1, repeats)):
        base_times.append(
            _run_curate_once(
                trip,
                work_dir=work_dir / f"baseline-{i}",
                cfg=baseline_cfg,
            )
        )
        cand_times.append(
            _run_curate_once(
                trip,
                work_dir=work_dir / f"candidate-{i}",
                cfg=candidate_cfg,
            )
        )
    baseline_s = min(base_times)
    candidate_s = min(cand_times)
    baseline_ms = round(baseline_s * 1000, 1)
    candidate_ms = round(candidate_s * 1000, 1)
    pct = delta_pct(baseline_ms, candidate_ms)
    return {
        "baselineMs": baseline_ms,
        "candidateMs": candidate_ms,
        "deltaPct": pct,
        "budgetPct": PERF_BUDGET_PCT,
        "withinBudget": within_budget(baseline_ms, candidate_ms),
        "repeats": repeats,
    }


def run_fixture_bench(
    fixture_id: str,
    *,
    work_dir: Path,
    repeats: int = 2,
) -> dict[str, Any]:
    from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
    from travelogue.layout_engine.sandbox import cfg_lse_sandbox_pair

    trip = load_fixture_trip(fixture_id)
    base_cfg = _cfg_for_mode("p3_full")
    baseline_cfg, candidate_cfg = cfg_lse_sandbox_pair(base_cfg)
    timing = bench_curate_pair(
        trip,
        work_dir=work_dir,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        repeats=repeats,
    )
    return {"fixtureId": fixture_id, **timing}


def build_record(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": "1",
        "benchmarkId": "p17-curate-perf-v1",
        "emittedAt": _now(),
        "commit": _git_commit(),
        "budgetPct": PERF_BUDGET_PCT,
        "ac_p17": {
            "AC-P17-28": all(r.get("withinBudget") for r in results),
        },
        "results": results,
        "notes": "LSE off vs on · min-of-repeats curate+cluster wall time",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 curate performance bench")
    parser.add_argument(
        "--fixture",
        action="append",
        default=["golden-mixed-scenes"],
        help="Fixture trip id (repeatable)",
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "p17-curate-bench")
    parser.add_argument("--write", action="store_true", help="Write acceptance record JSON")
    parser.add_argument("--check", action="store_true", help="Exit 1 when over +15%% budget")
    args = parser.parse_args()

    args.work_dir.mkdir(parents=True, exist_ok=True)
    results = [
        run_fixture_bench(fid, work_dir=args.work_dir / fid, repeats=args.repeats)
        for fid in args.fixture
    ]
    record = build_record(results)
    print(json.dumps(record, ensure_ascii=False, indent=2))

    if args.write:
        RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        RECORD_PATH.write_text(blob, encoding="utf-8")
        SPIKE_PATH.write_text(blob, encoding="utf-8")

    if args.check and not record["ac_p17"]["AC-P17-28"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
