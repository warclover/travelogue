"""P19 R-501 · asset subset planning (spike / S6 integration)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from travelogue.curation.asset_quality import asset_sharpness, normalized_sharpness
from travelogue.curation.curate import layout_eligible_assets
from travelogue.curation.photo_cull import _aesthetic_score
from travelogue.curation.subject_tagging import subject_class_for_asset

CoverageSubject = Literal["person", "landscape", "food"]

_TIER_SMALL_MAX = 80
_TIER_LARGE_MIN = 300
_DEFAULT_REDUCTION = {
    "small": 0.40,
    "regular": 0.30,
    "large": 0.25,
}


@dataclass
class SubsetConfig:
    """Spike defaults; S6 wires `curation.subset` from config.yaml."""

    enabled: bool = False
    target_reduction: float | None = None
    quality_sharpness_floor: float = 0.12
    min_per_coverage_cell: int = 1
    use_dpp_refine: bool = False


@dataclass
class SubsetPlan:
    kept_asset_ids: list[str]
    dropped_asset_ids: list[str]
    reasons: dict[str, str] = field(default_factory=dict)
    baseline_pool_count: int = 0
    target_keep_pool: int = 0
    target_reduction: float = 0.0
    tier: str = "regular"
    medoid_asset_ids: list[str] = field(default_factory=list)
    coverage_asset_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "keptAssetIds": list(self.kept_asset_ids),
            "droppedAssetIds": list(self.dropped_asset_ids),
            "reasons": dict(self.reasons),
            "baselinePoolCount": self.baseline_pool_count,
            "targetKeepPool": self.target_keep_pool,
            "targetReduction": round(self.target_reduction, 4),
            "tier": self.tier,
            "medoidAssetIds": list(self.medoid_asset_ids),
            "coverageAssetIds": list(self.coverage_asset_ids),
            "actualReduction": round(self._actual_reduction(), 4),
        }

    def _actual_reduction(self) -> float:
        if self.baseline_pool_count <= 0:
            return 0.0
        kept_pool = sum(
            1 for aid in self.kept_asset_ids if self.reasons.get(aid) != "featured_exempt"
        )
        return max(0.0, 1.0 - kept_pool / self.baseline_pool_count)


def _is_featured(asset: dict) -> bool:
    return str(asset.get("userTier") or "") == "featured"


def resolve_subset_tier(pool_count: int) -> str:
    if pool_count <= _TIER_SMALL_MAX:
        return "small"
    if pool_count >= _TIER_LARGE_MIN:
        return "large"
    return "regular"


def resolve_target_reduction(pool_count: int, cfg: SubsetConfig) -> tuple[float, str]:
    if cfg.target_reduction is not None:
        tier = resolve_subset_tier(pool_count)
        return float(cfg.target_reduction), tier
    tier = resolve_subset_tier(pool_count)
    return _DEFAULT_REDUCTION[tier], tier


def _asset_day_key(asset: dict) -> str:
    raw = str(asset.get("takenAt") or "")
    return raw[:10] if len(raw) >= 10 else "unknown"


def _coverage_subject(asset: dict) -> CoverageSubject:
    subj = subject_class_for_asset(asset)
    if subj == "person":
        return "person"
    if subj == "food":
        return "food"
    return "landscape"


def _quality_score(asset: dict, pool: list[dict]) -> float:
    sharp = normalized_sharpness(asset, pool)
    aesthetic = _aesthetic_score(asset)
    aes_part = aesthetic if aesthetic is not None else 0.5
    return 0.55 * sharp + 0.45 * aes_part


def _passes_quality_floor(asset: dict, pool: list[dict], cfg: SubsetConfig) -> bool:
    if normalized_sharpness(asset, pool) < cfg.quality_sharpness_floor:
        sharp = asset_sharpness(asset)
        if sharp > 0 and sharp < 15.0:
            return False
    return True


def _cluster_medoids(trip: dict, pool_ids: set[str]) -> list[str]:
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    clusters = clustering.get("clusters") or []
    out: list[str] = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        medoid = str(cluster.get("medoidAssetId") or "").strip()
        if medoid and medoid in pool_ids:
            out.append(medoid)
            continue
        for aid in cluster.get("assetIds") or []:
            sid = str(aid)
            if sid in pool_ids:
                out.append(sid)
                break
    return out


def _coverage_cells(pool: list[dict]) -> set[tuple[str, CoverageSubject]]:
    cells: set[tuple[str, CoverageSubject]] = set()
    for asset in pool:
        cells.add((_asset_day_key(asset), _coverage_subject(asset)))
    return cells


def _pick_coverage(
    pool: list[dict],
    *,
    cfg: SubsetConfig,
    already: set[str],
) -> list[str]:
    by_cell: dict[tuple[str, CoverageSubject], list[dict]] = {}
    for asset in pool:
        aid = str(asset.get("id") or "")
        if not aid or aid in already:
            continue
        key = (_asset_day_key(asset), _coverage_subject(asset))
        by_cell.setdefault(key, []).append(asset)

    picks: list[str] = []
    for _day, _subj in sorted(by_cell.keys()):
        candidates = sorted(
            by_cell[(_day, _subj)],
            key=lambda a: _quality_score(a, pool),
            reverse=True,
        )
        for asset in candidates[:cfg.min_per_coverage_cell]:
            if not _passes_quality_floor(asset, pool, cfg):
                continue
            aid = str(asset["id"])
            if aid not in already and aid not in picks:
                picks.append(aid)
    return picks


def _fill_to_target(
    pool: list[dict],
    kept: set[str],
    *,
    target: int,
    reasons: dict[str, str],
) -> None:
    if len(kept) >= target:
        return
    ranked = sorted(
        [a for a in pool if str(a.get("id") or "") not in kept],
        key=lambda a: _quality_score(a, pool),
        reverse=True,
    )
    for asset in ranked:
        aid = str(asset.get("id") or "")
        if not aid or aid in kept:
            continue
        kept.add(aid)
        reasons[aid] = reasons.get(aid) or "quality_rank"
        if len(kept) >= target:
            break


def _trim_to_target(
    pool: list[dict],
    kept: set[str],
    essential: set[str],
    *,
    target: int,
    reasons: dict[str, str],
) -> None:
    while len(kept) > target:
        removable = [
            aid
            for aid in kept
            if aid not in essential and reasons.get(aid) not in ("featured_exempt", "cluster_medoid")
        ]
        if not removable:
            break
        worst = min(
            removable,
            key=lambda aid: _quality_score(next(a for a in pool if a.get("id") == aid), pool),
        )
        kept.remove(worst)
        reasons[worst] = "trimmed_to_cap"


def plan_asset_subset(
    trip: dict,
    *,
    cfg: SubsetConfig | None = None,
) -> SubsetPlan:
    """Plan which layout-eligible assets survive into layout (R-501 spike API)."""
    cfg = cfg or SubsetConfig()
    eligible = layout_eligible_assets(trip)
    by_id = {str(a.get("id")): a for a in eligible if a.get("id")}

    featured_ids = [aid for aid, a in by_id.items() if _is_featured(a)]
    pool = [a for a in eligible if not _is_featured(a)]
    pool_ids = {str(a.get("id")) for a in pool if a.get("id")}

    reduction, tier = resolve_target_reduction(len(pool), cfg)
    target_keep = max(1, int(round(len(pool) * (1.0 - reduction))))

    reasons: dict[str, str] = {aid: "featured_exempt" for aid in featured_ids}
    kept: set[str] = set(featured_ids)

    medoids = [
        aid
        for aid in _cluster_medoids(trip, pool_ids)
        if aid in pool_ids and _passes_quality_floor(by_id[aid], pool, cfg)
    ]
    for aid in medoids:
        if aid not in kept:
            kept.add(aid)
            reasons[aid] = "cluster_medoid"

    coverage = _pick_coverage(pool, cfg=cfg, already=kept)
    for aid in coverage:
        if aid not in kept:
            kept.add(aid)
            reasons[aid] = "coverage_cell"

    essential = set(medoids) | set(coverage) | set(featured_ids)
    _fill_to_target(pool, kept, target=target_keep, reasons=reasons)
    _trim_to_target(pool, kept, essential, target=target_keep, reasons=reasons)

    kept_ids = sorted(kept, key=lambda aid: by_id[aid].get("takenAt") or aid)
    dropped = [aid for aid in pool_ids if aid not in kept]
    for aid in dropped:
        reasons.setdefault(aid, "subset_drop")

    return SubsetPlan(
        kept_asset_ids=kept_ids,
        dropped_asset_ids=dropped,
        reasons=reasons,
        baseline_pool_count=len(pool),
        target_keep_pool=target_keep,
        target_reduction=reduction,
        tier=tier,
        medoid_asset_ids=medoids,
        coverage_asset_ids=coverage,
    )


def subset_config_from_curate(cur_cfg) -> SubsetConfig:
    """Map CurateConfig.subset → planner SubsetConfig."""
    sub = getattr(cur_cfg, "subset", None)
    if sub is None:
        return SubsetConfig()
    return SubsetConfig(
        enabled=bool(getattr(sub, "enabled", False)),
        target_reduction=getattr(sub, "target_reduction", None),
        quality_sharpness_floor=float(getattr(sub, "quality_sharpness_floor", 0.12)),
        min_per_coverage_cell=int(getattr(sub, "min_per_coverage_cell", 1)),
    )


def maybe_apply_asset_subset_in_curate(
    trip: dict,
    *,
    trip_dir=None,
    app_cfg=None,
    cur_cfg=None,
) -> dict | None:
    """Insert point: after clustering, before screen planning (R-501 / S6-01)."""
    if cur_cfg is None:
        return None
    cfg = subset_config_from_curate(cur_cfg)
    if not cfg.enabled:
        return None

    if trip_dir is not None and app_cfg is not None:
        clustering = (trip.get("curation") or {}).get("clustering") or {}
        if not clustering.get("clusters"):
            from pathlib import Path

            from travelogue.curation.clustering import run_clustering_layer

            run_clustering_layer(
                trip,
                trip_dir=Path(trip_dir) / "subset-cluster",
                cfg=app_cfg,
            )

    plan = plan_asset_subset(trip, cfg=cfg)
    dropped = apply_subset_plan(trip, plan)
    summary = plan.to_dict()
    summary["layoutEligibleMarked"] = dropped
    return summary


def apply_subset_plan(trip: dict, plan: SubsetPlan) -> int:
    """Mark dropped assets layout-ineligible; returns drop count."""
    dropped = 0
    drop_set = set(plan.dropped_asset_ids)
    for asset in trip.get("assets") or []:
        aid = str(asset.get("id") or "")
        if aid in drop_set and asset.get("layoutEligible", True) is not False:
            asset["layoutEligible"] = False
            asset.setdefault("curation", {})["subsetDropped"] = True
            dropped += 1
    curation = trip.setdefault("curation", {})
    curation["subsetPlan"] = plan.to_dict()
    return dropped
