"""AA · M1 learned aesthetic evaluation vs human labels."""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from travelogue.config import AestheticConfig, AppConfig, DEFAULT_STRATUM_BLENDS, resolve_learned_blend
from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset
from travelogue.curation.aesthetic_score import (
    _read_learned_aesthetic_score,
    _rules_overall_from_dims,
    _rules_overall_from_weights,
    aesthetic_overall,
    apply_aesthetic_ml_calibration,
    asset_aesthetic,
    purpose_overall,
    refresh_portrait_lite_overall,
    resolve_aesthetic_weights,
)
from travelogue.curation.aesthetic_blind_review import normalize_human_score
from travelogue.curation.pa_acceptance import srcc_from_label_rows
from travelogue.curation.photo_cull_ml import apply_aesthetic_scores

AestheticPurposeGrid = Literal["default", "cover", "hero", "moment"]

_REQUIRED_DIMS = frozenset(
    {"composition", "exposure", "color", "lighting", "subjectClarity"}
)


def rules_only_overall(asset: dict, *, cfg: AestheticConfig | None = None) -> float | None:
    """Rules Layer-1 overall from existing dims (no ML blend)."""
    cfg = cfg or AestheticConfig()
    q = asset.get("quality")
    if not isinstance(q, dict):
        return None
    ae = q.get("aesthetic")
    if not isinstance(ae, dict):
        return None
    dims = ae.get("dims")
    if not isinstance(dims, dict) or not dims:
        return None
    return round(_rules_overall_from_dims(dims, cfg), 4)


def rules_for_purpose(
    asset: dict,
    purpose: AestheticPurposeGrid,
    *,
    cfg: AestheticConfig | None = None,
) -> float | None:
    """Rules-only overall for a purpose (no ML blend)."""
    cfg = cfg or AestheticConfig()
    if purpose == "default":
        return rules_only_overall(asset, cfg=cfg)
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    dims = ae.get("dims")
    if not isinstance(dims, dict) or not dims:
        return aesthetic_overall(asset)
    if not _REQUIRED_DIMS.issubset(dims.keys()):
        return aesthetic_overall(asset)
    weights = resolve_aesthetic_weights(cfg, purpose)
    return round(_rules_overall_from_weights(dims, weights), 4)


def blended_score(
    rules: float | None,
    learned: float | None,
    blend: float,
) -> float | None:
    if rules is None:
        return None
    if learned is None or blend <= 0.0:
        return round(float(rules), 4)
    b = min(1.0, max(0.0, float(blend)))
    if b >= 1.0:
        return round(float(learned), 4)
    return round((1.0 - b) * float(rules) + b * float(learned), 4)


def _blend_grid(min_b: float, max_b: float, step: float) -> list[float]:
    if step <= 0:
        raise ValueError("blend step must be > 0")
    out: list[float] = []
    v = float(min_b)
    max_b = float(max_b)
    while v <= max_b + 1e-9:
        out.append(round(v, 4))
        v += step
    if out and out[-1] < max_b:
        out.append(round(max_b, 4))
    return out


def _srcc_for_predictions(
    label_rows: list[dict[str, Any]],
    assets_by_id: dict[str, dict],
    *,
    predict_fn,
) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for row in label_rows:
        if row.get("humanScore") is None:
            continue
        aid = str(row.get("assetId") or "")
        asset = assets_by_id.get(aid)
        if not asset:
            continue
        try:
            hs = normalize_human_score(row["humanScore"])
            pred = predict_fn(asset, row)
        except (TypeError, ValueError):
            continue
        if pred is None:
            continue
        pairs.append({"humanScore": hs, "predictedOverall": float(pred)})
    rep = srcc_from_label_rows(pairs)
    return {"sampleCount": rep["sampleCount"], "srcc": rep["srcc"]}


def ensure_learned_scores(
    assets: list[dict],
    *,
    trip_dir: Path,
    metric: str,
    allow_cpu: bool = True,
) -> bool:
    """Run pyiqa once if learned scores missing; uses on-disk cache when warm."""
    from dataclasses import replace

    from travelogue.config import AppConfig

    missing = any(_read_learned_aesthetic_score(a) is None for a in assets)
    if not missing:
        return True
    app_cfg = AppConfig()
    cull_cfg = replace(
        app_cfg.cull,
        aesthetic_metric=metric,
        allow_cpu_ml=allow_cpu,
    )
    return apply_aesthetic_scores(assets, trip_dir=trip_dir, cfg=cull_cfg, force_ml=True)


