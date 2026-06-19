"""AA · multi-trip pooled SRCC eval (labels keyed by tripId + assetId)."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import (  # noqa: E402
    DEFAULT_STRATUM_BLENDS,
    AestheticConfig,
    resolve_learned_blend,  # noqa: E402
)
from travelogue.curation.aesthetic_blind_review import srcc_report  # noqa: E402
from travelogue.curation.aesthetic_learned_eval import (  # noqa: E402
    _read_learned_aesthetic_score,
    blended_score,
    ensure_learned_scores,
    rules_for_purpose,
)
from travelogue.curation.aesthetic_score import purpose_overall  # noqa: E402
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _blends_from_calibration(path: Path | None) -> dict[str, float]:
    blends = dict(DEFAULT_STRATUM_BLENDS)
    if path is None or not path.is_file():
        return blends
    raw = _load_json(path)
    rec = (raw.get("stratumCalibration") or {}).get("recommendedBlends") or raw.get("recommendedBlends")
    if isinstance(rec, dict):
        blends.update({str(k): float(v) for k, v in rec.items()})
    return blends


def load_trip_assets(trip_dir: Path) -> dict[str, dict]:
    trip = _load_json(trip_dir / "trip.json")
    return {str(a["id"]): copy.deepcopy(a) for a in (trip.get("assets") or []) if a.get("id")}


def run_merged_eval(
    *,
    trip_specs: list[dict[str, Any]],
    label_rows: list[dict[str, Any]],
    metric: str = "nima",
    allow_cpu: bool = True,
    portrait_lite: bool = True,
) -> dict[str, Any]:
    """Pooled SRCC across trips; each spec: tripDir, stratumCalibration (optional)."""
    assets_by_trip: dict[str, dict[str, dict]] = {}
    blends_by_trip: dict[str, dict[str, float]] = {}
    scored_flags: dict[str, bool] = {}

    for spec in trip_specs:
        trip_id = str(spec["tripId"])
        trip_dir = _resolve(Path(spec["tripDir"]))
        assets_by_trip[trip_id] = load_trip_assets(trip_dir)
        cal_path = spec.get("stratumCalibration")
        blends_by_trip[trip_id] = _blends_from_calibration(
            _resolve(Path(cal_path)) if cal_path else None
        )
        scored_flags[trip_id] = ensure_learned_scores(
            list(assets_by_trip[trip_id].values()),
            trip_dir=trip_dir,
            metric=metric,
            allow_cpu=allow_cpu,
        )
        if portrait_lite:
            from travelogue.curation.aesthetic_score import refresh_portrait_lite_overall

            cfg_pl = AestheticConfig(ml_calibrate=True, portrait_lite_enabled=True)
            for asset in assets_by_trip[trip_id].values():
                refresh_portrait_lite_overall(asset, cfg=cfg_pl)

    def _asset_for_row(row: dict[str, Any]) -> dict | None:
        trip_id = str(row.get("tripId") or "")
        aid = str(row.get("assetId") or "")
        pool = assets_by_trip.get(trip_id) or {}
        return pool.get(aid)

    def _cfg_for_row(row: dict[str, Any]) -> AestheticConfig:
        trip_id = str(row.get("tripId") or "")
        blends = blends_by_trip.get(trip_id) or dict(DEFAULT_STRATUM_BLENDS)
        return AestheticConfig(
            ml_calibrate=True,
            use_stratum_blend=True,
            stratum_blends=blends,
            portrait_lite_enabled=portrait_lite,
            source="rules+ml",
        )

    rules_cfg = AestheticConfig(ml_calibrate=False, use_purpose_presets=True)

    def predict_rules(asset: dict, row: dict) -> float | None:
        del row
        return rules_for_purpose(asset, "default", cfg=rules_cfg)

    def predict_stratum_blend(asset: dict, row: dict) -> float | None:
        cfg = _cfg_for_row(row)
        rules = rules_for_purpose(asset, "default", cfg=cfg)
        learned = _read_learned_aesthetic_score(asset)
        blend = resolve_learned_blend(asset, cfg)
        return blended_score(rules, learned, blend)

    def predict_cover(asset: dict, row: dict) -> float | None:
        return purpose_overall(asset, "cover", cfg=_cfg_for_row(row))

    def pooled_srcc(predict_fn) -> dict[str, Any]:
        prepared: list[dict[str, Any]] = []
        for row in label_rows:
            if row.get("humanScore") is None:
                continue
            asset = _asset_for_row(row)
            if asset is None:
                continue
            try:
                from travelogue.curation.aesthetic_blind_review import normalize_human_score

                hs = normalize_human_score(row["humanScore"])
                pred = predict_fn(asset, row)
            except (TypeError, ValueError):
                continue
            if pred is None:
                continue
            prepared.append({**row, "humanScore": hs, "predictedOverall": float(pred)})
        from travelogue.curation.pa_acceptance import srcc_from_label_rows

        rep = srcc_from_label_rows(prepared)
        return {"sampleCount": rep["sampleCount"], "srcc": rep["srcc"]}

    rules_rep = pooled_srcc(predict_rules)
    blend_rep = pooled_srcc(predict_stratum_blend)
    cover_rep = pooled_srcc(predict_cover)

    baseline_export = srcc_report(label_rows, by_stratum=True)

    per_trip: dict[str, Any] = {}
    for trip_id in assets_by_trip:
        sub = [r for r in label_rows if str(r.get("tripId") or "") == trip_id and r.get("humanScore") is not None]

        def pooled_trip(fn):
            prepared = []
            for row in sub:
                asset = assets_by_trip[trip_id].get(str(row.get("assetId") or ""))
                if not asset:
                    continue
                try:
                    from travelogue.curation.aesthetic_blind_review import normalize_human_score

                    hs = normalize_human_score(row["humanScore"])
                    pred = fn(asset, row)
                except (TypeError, ValueError):
                    continue
                if pred is None:
                    continue
                prepared.append({"humanScore": hs, "predictedOverall": float(pred)})
            from travelogue.curation.pa_acceptance import srcc_from_label_rows

            rep = srcc_from_label_rows(prepared)
            return {"sampleCount": rep["sampleCount"], "srcc": rep["srcc"]}

        per_trip[trip_id] = {
            "labeled": len(sub),
            "learnedScored": scored_flags.get(trip_id),
            "stratumBlends": blends_by_trip.get(trip_id),
            "rulesSrcc": pooled_trip(predict_rules).get("srcc"),
            "stratumBlendSrcc": pooled_trip(predict_stratum_blend).get("srcc"),
        }

    rules_srcc = rules_rep.get("srcc")
    blend_srcc = blend_rep.get("srcc")
    baseline_srcc = baseline_export.get("srcc")

    return {
        "metric": metric,
        "portraitLite": portrait_lite,
        "sampleCount": blend_rep.get("sampleCount"),
        "exportBaseline": {
            "srcc": baseline_srcc,
            "sampleCount": baseline_export.get("sampleCount"),
        },
        "rulesRecomputed": rules_rep,
        "stratumBlend": blend_rep,
        "coverPurpose": cover_rep,
        "deltaVsExportBaseline": (
            None
            if baseline_srcc is None or blend_srcc is None
            else round(float(blend_srcc) - float(baseline_srcc), 4)
        ),
        "deltaVsRules": (
            None
            if rules_srcc is None or blend_srcc is None
            else round(float(blend_srcc) - float(rules_srcc), 4)
        ),
        "acAa02": {
            "targetDelta": 0.15,
            "targetAbsolute": 0.6,
            "deltaFromBaseline": (
                None
                if baseline_srcc is None or blend_srcc is None
                else round(float(blend_srcc) - float(baseline_srcc), 4)
            ),
            "passedDelta": (
                baseline_srcc is not None
                and blend_srcc is not None
                and float(blend_srcc) - float(baseline_srcc) >= 0.15
            ),
            "passedAbsolute": blend_srcc is not None and float(blend_srcc) >= 0.6,
            "passed": (
                (blend_srcc is not None and float(blend_srcc) >= 0.6)
                or (
                    baseline_srcc is not None
                    and blend_srcc is not None
                    and float(blend_srcc) - float(baseline_srcc) >= 0.15
                )
            ),
        },
        "perTrip": per_trip,
        "trips": trip_specs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · merged multi-trip SRCC eval")
    parser.add_argument("--corpus", type=Path, required=True, help="aesthetic-alignment-corpus.v2.json")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--metric", type=str, default="nima")
    parser.add_argument("--no-cpu", action="store_true")
    parser.add_argument("--no-portrait-lite", action="store_true")
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args(argv)

    if not pyiqa_available():
        print('E_AA_MERGED: pyiqa not installed', file=sys.stderr)
        return 2

    corpus = _load_json(_resolve(args.corpus))
    labels_raw = _load_json(_resolve(args.labels))
    rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])

    trip_specs: list[dict[str, Any]] = []
    for trip in corpus.get("trips") or []:
        spec: dict[str, Any] = {
            "tripId": trip["tripId"],
            "tripDir": trip["tripDir"],
        }
        cal = trip.get("stratumCalibration")
        if cal:
            spec["stratumCalibration"] = cal
        trip_specs.append(spec)

    out = run_merged_eval(
        trip_specs=trip_specs,
        label_rows=rows,
        metric=str(args.metric),
        allow_cpu=not args.no_cpu,
        portrait_lite=not args.no_portrait_lite,
    )

    print("=== Merged pooled SRCC ===")
    print(f"n={out['sampleCount']} export baseline={out['exportBaseline']['srcc']}")
    print(f"rules={out['rulesRecomputed']['srcc']} stratum_blend={out['stratumBlend']['srcc']}")
    print(f"delta vs baseline={out['deltaVsExportBaseline']} AC-AA-02 passed={out['acAa02']['passed']}")
    for tid, block in (out.get("perTrip") or {}).items():
        print(f"  [{tid}] rules={block['rulesSrcc']} blend={block['stratumBlendSrcc']} n={block['labeled']}")

    if args.write:
        path = _resolve(args.write)
        _save_json(path, out)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
