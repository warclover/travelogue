"""Phase 7 equivalence gate checker (NR-P7 / AC-P7-04/06/09/11).

Usage:
  python scripts/phase7_equivalence_check.py
  python scripts/phase7_equivalence_check.py --write
  python scripts/phase7_equivalence_check.py --write --strict
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase7-perf-eval.json"
PHASE6_RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _float_or_none(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _bool_or_none(v: Any) -> bool | None:
    if v is None:
        return None
    return bool(v)


def _apply_cli_overrides(record: dict[str, Any], args: argparse.Namespace) -> None:
    nr = record.setdefault("nr_p7", {})
    qg = record.setdefault("qualityGuard", {})

    pairs = [
        ("curate_hash_rate_fixed", args.nr_fixed_curate),
        ("cluster_hash_rate_fixed", args.nr_fixed_cluster),
        ("curate_hash_rate_real", args.nr_real_curate),
        ("cluster_hash_rate_real", args.nr_real_cluster),
        ("subject_class_agreement", args.subject_class_agreement),
    ]
    for key, val in pairs:
        if val is not None:
            nr[key] = val

    q_pairs = [
        ("cluster_noise_ratio_p7", args.cluster_noise_p7),
        ("event_boundary_f1_p7", args.event_boundary_f1_p7),
        ("layout_repeat_streak_p7", args.layout_repeat_streak_p7),
    ]
    for key, val in q_pairs:
        if val is not None:
            qg[key] = val


def _fill_quality_baseline_from_phase6(record: dict[str, Any], phase6: dict[str, Any]) -> None:
    qg = record.setdefault("qualityGuard", {})
    kpi = phase6.get("kpiPhase6") or {}
    if qg.get("cluster_noise_ratio_p6") is None and kpi.get("clusterNoiseRatio") is not None:
        qg["cluster_noise_ratio_p6"] = kpi.get("clusterNoiseRatio")
    if qg.get("event_boundary_f1_p6") is None and kpi.get("eventBoundaryF1") is not None:
        qg["event_boundary_f1_p6"] = kpi.get("eventBoundaryF1")
    if qg.get("layout_repeat_streak_p6") is None and kpi.get("layoutRepeatStreak") is not None:
        qg["layout_repeat_streak_p6"] = kpi.get("layoutRepeatStreak")


def _compute_nr_and_ac(record: dict[str, Any]) -> dict[str, Any]:
    nr = record.setdefault("nr_p7", {})
    ac = record.setdefault("ac_p7", {})
    qg = record.setdefault("qualityGuard", {})
    cand = record.setdefault("candidate", {})

    f_cur = _float_or_none(nr.get("curate_hash_rate_fixed"))
    f_clu = _float_or_none(nr.get("cluster_hash_rate_fixed"))
    r_cur = _float_or_none(nr.get("curate_hash_rate_real"))
    r_clu = _float_or_none(nr.get("cluster_hash_rate_real"))
    subj = _float_or_none(nr.get("subject_class_agreement"))

    fixed_ok = None if (f_cur is None or f_clu is None) else (abs(f_cur - 1.0) < 1e-12 and abs(f_clu - 1.0) < 1e-12)
    real_ok = None if (r_cur is None or r_clu is None) else (r_cur >= 0.95 and r_clu >= 0.95)
    subj_ok = None if subj is None else abs(subj - 1.0) < 1e-12

    ac04 = None
    if fixed_ok is not None and real_ok is not None and subj_ok is not None:
        ac04 = fixed_ok and real_ok and subj_ok
    ac["AC-P7-04"] = _bool_or_none(ac04)

    ac06 = None
    if fixed_ok is not None and real_ok is not None:
        ac06 = fixed_ok and real_ok
    ac["AC-P7-06"] = _bool_or_none(ac06)

    # AC-P7-09 quality guards
    c_p6 = _float_or_none(qg.get("cluster_noise_ratio_p6"))
    c_p7 = _float_or_none(qg.get("cluster_noise_ratio_p7"))
    e_p6 = _float_or_none(qg.get("event_boundary_f1_p6"))
    e_p7 = _float_or_none(qg.get("event_boundary_f1_p7"))
    l_p6 = _float_or_none(qg.get("layout_repeat_streak_p6"))
    l_p7 = _float_or_none(qg.get("layout_repeat_streak_p7"))
    q_ok = None
    if None not in (c_p6, c_p7, e_p6, e_p7, l_p6, l_p7):
        q_ok = c_p7 <= c_p6 + 0.02 and e_p7 >= e_p6 and l_p7 <= l_p6
    ac["AC-P7-09"] = _bool_or_none(q_ok)

    # AC-P7-11 (cache ABI mismatch triggers rebuild + NR passes)
    cache_rebuild = _float_or_none(cand.get("cache_rebuild_success_rate"))
    ac11 = None
    if cache_rebuild is not None and ac04 is not None:
        ac11 = cache_rebuild >= 1.0 and bool(ac04)
    ac["AC-P7-11"] = _bool_or_none(ac11)

    nr_passed = None
    if ac04 is not None and ac06 is not None:
        nr_passed = ac04 and ac06
    nr["passed"] = _bool_or_none(nr_passed)
    nr["checkedAt"] = _now()

    return {
        "fixedOk": fixed_ok,
        "realOk": real_ok,
        "subjectOk": subj_ok,
        "qualityGuardOk": q_ok,
        "cacheRebuildSuccessRate": cache_rebuild,
        "ac_p7": ac,
        "nr_p7": nr,
    }


def _missing_for_gate(record: dict[str, Any]) -> list[str]:
    nr = record.get("nr_p7") or {}
    qg = record.get("qualityGuard") or {}
    needed = {
        "nr_p7.curate_hash_rate_fixed": nr.get("curate_hash_rate_fixed"),
        "nr_p7.cluster_hash_rate_fixed": nr.get("cluster_hash_rate_fixed"),
        "nr_p7.curate_hash_rate_real": nr.get("curate_hash_rate_real"),
        "nr_p7.cluster_hash_rate_real": nr.get("cluster_hash_rate_real"),
        "nr_p7.subject_class_agreement": nr.get("subject_class_agreement"),
        "qualityGuard.cluster_noise_ratio_p6": qg.get("cluster_noise_ratio_p6"),
        "qualityGuard.cluster_noise_ratio_p7": qg.get("cluster_noise_ratio_p7"),
        "qualityGuard.event_boundary_f1_p6": qg.get("event_boundary_f1_p6"),
        "qualityGuard.event_boundary_f1_p7": qg.get("event_boundary_f1_p7"),
        "qualityGuard.layout_repeat_streak_p6": qg.get("layout_repeat_streak_p6"),
        "qualityGuard.layout_repeat_streak_p7": qg.get("layout_repeat_streak_p7"),
        "candidate.cache_rebuild_success_rate": (record.get("candidate") or {}).get("cache_rebuild_success_rate"),
    }
    return [k for k, v in needed.items() if v is None]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 NR-P7 equivalence gate checker")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true", help="fail when required fields are missing")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--phase6-record", type=Path, default=PHASE6_RECORD_PATH)
    parser.add_argument("--fill-baseline-from-phase6", action="store_true", default=True)
    parser.add_argument("--nr-fixed-curate", type=float, default=None)
    parser.add_argument("--nr-fixed-cluster", type=float, default=None)
    parser.add_argument("--nr-real-curate", type=float, default=None)
    parser.add_argument("--nr-real-cluster", type=float, default=None)
    parser.add_argument("--subject-class-agreement", type=float, default=None)
    parser.add_argument("--cluster-noise-p7", type=float, default=None)
    parser.add_argument("--event-boundary-f1-p7", type=float, default=None)
    parser.add_argument("--layout-repeat-streak-p7", type=float, default=None)
    args = parser.parse_args()

    rec_path = args.record.resolve()
    if not rec_path.is_file():
        print(json.dumps({"ok": False, "error": f"record not found: {rec_path}"}, ensure_ascii=False))
        return 2

    record = _load_json(rec_path)
    if args.fill_baseline_from_phase6 and args.phase6_record.is_file():
        phase6 = _load_json(args.phase6_record.resolve())
        _fill_quality_baseline_from_phase6(record, phase6)

    _apply_cli_overrides(record, args)
    summary = _compute_nr_and_ac(record)
    missing = _missing_for_gate(record)
    summary["missing"] = missing
    summary["record"] = str(rec_path)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.write:
        _save_json(rec_path, record)
        print(json.dumps({"written": str(rec_path)}, indent=2, ensure_ascii=False))

    if args.strict and missing:
        return 2

    failed = [
        key
        for key in ("AC-P7-04", "AC-P7-06", "AC-P7-09", "AC-P7-11")
        if (record.get("ac_p7") or {}).get(key) is False
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

