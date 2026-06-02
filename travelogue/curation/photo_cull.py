"""排版前照片筛选 · Phase 9 Quality Gate."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, CullConfig, get_config
from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.photo_cull_ml import apply_aesthetic_scores, resolve_effective_mode

_log = logging.getLogger(__name__)

CULL_EXCLUDE_REASONS = frozenset(
    {"media_class", "blur", "duplicate_group", "cull_quota", "exposure_extreme"}
)

_MEDIA_CLASS_WEIGHT: dict[str, float] = {
    "photo": 1.0,
    "unknown": 0.85,
    "archive": 0.15,
    "screenshot": 0.0,
    "thumbnail": 0.0,
    "reupload": 0.0,
}


@dataclass
class CullStats:
    excluded_by_reason: dict[str, int] = field(default_factory=dict)
    excluded_ids: list[str] = field(default_factory=list)

    def bump(self, reason: str, asset_id: str) -> None:
        self.excluded_by_reason[reason] = self.excluded_by_reason.get(reason, 0) + 1
        if asset_id not in self.excluded_ids:
            self.excluded_ids.append(asset_id)


def _is_featured(asset: dict, cfg: CullConfig) -> bool:
    return cfg.featured_exempt and str(asset.get("userTier") or "") == "featured"


def _image_assets(assets: list[dict]) -> list[dict]:
    return [a for a in assets if a.get("type", "image") != "video"]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100.0)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return ordered[lo]
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _norm_sharpness(sharp: float, *, lo: float, hi: float) -> float:
    if hi <= lo:
        return 1.0 if sharp > 0 else 0.0
    return max(0.0, min(1.0, (sharp - lo) / (hi - lo)))


def _media_weight(asset: dict) -> float:
    mc = str(asset.get("mediaClass") or "photo")
    return _MEDIA_CLASS_WEIGHT.get(mc, 0.85)


def _aesthetic_score(asset: dict) -> float | None:
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("aestheticScore") is not None:
        return float(q["aestheticScore"])
    return None


def _cull_score(asset: dict, *, sharp_lo: float, sharp_hi: float, use_ml: bool) -> float:
    sharp_part = _norm_sharpness(asset_sharpness(asset), lo=sharp_lo, hi=sharp_hi)
    media = _media_weight(asset)
    aesthetic = _aesthetic_score(asset) if use_ml else None
    if aesthetic is not None:
        return 0.35 * sharp_part + 0.35 * aesthetic + 0.20 * media + 0.10
    return 0.55 * sharp_part + 0.25 * media


def _preliminary_score(asset: dict, *, sharp_lo: float, sharp_hi: float, use_ml: bool = False) -> float:
    return _cull_score(asset, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml)


def _cull_group_id(asset: dict) -> str | None:
    burst = asset.get("burstGroupId")
    if burst:
        return f"burst:{burst}"
    dedupe = asset.get("dedupeGroupId")
    if dedupe:
        return f"dedupe:{dedupe}"
    return None


def _exclude(asset: dict, reason: str, stats: CullStats) -> None:
    asset["layoutEligible"] = False
    asset["excludeReason"] = reason
    aid = str(asset.get("id") or "")
    if aid:
        stats.bump(reason, aid)


def _reset_for_recull(assets: list[dict], cfg: CullConfig) -> None:
    for a in assets:
        if a.get("type", "image") == "video":
            continue
        reason = str(a.get("excludeReason") or "")
        if reason in CULL_EXCLUDE_REASONS:
            a.pop("excludeReason", None)
        if _is_featured(a, cfg):
            a["layoutEligible"] = True
        elif reason in CULL_EXCLUDE_REASONS or a.get("layoutEligible") is False:
            a["layoutEligible"] = True


def _pass1_hard_exclude(
    assets: list[dict],
    *,
    cfg: CullConfig,
    stats: CullStats,
) -> None:
    hard_classes = set(cfg.hard_exclude_media_classes)
    non_feat = [a for a in assets if not _is_featured(a, cfg)]
    sharp_vals = [asset_sharpness(a) for a in non_feat]
    p2 = _percentile(sharp_vals, cfg.blur_percentile) if sharp_vals else 0.0
    blur_threshold = max(cfg.sharpness_absolute_min, p2 * 0.85)

    for a in assets:
        if _is_featured(a, cfg):
            continue
        mc = str(a.get("mediaClass") or "")
        if mc in hard_classes:
            _exclude(a, "media_class", stats)
            continue
        if asset_sharpness(a) < blur_threshold:
            _exclude(a, "blur", stats)


def _pass2_group_winners(
    assets: list[dict],
    *,
    cfg: CullConfig,
    stats: CullStats,
    sharp_lo: float,
    sharp_hi: float,
    use_ml: bool = False,
) -> None:
    by_group: dict[str, list[dict]] = {}
    for a in assets:
        if not a.get("layoutEligible", True):
            continue
        gid = _cull_group_id(a)
        if not gid:
            continue
        by_group.setdefault(gid, []).append(a)
        q = a.setdefault("quality", {})
        if isinstance(q, dict):
            q["cullGroupId"] = gid

    for group in by_group.values():
        if len(group) <= 1:
            continue
        featured = [a for a in group if _is_featured(a, cfg)]
        if featured:
            keep_material: dict | None = None
            best_score = -1.0
            for a in group:
                if _is_featured(a, cfg):
                    continue
                sc = _preliminary_score(a, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml)
                if sc > best_score:
                    best_score = sc
                    keep_material = a
            for a in group:
                if _is_featured(a, cfg):
                    continue
                if a is not keep_material:
                    _exclude(a, "duplicate_group", stats)
        # PRD §4.1: material-only groups skip Pass 2 (ingest dedupe is authoritative).


def _assign_scores_and_ranks(
    assets: list[dict],
    *,
    sharp_lo: float,
    sharp_hi: float,
    use_ml: bool = False,
) -> list[tuple[dict, float]]:
    scored: list[tuple[dict, float]] = []
    for a in assets:
        if not a.get("layoutEligible", True):
            continue
        sc = _preliminary_score(a, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml)
        q = a.setdefault("quality", {})
        if isinstance(q, dict):
            q["cullScore"] = round(sc, 4)
        scored.append((a, sc))
    scored.sort(key=lambda t: (-t[1], str(t[0].get("id") or "")))
    for rank, (a, _) in enumerate(scored, start=1):
        q = a.get("quality")
        if isinstance(q, dict):
            q["cullRank"] = rank
    return scored


def _pass3_quota(
    assets: list[dict],
    *,
    cfg: CullConfig,
    stats: CullStats,
    n_scan: int,
    use_ml: bool = False,
) -> dict[str, Any]:
    meta: dict[str, Any] = {"pass3Skipped": None, "floorNotMet": False}
    floor_target = math.ceil(cfg.keep_ratio_floor * n_scan)
    n_min = max(floor_target, cfg.min_keep)

    pool = [
        a
        for a in assets
        if a.get("layoutEligible", True) and not _is_featured(a, cfg)
    ]
    if n_scan < cfg.min_keep or len(pool) <= n_min:
        meta["pass3Skipped"] = "pool_at_or_below_floor"
        return meta

    sharp_vals = [asset_sharpness(a) for a in pool]
    sharp_lo = min(sharp_vals) if sharp_vals else 0.0
    sharp_hi = max(sharp_vals) if sharp_vals else 1.0
    scored = _assign_scores_and_ranks(pool, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml)
    if len(scored) <= n_min:
        meta["pass3Skipped"] = "pool_at_or_below_floor"
        return meta

    keep_ids = {str(t[0].get("id")) for t in scored[:n_min]}
    for a, _ in scored[n_min:]:
        _exclude(a, "cull_quota", stats)

    eligible_non_feat = sum(
        1 for a in assets if a.get("layoutEligible", True) and not _is_featured(a, cfg)
    )
    if n_scan > 0 and eligible_non_feat / n_scan < cfg.keep_ratio_floor:
        meta["floorNotMet"] = True
    meta["floorTargetNonFeatured"] = n_min
    return meta


def _pass4_warn(
    assets: list[dict],
    *,
    cfg: CullConfig,
    max_photos: int,
) -> dict[str, Any]:
    eligible = [a for a in assets if a.get("layoutEligible", True)]
    out: dict[str, Any] = {
        "maxPhotosExceeded": False,
        "maxPhotosLimit": max_photos,
        "layoutEligibleCount": len(eligible),
    }
    if cfg.max_photos_warn_only and len(eligible) > max_photos:
        out["maxPhotosExceeded"] = True
        out["warnMessage"] = (
            f"精选与素材共 {len(eligible)} 张进入排版，超过建议上限 {max_photos} 张，成册可能较慢"
        )
    return out


def _build_user_line(summary: dict[str, Any]) -> str:
    n = int(summary.get("layoutEligibleCount") or 0)
    feat = int(summary.get("featuredCount") or 0)
    if feat > 0:
        return f"经挑选 {n} 张进入排版（精选 {feat} 张已为您保留）"
    return f"经挑选 {n} 张进入排版"


def format_ingest_progress_hint(cur: int, total: int, *, cull_enabled: bool) -> str:
    """P9-D §3.2 · merged ingest+cull progress hint for Studio."""
    core = f"已处理 {cur}/{total} 张"
    if cull_enabled and total > 0:
        return f"正在导入并挑选照片（{core}）"
    return core


def cull_stage_hint(cfg: CullConfig) -> str:
    """P9-D §3.2 · sub-hint while Pass 1–4 runs (W2 ML variant)."""
    if not cfg.enabled:
        return ""
    if resolve_effective_mode(cfg) == "ml":
        return "正在评估照片质量…"
    return "正在挑选照片…"


def run_photo_cull(
    assets: list[dict],
    *,
    cfg: CullConfig,
    max_photos: int = 250,
    trip_dir: Path | None = None,
) -> dict[str, Any]:
    """Pure cull passes; mutates assets in place."""
    images = _image_assets(assets)
    n_scan = len(images)
    n_feat = sum(1 for a in images if _is_featured(a, cfg))
    stats = CullStats()
    runtime_mode = resolve_effective_mode(cfg)
    use_ml = False
    if runtime_mode == "ml":
        if trip_dir is not None:
            apply_aesthetic_scores(images, trip_dir=trip_dir, cfg=cfg)
        use_ml = any(_aesthetic_score(a) is not None for a in images)
        if not use_ml:
            runtime_mode = "rules"

    _reset_for_recull(images, cfg)
    _pass1_hard_exclude(images, cfg=cfg, stats=stats)

    non_feat_eligible = [a for a in images if a.get("layoutEligible", True) and not _is_featured(a, cfg)]
    sharp_vals = [asset_sharpness(a) for a in non_feat_eligible] or [0.0]
    sharp_lo, sharp_hi = min(sharp_vals), max(sharp_vals)

    _pass2_group_winners(
        images, cfg=cfg, stats=stats, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml
    )

    pass3_meta = _pass3_quota(images, cfg=cfg, stats=stats, n_scan=n_scan, use_ml=use_ml)

    eligible = [a for a in images if a.get("layoutEligible", True)]
    non_feat_eligible = sum(1 for a in eligible if not _is_featured(a, cfg))

    for a in eligible:
        if _is_featured(a, cfg):
            sc = _preliminary_score(a, sharp_lo=sharp_lo, sharp_hi=sharp_hi, use_ml=use_ml)
            q = a.setdefault("quality", {})
            if isinstance(q, dict):
                q["cullScore"] = round(sc, 4)

    pass4 = _pass4_warn(images, cfg=cfg, max_photos=max_photos)

    summary: dict[str, Any] = {
        "enabled": True,
        "mode": runtime_mode,
        "scanned": n_scan,
        "featuredCount": n_feat,
        "layoutEligibleCount": pass4["layoutEligibleCount"],
        "nonFeaturedEligibleCount": non_feat_eligible,
        "keepRatioFloor": cfg.keep_ratio_floor,
        "excludedByCull": len(stats.excluded_ids),
        "excludedByReason": dict(stats.excluded_by_reason),
        "pass3Skipped": pass3_meta.get("pass3Skipped"),
        "floorNotMet": pass3_meta.get("floorNotMet", False),
        "floorTargetNonFeatured": pass3_meta.get("floorTargetNonFeatured")
        or math.ceil(cfg.keep_ratio_floor * n_scan),
        **pass4,
    }
    summary["cullUserLine"] = _build_user_line(summary)
    return summary


def apply_photo_cull(
    trip: dict,
    assets: list[dict] | None = None,
    *,
    cfg: AppConfig | None = None,
    ingest_stats: dict | None = None,
    trip_dir: Path | None = None,
) -> dict[str, Any]:
    """Full-trip re-cull with fail-open (D-P9-14)."""
    resolved = cfg or get_config()
    cull_cfg = resolved.cull
    body = assets if assets is not None else trip.get("assets") or []

    if not cull_cfg.enabled:
        summary = {"enabled": False, "layoutEligibleCount": sum(1 for a in body if a.get("layoutEligible", True))}
        return summary

    try:
        summary = run_photo_cull(
            body,
            cfg=cull_cfg,
            max_photos=resolved.ingest.max_photos,
            trip_dir=trip_dir,
        )
    except Exception as exc:
        _log.exception("photo cull failed; fail-open")
        for a in body:
            if a.get("type", "image") != "video":
                a["layoutEligible"] = True
        summary = {
            "enabled": True,
            "error": str(exc),
            "layoutEligibleCount": len(_image_assets(body)),
        }
        curation = trip.setdefault("curation", {})
        curation["cullSummary"] = dict(summary)
        curation.pop("cullUserLine", None)
        curation.pop("excludedByCullAssetIds", None)
        if ingest_stats is not None:
            ingest_stats["cull_error"] = str(exc)
        return summary

    curation = trip.setdefault("curation", {})
    curation["cullSummary"] = {k: v for k, v in summary.items() if k != "cullUserLine"}
    curation["cullUserLine"] = summary.get("cullUserLine")
    excluded = [
        str(a["id"])
        for a in body
        if a.get("type", "image") != "video"
        and not a.get("layoutEligible", True)
        and str(a.get("excludeReason") or "") in CULL_EXCLUDE_REASONS
    ]
    if excluded:
        curation["excludedByCullAssetIds"] = excluded
    else:
        curation.pop("excludedByCullAssetIds", None)

    if ingest_stats is not None:
        ingest_stats["cull_excluded"] = summary.get("excludedByCull", 0)
        ingest_stats["cull_layout_eligible"] = summary.get("layoutEligibleCount", 0)
        ingest_stats["cull_user_line"] = summary.get("cullUserLine")
        for reason, count in (summary.get("excludedByReason") or {}).items():
            ingest_stats[f"cull_{reason}"] = count

    return summary
