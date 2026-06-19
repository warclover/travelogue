"""AA · GAP-04 · purpose preset weight grid search vs human labels."""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from travelogue.config import AestheticConfig, AestheticPurposePresets, AestheticWeights
from travelogue.curation.aesthetic_learned_eval import (
    _srcc_for_predictions,
    ensure_learned_scores,
    rules_for_purpose,
)
from travelogue.curation.aesthetic_score import (
    _blend_ml_overall,
    _rules_overall_from_weights,
    asset_aesthetic,
    purpose_overall,
)

PurposeGrid = Literal["cover", "hero", "moment", "solo"]
_DIM_KEYS = ("composition", "exposure", "color", "lighting", "subjectClarity")


def _base_weights(cfg: AestheticConfig, purpose: PurposeGrid) -> AestheticWeights:
    presets = cfg.presets
    if purpose == "cover":
        return presets.cover
    if purpose == "hero":
        return presets.hero
    if purpose == "solo":
        return presets.solo
    return presets.moment


def weights_with_dim_emphasis(
    base: AestheticWeights,
    *,
    dim: str,
    emphasis: float,
) -> AestheticWeights:
    """Set one dim to *emphasis* and scale the rest to sum to 1."""
    key = dim if dim != "subject_clarity" else "subjectClarity"
    if key not in _DIM_KEYS:
        raise ValueError(f"unknown dim {dim!r}")
    m = base.as_dim_map()
    emphasis = max(0.05, min(0.85, float(emphasis)))
    others = [k for k in _DIM_KEYS if k != key]
    rest = 1.0 - emphasis
    others_sum = sum(float(m[k]) for k in others) or 1.0
    scaled = {key: emphasis}
    for k in others:
        scaled[k] = rest * float(m[k]) / others_sum
    return AestheticWeights(
        composition=scaled["composition"],
        exposure=scaled["exposure"],
        color=scaled["color"],
        lighting=scaled["lighting"],
        subject_clarity=scaled["subjectClarity"],
    )


def purpose_overall_with_weights(
    asset: dict,
    purpose: PurposeGrid,
    weights: AestheticWeights,
    *,
    cfg: AestheticConfig,
) -> float | None:
    ae = asset_aesthetic(asset)
    if not ae:
        return purpose_overall(asset, purpose, cfg=cfg)
    dims = ae.get("dims")
    if not isinstance(dims, dict) or not dims:
        return purpose_overall(asset, purpose, cfg=cfg)
    rules = _rules_overall_from_weights(dims, weights)
    blended, _, _ = _blend_ml_overall(rules, asset, cfg=cfg, purpose=purpose)
    return blended


def _emphasis_grid(min_v: float, max_v: float, step: float) -> list[float]:
    out: list[float] = []
    v = float(min_v)
    while v <= max_v + 1e-9:
        out.append(round(v, 4))
        v += step
    return out


