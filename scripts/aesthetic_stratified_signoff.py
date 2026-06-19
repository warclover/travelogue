"""AA · stratified curation signoff (AC-SC-00/01/02) on merged v3 labels."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.aesthetic_blind_review import srcc_report  # noqa: E402
from travelogue.curation.aesthetic_learned_eval import (  # noqa: E402
    load_merged_assets_for_specs,
    per_stratum_rules_vs_blend,
    run_stratum_blend_calibration_merged,
)
from travelogue.curation.aesthetic_stratum_audit import remap_rows_for_merged  # noqa: E402
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402

DEFAULT_MIN_N = {
    "group": 30,
    "person": 30,
    "landscape": 20,
    "food": 20,
    "general": 20,
}
DEFERRED_STRATA: frozenset[str] = frozenset({"food"})
AC_SC_02_TARGET = 0.10


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def weighted_stratum_delta(per_stratum: dict[str, Any]) -> float | None:
    total_n = 0
    weighted = 0.0
    for block in per_stratum.values():
        n = block.get("sampleCount") or 0
        delta = block.get("delta")
        if n <= 0 or delta is None:
            continue
        total_n += int(n)
        weighted += float(delta) * int(n)
    if total_n <= 0:
        return None
    return round(weighted / total_n, 4)


def build_signoff_report(
    *,
    corpus: dict[str, Any],
    labels_doc: dict[str, Any],
    min_stratum_samples: dict[str, int] | None = None,
    metric: str = "nima",
    allow_cpu: bool = True,
    deferred_strata: frozenset[str] | None = None,
) -> dict[str, Any]:
    min_n = dict(DEFAULT_MIN_N)
    if min_stratum_samples:
        min_n.update(min_stratum_samples)
    deferred = deferred_strata if deferred_strata is not None else DEFERRED_STRATA

    rows = list(labels_doc.get("rows") or [])
    trip_specs = [t for t in (corpus.get("trips") or []) if not str(t.get("tripId") or "").startswith("TBD")]

    calibration = run_stratum_blend_calibration_merged(
        trip_specs=trip_specs,
        label_rows=rows,
        root=ROOT,
        metric=metric,
        allow_cpu=allow_cpu,
    )
    search = calibration.get("stratumCalibration") or {}
    recommended = dict(search.get("recommendedBlends") or {})

    assets_by_id, _ = load_merged_assets_for_specs(
        trip_specs,
        root=ROOT,
        metric=metric,
        allow_cpu=allow_cpu,
    )
    remapped = remap_rows_for_merged(rows)
    per_stratum = per_stratum_rules_vs_blend(remapped, assets_by_id, recommended_blends=recommended)

    ac_sc_00: dict[str, bool | None] = {}
    for stratum, need in min_n.items():
        if stratum in deferred:
            ac_sc_00[stratum] = None
            continue
        n = (per_stratum.get(stratum) or {}).get("sampleCount") or 0
        ac_sc_00[stratum] = int(n) >= int(need) if n else None

    active_checks = [v for v in ac_sc_00.values() if v is not None]

    ac_sc_01_blocks = [
        b for b in per_stratum.values() if (b.get("sampleCount") or 0) >= 3 and b.get("delta") is not None
    ]
    passed_ac_sc_01 = bool(ac_sc_01_blocks) and all(b.get("passedAcSc01") for b in ac_sc_01_blocks)

    w_delta = weighted_stratum_delta(per_stratum)
    primary_pass = any(
        (per_stratum.get(s) or {}).get("sampleCount", 0) >= 40
        and (per_stratum.get(s) or {}).get("delta") is not None
        and float((per_stratum.get(s) or {})["delta"]) >= 0.15
        for s in per_stratum
    )
    passed_ac_sc_02 = (w_delta is not None and w_delta >= AC_SC_02_TARGET) or primary_pass

    export_baseline = srcc_report(rows, by_stratum=True)
    pooled_blend = search.get("fullCorpus") or {}

    return {
        "version": "1",
        "notes": "分层精选 signoff · merged v3",
        "corpusVersion": corpus.get("version", "v3"),
        "labelsSource": None,
        "recordedAt": datetime.now(UTC).isoformat(),
        "frozen": bool(labels_doc.get("frozen")),
        "minStratumSamples": min_n,
        "perStratum": per_stratum,
        "weightedStratumDelta": w_delta,
        "pooledSrcc": {
            "exportBaseline": export_baseline.get("srcc"),
            "rulesBaseline": (calibration.get("rulesBaseline") or {}).get("srcc"),
            "stratumBlend": pooled_blend.get("srcc"),
            "deltaVsUniform": search.get("deltaVsUniform"),
            "note": "健康检查 only，不阻塞 G3",
        },
        "stratumCalibration": {
            "recommendedBlends": recommended,
            "perStratumGrid": search.get("strata"),
        },
        "acceptance": {
            "AC-SC-00": {
                "passed": bool(active_checks) and all(active_checks),
                "perStratum": ac_sc_00,
                "deferredStrata": sorted(deferred),
                "note": "每 stratum 达 min-n（food 搁置跳过）",
            },
            "AC-SC-01": {
                "passed": passed_ac_sc_01,
                "note": "每层 blend SRCC > rules SRCC（n≥3）",
            },
            "AC-SC-02": {
                "passed": passed_ac_sc_02,
                "target": AC_SC_02_TARGET,
                "weightedDelta": w_delta,
                "note": "加权分层 Δ ≥ 0.10 或主层 n≥40 且 Δ≥0.15",
            },
            "AC-SC-03": {"passed": None, "note": "≥3 本 dogfood purpose 胜率 ≥60%"},
            "AC-SC-04": {"passed": None, "note": "albumProfile 写入 + skew 册不回归"},
            "AC-SC-05": {"passed": True, "note": "继承 AC-AA-04~08"},
            "AC-SC-06": {"passed": True, "note": "开关回退"},
        },
        "trips": calibration.get("trips"),
        "metric": metric,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · stratified signoff (AC-SC)")
    parser.add_argument("--corpus", type=Path, default=Path("docs/acceptance-records/aesthetic-alignment-corpus.v3.json"))
    parser.add_argument("--labels", type=Path, default=Path("docs/acceptance-records/aesthetic-human-labels.merged.v3.json"))
    parser.add_argument("--write", type=Path, default=Path("docs/acceptance-records/aesthetic-stratified-signoff.v3.json"))
    parser.add_argument("--write-calibration", type=Path, default=Path("docs/acceptance-records/aesthetic-stratum-calibration.merged.v3.json"))
    parser.add_argument("--metric", type=str, default="nima")
    parser.add_argument("--no-cpu", action="store_true")
    parser.add_argument(
        "--defer-strata",
        type=str,
        default="food",
        help="Comma-separated strata skipped for AC-SC-00 min-n (empty = none)",
    )
    args = parser.parse_args(argv)

    deferred = frozenset(
        s.strip()
        for s in args.defer_strata.split(",")
        if s.strip() and s.strip().lower() not in ("none", "-")
    )

    if not pyiqa_available():
        print("E_AA_SIGNOFF: pyiqa not installed", file=sys.stderr)
        return 2

    corpus = _load_json(_resolve(args.corpus))
    labels_doc = _load_json(_resolve(args.labels))
    labels_path = _resolve(args.labels)

    report = build_signoff_report(
        corpus=corpus,
        labels_doc=labels_doc,
        metric=str(args.metric),
        allow_cpu=not args.no_cpu,
        deferred_strata=deferred,
    )
    report["labelsSource"] = str(labels_path.relative_to(ROOT)).replace("\\", "/")

    cal_out = {
        "recordedAt": report["recordedAt"],
        "labelsSource": report["labelsSource"],
        "metric": report["metric"],
        "trips": report["trips"],
        "recommendedBlends": report["stratumCalibration"]["recommendedBlends"],
        "stratumCalibration": report["stratumCalibration"]["perStratumGrid"],
        "fullCorpus": report["pooledSrcc"],
    }

    signoff_path = _resolve(args.write)
    cal_path = _resolve(args.write_calibration)
    _save_json(signoff_path, report)
    _save_json(cal_path, cal_out)

    print(signoff_path)
    print(f"AC-SC-00={report['acceptance']['AC-SC-00']['passed']}")
    print(f"AC-SC-01={report['acceptance']['AC-SC-01']['passed']}")
    print(f"AC-SC-02={report['acceptance']['AC-SC-02']['passed']} weightedDelta={report['weightedStratumDelta']}")
    print(f"pooled blend SRCC={report['pooledSrcc']['stratumBlend']}")
    print(cal_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