def grid_search_blend(
    assets_by_id: dict[str, dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
    purposes: tuple[AestheticPurposeGrid, ...] = ("default", "cover", "hero", "moment"),
    blend_min: float = 0.0,
    blend_max: float = 1.0,
    blend_step: float = 0.05,
    baseline_rules_srcc: float | None = None,
) -> dict[str, Any]:
    """Grid-search ``ml_calibrate_blend``; learned scores must already be on assets."""
    cfg = cfg or AestheticConfig()
    grid = _blend_grid(blend_min, blend_max, blend_step)
    features: list[dict[str, Any]] = []
    for row in label_rows:
        aid = str(row.get("assetId") or "")
        asset = assets_by_id.get(aid)
        if not asset or row.get("humanScore") is None:
            continue
        learned = _read_learned_aesthetic_score(asset)
        rules_map = {p: rules_for_purpose(asset, p, cfg=cfg) for p in purposes}
        features.append(
            {
                "assetId": aid,
                "stratum": row.get("stratum"),
                "humanScore": row.get("humanScore"),
                "learnedOnly": learned,
                "rules": rules_map,
            }
        )

    learned_only = _srcc_for_predictions(
        label_rows,
        assets_by_id,
        predict_fn=lambda asset, _row: _read_learned_aesthetic_score(asset),
    )

    purpose_results: dict[str, Any] = {}
    for purpose in purposes:
        rows: list[dict[str, Any]] = []
        for blend in grid:
            rep = _srcc_for_predictions(
                label_rows,
                assets_by_id,
                predict_fn=lambda asset, row, p=purpose, b=blend: blended_score(
                    rules_for_purpose(asset, p, cfg=cfg),
                    _read_learned_aesthetic_score(asset),
                    b,
                ),
            )
            rows.append({"blend": blend, **rep})
        best = max(
            rows,
            key=lambda r: (-1.0 if r.get("srcc") is None else float(r["srcc"])),
        )
        purpose_results[purpose] = {
            "grid": rows,
            "bestBlend": best["blend"],
            "bestSrcc": best.get("srcc"),
            "baselineRulesSrcc": baseline_rules_srcc,
            "deltaVsBaseline": (
                None
                if baseline_rules_srcc is None or best.get("srcc") is None
                else round(float(best["srcc"]) - float(baseline_rules_srcc), 4)
            ),
        }

    default_best = purpose_results.get("default", {})
    return {
        "sampleCount": len(features),
        "blendGrid": grid,
        "learnedOnly": learned_only,
        "purposes": purpose_results,
        "recommended": {
            "blend": default_best.get("bestBlend"),
            "srcc": default_best.get("bestSrcc"),
            "purpose": "default",
        },
    }


def _row_stratum(row: dict[str, Any], assets_by_id: dict[str, dict]) -> str:
    raw = row.get("stratum")
    if raw:
        return str(raw)
    aid = str(row.get("assetId") or "")
    asset = assets_by_id.get(aid) or {}
    return review_stratum_for_asset(asset)


def grid_search_stratum_blend(
    assets_by_id: dict[str, dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
    blend_min: float = 0.0,
    blend_max: float = 0.6,
    blend_step: float = 0.05,
    min_samples: int = 3,
    baseline_rules_srcc: float | None = None,
) -> dict[str, Any]:
    """Per-stratum blend grid search; learned scores must already be on assets."""
    cfg = cfg or AestheticConfig()
    strata = sorted(
        {
            _row_stratum(row, assets_by_id)
            for row in label_rows
            if row.get("humanScore") is not None
        }
    )
    per_stratum: dict[str, Any] = {}
    merged_blends = dict(DEFAULT_STRATUM_BLENDS)
    merged_blends.update(dict(cfg.stratum_blends or {}))

    for stratum in strata:
        sub_rows = [
            row
            for row in label_rows
            if row.get("humanScore") is not None and _row_stratum(row, assets_by_id) == stratum
        ]
        if len(sub_rows) < min_samples:
            per_stratum[stratum] = {
                "sampleCount": len(sub_rows),
                "skipped": True,
                "reason": f"need>={min_samples} samples",
            }
            continue
        search = grid_search_blend(
            assets_by_id,
            sub_rows,
            cfg=cfg,
            purposes=("default",),
            blend_min=blend_min,
            blend_max=blend_max,
            blend_step=blend_step,
            baseline_rules_srcc=baseline_rules_srcc,
        )
        block = search["purposes"]["default"]
        best_blend = block.get("bestBlend")
        if best_blend is not None:
            merged_blends[stratum] = float(best_blend)
        per_stratum[stratum] = {
            "sampleCount": len(sub_rows),
            "skipped": False,
            "bestBlend": best_blend,
            "bestSrcc": block.get("bestSrcc"),
            "grid": block.get("grid"),
        }

    stratum_cfg = replace(
        cfg,
        ml_calibrate=True,
        use_stratum_blend=True,
        stratum_blends=merged_blends,
    )

    def _predict_stratum(asset: dict, _row: dict[str, Any]) -> float | None:
        rules = rules_for_purpose(asset, "default", cfg=stratum_cfg)
        learned = _read_learned_aesthetic_score(asset)
        blend = resolve_learned_blend(asset, stratum_cfg)
        return blended_score(rules, learned, blend)

    full = _srcc_for_predictions(label_rows, assets_by_id, predict_fn=_predict_stratum)
    uniform = _srcc_for_predictions(
        label_rows,
        assets_by_id,
        predict_fn=lambda asset, _row: blended_score(
            rules_for_purpose(asset, "default", cfg=cfg),
            _read_learned_aesthetic_score(asset),
            cfg.ml_calibrate_blend,
        ),
    )
    return {
        "strata": per_stratum,
        "recommendedBlends": merged_blends,
        "fullCorpus": full,
        "uniformBlend": uniform,
        "deltaVsUniform": (
            None
            if full.get("srcc") is None or uniform.get("srcc") is None
            else round(float(full["srcc"]) - float(uniform["srcc"]), 4)
        ),
        "baselineRulesSrcc": baseline_rules_srcc,
        "deltaVsBaseline": (
            None
            if baseline_rules_srcc is None or full.get("srcc") is None
            else round(float(full["srcc"]) - float(baseline_rules_srcc), 4)
        ),
    }


def run_stratum_blend_calibration(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    metric: str = "nima",
    allow_cpu: bool = True,
    blend_min: float = 0.0,
    blend_max: float = 0.6,
    blend_step: float = 0.05,
) -> dict[str, Any]:
    """M2 extension · per-stratum blend grid vs human labels."""
    import json

    trip_path = trip_dir / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assets = list(trip.get("assets") or [])
    assets_by_id = {str(a["id"]): copy.deepcopy(a) for a in assets if a.get("id")}

    scored = ensure_learned_scores(
        list(assets_by_id.values()),
        trip_dir=trip_dir,
        metric=metric,
        allow_cpu=allow_cpu,
    )

    cfg = AestheticConfig(use_purpose_presets=True, ml_calibrate=True)
    rules_baseline = _srcc_for_predictions(
        label_rows,
        assets_by_id,
        predict_fn=lambda asset, _row: rules_for_purpose(asset, "default", cfg=cfg),
    )
    search = grid_search_stratum_blend(
        assets_by_id,
        label_rows,
        cfg=cfg,
        blend_min=blend_min,
        blend_max=blend_max,
        blend_step=blend_step,
        baseline_rules_srcc=rules_baseline.get("srcc"),
    )
    return {
        "tripDir": str(trip_dir),
        "metric": metric,
        "scored": scored,
        "rulesBaseline": rules_baseline,
        "stratumCalibration": search,
    }


def run_blend_calibration(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    metric: str = "nima",
    allow_cpu: bool = True,
    blend_min: float = 0.0,
    blend_max: float = 0.6,
    blend_step: float = 0.05,
) -> dict[str, Any]:
    """M2 · score once, grid-search blend weights vs human labels."""
    import json

    trip_path = trip_dir / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assets = list(trip.get("assets") or [])
    assets_by_id = {str(a["id"]): copy.deepcopy(a) for a in assets if a.get("id")}

    scored = ensure_learned_scores(
        list(assets_by_id.values()),
        trip_dir=trip_dir,
        metric=metric,
        allow_cpu=allow_cpu,
    )

    cfg = AestheticConfig(use_purpose_presets=True)
    rules_baseline = _srcc_for_predictions(
        label_rows,
        assets_by_id,
        predict_fn=lambda asset, _row: rules_for_purpose(asset, "default", cfg=cfg),
    )
    search = grid_search_blend(
        assets_by_id,
        label_rows,
        cfg=cfg,
        blend_min=blend_min,
        blend_max=blend_max,
        blend_step=blend_step,
        baseline_rules_srcc=rules_baseline.get("srcc"),
    )
    return {
        "tripDir": str(trip_dir),
        "metric": metric,
        "scored": scored,
        "rulesBaseline": rules_baseline,
        "calibration": search,
    }


def load_merged_assets_for_specs(
    trip_specs: list[dict[str, Any]],
    *,
    root: Path,
    metric: str = "nima",
    allow_cpu: bool = True,
) -> tuple[dict[str, dict], dict[str, bool]]:
    """Load assets from multiple trips; keys are ``tripId::assetId``."""
    from travelogue.curation.aesthetic_stratum_audit import load_trip_assets_by_id, merged_asset_key

    assets_by_id: dict[str, dict] = {}
    scored_flags: dict[str, bool] = {}
    for spec in trip_specs:
        trip_id = str(spec.get("tripId") or "")
        if not trip_id or trip_id.startswith("TBD"):
            continue
        trip_dir = Path(spec["tripDir"])
        if not trip_dir.is_absolute():
            trip_dir = (root / trip_dir).resolve()
        pool = {k: copy.deepcopy(v) for k, v in load_trip_assets_by_id(trip_dir).items()}
        scored_flags[trip_id] = ensure_learned_scores(
            list(pool.values()),
            trip_dir=trip_dir,
            metric=metric,
            allow_cpu=allow_cpu,
        )
        for aid, asset in pool.items():
            assets_by_id[merged_asset_key(trip_id, aid)] = asset
    return assets_by_id, scored_flags


def run_stratum_blend_calibration_merged(
    *,
    trip_specs: list[dict[str, Any]],
    label_rows: list[dict[str, Any]],
    root: Path,
    metric: str = "nima",
    allow_cpu: bool = True,
    blend_min: float = 0.0,
    blend_max: float = 0.6,
    blend_step: float = 0.05,
) -> dict[str, Any]:
    """P2 · per-stratum blend grid on pooled multi-trip labels."""
    from travelogue.curation.aesthetic_stratum_audit import remap_rows_for_merged

    assets_by_id, scored_flags = load_merged_assets_for_specs(
        trip_specs,
        root=root,
        metric=metric,
        allow_cpu=allow_cpu,
    )
    remapped = remap_rows_for_merged(label_rows)
    cfg = AestheticConfig(use_purpose_presets=True, ml_calibrate=True)
    rules_baseline = _srcc_for_predictions(
        remapped,
        assets_by_id,
        predict_fn=lambda asset, _row: rules_for_purpose(asset, "default", cfg=cfg),
    )
    search = grid_search_stratum_blend(
        assets_by_id,
        remapped,
        cfg=cfg,
        blend_min=blend_min,
        blend_max=blend_max,
        blend_step=blend_step,
        baseline_rules_srcc=rules_baseline.get("srcc"),
    )
    active_trips = [str(s["tripId"]) for s in trip_specs if not str(s.get("tripId") or "").startswith("TBD")]
    return {
        "metric": metric,
        "trips": active_trips,
        "scoredByTrip": scored_flags,
        "rulesBaseline": rules_baseline,
        "stratumCalibration": search,
    }


def per_stratum_rules_vs_blend(
    label_rows: list[dict[str, Any]],
    assets_by_id: dict[str, dict],
    *,
    recommended_blends: dict[str, float],
    portrait_lite: bool = True,
) -> dict[str, Any]:
    """Per-stratum rules SRCC vs stratum-blend SRCC (for AC-SC-01)."""
    from travelogue.curation.aesthetic_blind_review import srcc_report

    rules_cfg = AestheticConfig(ml_calibrate=False, use_purpose_presets=True)
    blend_cfg = AestheticConfig(
        ml_calibrate=True,
        use_stratum_blend=True,
        stratum_blends=recommended_blends,
        portrait_lite_enabled=portrait_lite,
    )

    def _prepare(predict_fn) -> list[dict[str, Any]]:
        prepared: list[dict[str, Any]] = []
        for row in label_rows:
            if row.get("humanScore") is None:
                continue
            aid = str(row.get("assetId") or "")
            asset = assets_by_id.get(aid)
            if not asset:
                continue
            try:
                hs = normalize_human_score(row["humanScore"])
                pred = predict_fn(asset, row)
            except (TypeError, ValueError):
                continue
            if pred is None:
                continue
            prepared.append({**row, "humanScore": hs, "predictedOverall": float(pred)})
        return prepared

    rules_rows = _prepare(lambda asset, _row: rules_for_purpose(asset, "default", cfg=rules_cfg))
    blend_rows = _prepare(
        lambda asset, row: blended_score(
            rules_for_purpose(asset, "default", cfg=blend_cfg),
            _read_learned_aesthetic_score(asset),
            resolve_learned_blend(asset, blend_cfg),
        )
    )
    rules_by = srcc_report(rules_rows, by_stratum=True).get("byStratum") or {}
    blend_by = srcc_report(blend_rows, by_stratum=True).get("byStratum") or {}
    out: dict[str, Any] = {}
    for stratum in sorted(set(rules_by) | set(blend_by)):
        r_srcc = (rules_by.get(stratum) or {}).get("srcc")
        b_srcc = (blend_by.get(stratum) or {}).get("srcc")
        n = (blend_by.get(stratum) or {}).get("sampleCount") or (rules_by.get(stratum) or {}).get("sampleCount")
        delta = None if r_srcc is None or b_srcc is None else round(float(b_srcc) - float(r_srcc), 4)
        out[stratum] = {
            "sampleCount": n,
            "rulesSrcc": r_srcc,
            "stratumBlendSrcc": b_srcc,
            "delta": delta,
            "passedAcSc01": (
                n is not None
                and n >= 3
                and r_srcc is not None
                and b_srcc is not None
                and float(b_srcc) > float(r_srcc)
            ),
        }
    return out


def build_eval_rows(
    assets_by_id: dict[str, dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
) -> list[dict[str, Any]]:
    cfg = cfg or AestheticConfig(ml_calibrate=True)
    out: list[dict[str, Any]] = []
    for row in label_rows:
        aid = str(row.get("assetId") or "")
        asset = assets_by_id.get(aid)
        if not asset or row.get("humanScore") is None:
            continue
        out.append(
            {
                "assetId": aid,
                "humanScore": row.get("humanScore"),
                "stratum": row.get("stratum"),
                "rulesOnly": rules_only_overall(asset, cfg=cfg),
                "learnedOnly": _read_learned_aesthetic_score(asset),
                "blendedOverall": aesthetic_overall(asset),
                "blendedCover": purpose_overall(asset, "cover", cfg=cfg),
                "blendedHero": purpose_overall(asset, "hero", cfg=cfg),
                "blendedMoment": purpose_overall(asset, "moment", cfg=cfg),
                "blendedSolo": purpose_overall(asset, "solo", cfg=cfg),
                "baselinePredicted": row.get("predictedOverall"),
            }
        )
    return out


def srcc_comparison(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = {
        "baselinePredicted": "baseline_rules_export",
        "rulesOnly": "rules_only_recomputed",
        "learnedOnly": "learned_nima",
        "blendedOverall": "rules_plus_learned_blend",
        "blendedCover": "blended_cover",
        "blendedHero": "blended_hero",
        "blendedMoment": "blended_moment",
        "blendedSolo": "blended_solo",
    }
    report: dict[str, Any] = {"sampleCount": len(rows), "metrics": {}}
    for field, label in keys.items():
        subset = [
            {"humanScore": r["humanScore"], "predictedOverall": r.get(field)}
            for r in rows
            if r.get(field) is not None
        ]
        rep = srcc_from_label_rows(subset)
        report["metrics"][label] = {
            "field": field,
            "sampleCount": rep["sampleCount"],
            "srcc": rep["srcc"],
        }
    return report


def run_learned_eval(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    metric: str = "nima",
    blend: float = 0.4,
    allow_cpu: bool = True,
    use_stratum_blend: bool = False,
    stratum_blends: dict[str, float] | None = None,
    portrait_lite: bool = True,
) -> dict[str, Any]:
    """Score trip with learned metric and compare SRCC vs human labels."""
    trip_path = trip_dir / "trip.json"
    import json

    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assets = list(trip.get("assets") or [])
    assets_by_id = {str(a["id"]): copy.deepcopy(a) for a in assets if a.get("id")}

    app_cfg = AppConfig()
    blends = dict(DEFAULT_STRATUM_BLENDS)
    if stratum_blends:
        blends.update(stratum_blends)
    ae_cfg = replace(
        app_cfg.aesthetic,
        ml_calibrate=True,
        ml_calibrate_blend=blend,
        learned_metric=metric,
        learned_allow_cpu=allow_cpu,
        source="rules+ml",
        use_stratum_blend=use_stratum_blend,
        stratum_blends=blends,
        portrait_lite_enabled=portrait_lite,
    )
    app_cfg = replace(app_cfg, aesthetic=ae_cfg)

    scored = apply_aesthetic_ml_calibration(
        list(assets_by_id.values()),
        trip_dir=trip_dir,
        cfg=app_cfg,
    )
    if portrait_lite:
        for asset in assets_by_id.values():
            refresh_portrait_lite_overall(asset, cfg=ae_cfg)
    eval_rows = build_eval_rows(assets_by_id, label_rows, cfg=ae_cfg)
    comparison = srcc_comparison(eval_rows)
    return {
        "tripDir": str(trip_dir),
        "metric": metric,
        "blend": blend,
        "useStratumBlend": use_stratum_blend,
        "stratumBlends": blends if use_stratum_blend else None,
        "portraitLite": portrait_lite,
        "scored": scored,
        "evalRows": len(eval_rows),
        "comparison": comparison,
    }