def grid_search_purpose_weights(
    assets_by_id: dict[str, dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
    purposes: tuple[PurposeGrid, ...] = ("cover", "hero", "moment", "solo"),
    emphasis_dims: tuple[str, ...] = ("subjectClarity", "composition", "color"),
    emphasis_min: float = 0.10,
    emphasis_max: float = 0.40,
    emphasis_step: float = 0.05,
    baseline_rules_srcc: float | None = None,
) -> dict[str, Any]:
    """Grid-search per-purpose dim emphasis; learned scores must be on assets."""
    cfg = cfg or AestheticConfig(ml_calibrate=True, use_purpose_presets=True)
    grid = _emphasis_grid(emphasis_min, emphasis_max, emphasis_step)
    purpose_results: dict[str, Any] = {}

    for purpose in purposes:
        base = _base_weights(cfg, purpose)
        dim_results: dict[str, Any] = {}
        for dim in emphasis_dims:
            rows: list[dict[str, Any]] = []
            for emphasis in grid:
                weights = weights_with_dim_emphasis(base, dim=dim, emphasis=emphasis)

                def _predict(asset: dict, _row: dict, w=weights) -> float | None:
                    return purpose_overall_with_weights(asset, purpose, w, cfg=cfg)

                rep = _srcc_for_predictions(label_rows, assets_by_id, predict_fn=_predict)
                rows.append({"emphasis": emphasis, **rep})
            best = max(
                rows,
                key=lambda r: (-1.0 if r.get("srcc") is None else float(r["srcc"])),
            )
            dim_results[dim] = {
                "grid": rows,
                "bestEmphasis": best["emphasis"],
                "bestSrcc": best.get("srcc"),
            }
        best_dim = max(
            dim_results.items(),
            key=lambda kv: (-1.0 if (kv[1].get("bestSrcc") is None) else float(kv[1]["bestSrcc"])),
        )
        purpose_results[purpose] = {
            "byDim": dim_results,
            "recommended": {
                "dim": best_dim[0],
                "emphasis": best_dim[1]["bestEmphasis"],
                "srcc": best_dim[1]["bestSrcc"],
            },
            "baselineRulesSrcc": baseline_rules_srcc,
        }

    return {
        "emphasisGrid": grid,
        "purposes": purpose_results,
    }


def apply_recommended_presets(
    cfg: AestheticConfig,
    recommended: dict[str, Any],
) -> AestheticConfig:
    """Return cfg copy with preset weights updated from grid-search recommendations."""
    presets = AestheticPurposePresets(
        cover=cfg.presets.cover,
        hero=cfg.presets.hero,
        solo=cfg.presets.solo,
        moment=cfg.presets.moment,
    )
    for purpose, block in (recommended.get("purposes") or {}).items():
        rec = block.get("recommended") or {}
        dim = str(rec.get("dim") or "")
        emphasis = rec.get("emphasis")
        if dim is None or emphasis is None:
            continue
        base = _base_weights(cfg, purpose)  # type: ignore[arg-type]
        new_w = weights_with_dim_emphasis(base, dim=dim, emphasis=float(emphasis))
        if purpose == "cover":
            presets = replace(presets, cover=new_w)
        elif purpose == "hero":
            presets = replace(presets, hero=new_w)
        elif purpose == "solo":
            presets = replace(presets, solo=new_w)
        elif purpose == "moment":
            presets = replace(presets, moment=new_w)
    return replace(cfg, presets=presets)


def run_purpose_weight_calibration(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    metric: str = "nima",
    allow_cpu: bool = True,
    emphasis_min: float = 0.10,
    emphasis_max: float = 0.40,
    emphasis_step: float = 0.05,
) -> dict[str, Any]:
    import json

    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assets = list(trip.get("assets") or [])
    assets_by_id = {str(a["id"]): copy.deepcopy(a) for a in assets if a.get("id")}

    ensure_learned_scores(
        list(assets_by_id.values()),
        trip_dir=trip_dir,
        metric=metric,
        allow_cpu=allow_cpu,
    )

    cfg = AestheticConfig(ml_calibrate=True, use_purpose_presets=True)
    rules_baseline = _srcc_for_predictions(
        label_rows,
        assets_by_id,
        predict_fn=lambda asset, _row: rules_for_purpose(asset, "default", cfg=cfg),
    )
    search = grid_search_purpose_weights(
        assets_by_id,
        label_rows,
        cfg=cfg,
        emphasis_min=emphasis_min,
        emphasis_max=emphasis_max,
        emphasis_step=emphasis_step,
        baseline_rules_srcc=rules_baseline.get("srcc"),
    )
    tuned_cfg = apply_recommended_presets(cfg, search)
    tuned_srcc: dict[str, Any] = {}
    for purpose in ("cover", "hero", "moment", "solo"):
        rep = _srcc_for_predictions(
            label_rows,
            assets_by_id,
            predict_fn=lambda asset, _row, p=purpose: purpose_overall(
                asset, p, cfg=tuned_cfg
            ),
        )
        tuned_srcc[purpose] = rep

    return {
        "tripDir": str(trip_dir),
        "metric": metric,
        "rulesBaseline": rules_baseline,
        "calibration": search,
        "tunedPurposeSrcc": tuned_srcc,
    }


def recommended_cover_weights_dict(cfg: AestheticConfig, calibration: dict[str, Any]) -> dict[str, float]:
    """Serialize tuned cover preset weights for config.yaml."""
    tuned = apply_recommended_presets(cfg, calibration)
    w = tuned.presets.cover
    return {
        "composition": round(w.composition, 4),
        "exposure": round(w.exposure, 4),
        "color": round(w.color, 4),
        "lighting": round(w.lighting, 4),
        "subjectClarity": round(w.subject_clarity, 4),
    }


def run_purpose_weight_calibration_merged(
    *,
    trip_specs: list[dict[str, Any]],
    label_rows: list[dict[str, Any]],
    root: Path,
    metric: str = "nima",
    allow_cpu: bool = True,
    purposes: tuple[PurposeGrid, ...] = ("cover",),
    strata_filter: frozenset[str] | None = None,
    cfg: AestheticConfig | None = None,
    emphasis_min: float = 0.10,
    emphasis_max: float = 0.45,
    emphasis_step: float = 0.05,
) -> dict[str, Any]:
    """Multi-trip purpose weight grid (optional stratum filter, e.g. landscape-only)."""
    from travelogue.curation.aesthetic_learned_eval import load_merged_assets_for_specs
    from travelogue.curation.aesthetic_stratum_audit import remap_rows_for_merged

    assets_by_id, scored_by_trip = load_merged_assets_for_specs(
        trip_specs,
        root=root,
        metric=metric,
        allow_cpu=allow_cpu,
    )
    remapped = remap_rows_for_merged(label_rows)
    if strata_filter:
        remapped = [r for r in remapped if str(r.get("stratum") or "") in strata_filter]

    cfg = cfg or AestheticConfig(ml_calibrate=True, use_purpose_presets=True)
    rules_baseline = _srcc_for_predictions(
        remapped,
        assets_by_id,
        predict_fn=lambda asset, _row: rules_for_purpose(asset, "default", cfg=cfg),
    )
    search = grid_search_purpose_weights(
        assets_by_id,
        remapped,
        cfg=cfg,
        purposes=purposes,
        emphasis_min=emphasis_min,
        emphasis_max=emphasis_max,
        emphasis_step=emphasis_step,
        baseline_rules_srcc=rules_baseline.get("srcc"),
    )
    tuned_cfg = apply_recommended_presets(cfg, search)
    tuned_srcc: dict[str, Any] = {}
    for purpose in purposes:
        rep = _srcc_for_predictions(
            remapped,
            assets_by_id,
            predict_fn=lambda asset, _row, p=purpose: purpose_overall(asset, p, cfg=tuned_cfg),
        )
        tuned_srcc[purpose] = rep

    return {
        "metric": metric,
        "trips": [str(s["tripId"]) for s in trip_specs if not str(s.get("tripId") or "").startswith("TBD")],
        "scoredByTrip": scored_by_trip,
        "strataFilter": sorted(strata_filter) if strata_filter else None,
        "sampleCount": len(remapped),
        "rulesBaseline": rules_baseline,
        "calibration": search,
        "tunedPurposeSrcc": tuned_srcc,
        "recommendedCoverWeights": recommended_cover_weights_dict(cfg, search) if "cover" in purposes else None,
    }

