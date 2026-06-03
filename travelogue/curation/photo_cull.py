"""排版前照片筛选 · Phase 9 Quality Gate."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

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


def _face_ratio(asset: dict) -> float:
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("faceRatio") is not None:
        try:
            return max(0.0, min(1.0, float(q["faceRatio"])))
        except (TypeError, ValueError):
            pass
    box = asset.get("salientBox")
    if isinstance(box, dict):
        try:
            ratio = float(box.get("w", 0.0)) * float(box.get("h", 0.0))
            return max(0.0, min(1.0, ratio))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _has_face_signal(asset: dict) -> bool:
    q = asset.get("quality")
    if isinstance(q, dict):
        if q.get("faceRatio") is not None:
            return True
        if q.get("faceCount") is not None:
            try:
                return int(q.get("faceCount") or 0) > 0
            except (TypeError, ValueError):
                return False
    box = asset.get("salientBox")
    if isinstance(box, dict):
        try:
            return float(box.get("w", 0.0)) > 0.0 and float(box.get("h", 0.0)) > 0.0
        except (TypeError, ValueError):
            return False
    return False


def _branch_for_asset(asset: dict, *, cfg: CullConfig) -> Literal["portrait", "landscape", "gray"]:
    ratio = _face_ratio(asset)
    if ratio >= cfg.face_ratio_portrait_min:
        return "portrait"
    if cfg.face_ratio_gray_low <= ratio <= cfg.face_ratio_gray_high:
        return "gray"
    return "landscape"


def _l2_branch_fallback_reason(asset: dict, *, cfg: CullConfig) -> str | None:
    if not cfg.portrait_quality_enabled:
        return "branch_disabled"
    ratio = _face_ratio(asset)
    if cfg.face_ratio_gray_low <= ratio <= cfg.face_ratio_gray_high:
        return "gray_zone"
    if not _has_face_signal(asset):
        return "face_signal_missing"
    return None


def _portrait_quality_score(asset: dict, *, sharp_part: float) -> float:
    ratio = _face_ratio(asset)
    q = asset.get("quality")
    mean_luma = 0.5
    if isinstance(q, dict) and q.get("meanLuma") is not None:
        try:
            mean_luma = max(0.0, min(1.0, float(q["meanLuma"])))
        except (TypeError, ValueError):
            mean_luma = 0.5
    exposure_center = 1.0 - min(1.0, abs(mean_luma - 0.5) * 2.0)
    # Favor clear face-dominant portraits with balanced exposure.
    return min(1.0, max(0.0, ratio * 0.55 + sharp_part * 0.30 + exposure_center * 0.15))


def _landscape_quality_score(
    asset: dict,
    *,
    sharp_part: float,
    aesthetic: float | None,
) -> float:
    aspect = str(asset.get("aspectKind") or "")
    aspect_boost = 0.0 if aspect == "portrait" else 0.12
    base = sharp_part * 0.70 + _media_weight(asset) * 0.30 + aspect_boost
    if aesthetic is not None:
        base = base * 0.7 + aesthetic * 0.3
    return min(1.0, max(0.0, base))


def _cull_score(
    asset: dict,
    *,
    sharp_lo: float,
    sharp_hi: float,
    use_ml: bool,
    cfg: CullConfig,
) -> float:
    sharp_part = _norm_sharpness(asset_sharpness(asset), lo=sharp_lo, hi=sharp_hi)
    media = _media_weight(asset)
    aesthetic = _aesthetic_score(asset) if use_ml else None
    if aesthetic is not None:
        base_score = (
            cfg.score_sharpness_weight_ml * sharp_part
            + cfg.score_aesthetic_weight_ml * aesthetic
            + cfg.score_media_weight_ml * media
            + cfg.score_bias_ml
        )
    else:
        base_score = (
            cfg.score_sharpness_weight_rules * sharp_part
            + cfg.score_media_weight_rules * media
        )

    if not cfg.portrait_quality_enabled:
        return base_score

    branch = _branch_for_asset(asset, cfg=cfg)
    if branch == "portrait":
        branch_score = _portrait_quality_score(asset, sharp_part=sharp_part)
        w = cfg.score_branch_weight_portrait
    elif branch == "landscape":
        branch_score = _landscape_quality_score(
            asset,
            sharp_part=sharp_part,
            aesthetic=aesthetic,
        )
        w = cfg.score_branch_weight_landscape
    else:
        portrait_s = _portrait_quality_score(asset, sharp_part=sharp_part)
        landscape_s = _landscape_quality_score(
            asset,
            sharp_part=sharp_part,
            aesthetic=aesthetic,
        )
        branch_score = max(portrait_s, landscape_s)
        w = max(cfg.score_branch_weight_portrait, cfg.score_branch_weight_landscape)

    q = asset.setdefault("quality", {})
    if isinstance(q, dict):
        q["cullBranch"] = branch
        q["cullBranchScore"] = round(float(branch_score), 4)
    return (1.0 - w) * base_score + w * branch_score


def _preliminary_score(
    asset: dict,
    *,
    sharp_lo: float,
    sharp_hi: float,
    use_ml: bool = False,
    cfg: CullConfig,
) -> float:
    return _cull_score(
        asset,
        sharp_lo=sharp_lo,
        sharp_hi=sharp_hi,
        use_ml=use_ml,
        cfg=cfg,
    )


def _cull_group_id(asset: dict) -> str | None:
    burst = asset.get("burstGroupId")
    if burst:
        return f"burst:{burst}"
    dedupe = asset.get("dedupeGroupId")
    if dedupe:
        return f"dedupe:{dedupe}"
    return None


def _set_cull_explain(asset: dict, detail: str | None, *, cfg: CullConfig) -> None:
    if not cfg.enable_cull_explain or not detail:
        return
    q = asset.setdefault("quality", {})
    if isinstance(q, dict):
        q["cullExplain"] = detail


def _exclude(
    asset: dict,
    reason: str,
    stats: CullStats,
    *,
    cfg: CullConfig,
    detail: str | None = None,
) -> None:
    asset["layoutEligible"] = False
    asset["excludeReason"] = reason
    _set_cull_explain(asset, detail, cfg=cfg)
    aid = str(asset.get("id") or "")
    if aid:
        stats.bump(reason, aid)


def _clear_cull_exclude_reason(asset: dict) -> None:
    reason = str(asset.get("excludeReason") or "")
    if reason in CULL_EXCLUDE_REASONS:
        asset.pop("excludeReason", None)


def _reset_for_recull(assets: list[dict], cfg: CullConfig) -> None:
    for a in assets:
        if a.get("type", "image") == "video":
            continue
        reason = str(a.get("excludeReason") or "")
        if reason in CULL_EXCLUDE_REASONS:
            a.pop("excludeReason", None)
        if _is_featured(a, cfg):
            a["layoutEligible"] = True
        elif reason in CULL_EXCLUDE_REASONS:
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
    bucket_thresholds: dict[str, float] = {}
    if cfg.bucketed_blur_thresholds:
        by_bucket: dict[str, list[float]] = {}
        for a in non_feat:
            bucket = str(a.get("mediaClass") or "photo")
            by_bucket.setdefault(bucket, []).append(asset_sharpness(a))
        for bucket, values in by_bucket.items():
            if len(values) < max(1, cfg.bucketed_blur_min_samples):
                continue
            bp = _percentile(values, cfg.blur_percentile)
            bucket_thresholds[bucket] = max(cfg.sharpness_absolute_min, bp * 0.85)

    for a in assets:
        if _is_featured(a, cfg):
            continue
        mc = str(a.get("mediaClass") or "")
        if mc in hard_classes:
            _exclude(
                a,
                "media_class",
                stats,
                cfg=cfg,
                detail=f"mediaClass={mc} in hard_exclude_media_classes",
            )
            continue
        threshold = bucket_thresholds.get(mc, blur_threshold)
        sharp = asset_sharpness(a)
        if sharp < threshold:
            _exclude(
                a,
                "blur",
                stats,
                cfg=cfg,
                detail=f"sharpness={sharp:.2f} < blur_threshold={threshold:.2f} (bucket={mc})",
            )


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
                sc = _preliminary_score(
                    a,
                    sharp_lo=sharp_lo,
                    sharp_hi=sharp_hi,
                    use_ml=use_ml,
                    cfg=cfg,
                )
                if sc > best_score:
                    best_score = sc
                    keep_material = a
            for a in group:
                if _is_featured(a, cfg):
                    continue
                if a is not keep_material:
                    _exclude(
                        a,
                        "duplicate_group",
                        stats,
                        cfg=cfg,
                        detail=f"group={_cull_group_id(a) or ''} lost_to={str((keep_material or {}).get('id') or '')}",
                    )
            continue
        if not cfg.recalc_strict_groups:
            # Default path: material-only groups skip Pass 2; ingest dedupe stays authoritative.
            continue
        keep: dict | None = None
        best_score = -1.0
        for a in group:
            sc = _preliminary_score(
                a,
                sharp_lo=sharp_lo,
                sharp_hi=sharp_hi,
                use_ml=use_ml,
                cfg=cfg,
            )
            if sc > best_score:
                best_score = sc
                keep = a
        for a in group:
            if keep is not None and a is not keep:
                _exclude(
                    a,
                    "duplicate_group",
                    stats,
                    cfg=cfg,
                    detail=f"group={_cull_group_id(a) or ''} lost_to={str((keep or {}).get('id') or '')}",
                )


def _assign_scores_and_ranks(
    assets: list[dict],
    *,
    cfg: CullConfig,
    sharp_lo: float,
    sharp_hi: float,
    use_ml: bool = False,
) -> list[tuple[dict, float]]:
    group_members: dict[str, list[dict]] = {}
    for a in assets:
        gid = _cull_group_id(a)
        if gid:
            group_members.setdefault(gid, []).append(a)
    group_best_id: dict[str, str] = {}
    for gid, members in group_members.items():
        if len(members) <= 1:
            continue
        best = max(
            members,
            key=lambda item: _preliminary_score(
                item,
                sharp_lo=sharp_lo,
                sharp_hi=sharp_hi,
                use_ml=use_ml,
                cfg=cfg,
            ),
        )
        best_id = str(best.get("id") or "")
        if best_id:
            group_best_id[gid] = best_id

    scored: list[tuple[dict, float]] = []
    for a in assets:
        if not a.get("layoutEligible", True):
            continue
        sc = _preliminary_score(
            a,
            sharp_lo=sharp_lo,
            sharp_hi=sharp_hi,
            use_ml=use_ml,
            cfg=cfg,
        )
        gid = _cull_group_id(a)
        aid = str(a.get("id") or "")
        if (
            gid
            and gid in group_best_id
            and aid
            and aid != group_best_id[gid]
            and cfg.score_duplicate_group_penalty > 0
        ):
            sc = max(0.0, sc - cfg.score_duplicate_group_penalty)
        q = a.setdefault("quality", {})
        if isinstance(q, dict):
            q["cullScore"] = round(sc, 4)
        scored.append((a, sc))
    def _sort_key(item: tuple[dict, float]) -> tuple[float, float, str, str]:
        a, sc = item
        sharp = asset_sharpness(a)
        taken = str(a.get("takenAt") or "")
        aid = str(a.get("id") or "")
        # deterministic: score -> sharpness -> takenAt -> assetId
        return (-sc, -sharp, taken, aid)

    scored.sort(key=_sort_key)
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
    scored = _assign_scores_and_ranks(
        pool,
        cfg=cfg,
        sharp_lo=sharp_lo,
        sharp_hi=sharp_hi,
        use_ml=use_ml,
    )
    if len(scored) <= n_min:
        meta["pass3Skipped"] = "pool_at_or_below_floor"
        return meta

    threshold = max(0.0, min(1.0, float(cfg.score_threshold)))
    topk_ratio = max(0.0, min(1.0, float(cfg.score_topk_ratio)))
    if threshold <= 0.0 and topk_ratio >= 1.0:
        threshold_keep = len(scored)
        ratio_keep = len(scored)
        keep_n = n_min
    else:
        threshold_keep = len(scored)
        if threshold > 0.0:
            threshold_keep = sum(1 for _a, sc in scored if sc >= threshold)
        ratio_keep = len(scored)
        if topk_ratio < 1.0:
            ratio_keep = max(1, math.ceil(len(scored) * topk_ratio))
        tuned_keep = min(len(scored), threshold_keep, ratio_keep)
        keep_n = max(n_min, tuned_keep)
    keep_n = min(len(scored), keep_n)
    meta["scoreThreshold"] = round(threshold, 4)
    meta["scoreTopkRatio"] = round(topk_ratio, 4)
    meta["scoreThresholdKeep"] = threshold_keep
    meta["scoreTopkKeep"] = ratio_keep
    meta["scoreKeepApplied"] = keep_n

    for a, _ in scored[keep_n:]:
        _exclude(
            a,
            "cull_quota",
            stats,
            cfg=cfg,
            detail=f"rank={int((a.get('quality') or {}).get('cullRank') or 0)} > keep_top={keep_n}",
        )

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
    t0 = time.perf_counter()
    images = _image_assets(assets)
    n_scan = len(images)
    n_feat = sum(1 for a in images if _is_featured(a, cfg))
    branch_counts: dict[str, int] = {"portrait": 0, "landscape": 0, "gray": 0}
    branch_fallback_counts: dict[str, int] = {
        "branch_disabled": 0,
        "gray_zone": 0,
        "face_signal_missing": 0,
    }
    l2_fallback_count = 0
    if cfg.portrait_quality_enabled:
        for a in images:
            branch_counts[_branch_for_asset(a, cfg=cfg)] += 1
    for a in images:
        reason = _l2_branch_fallback_reason(a, cfg=cfg)
        if not reason:
            continue
        l2_fallback_count += 1
        branch_fallback_counts[reason] = branch_fallback_counts.get(reason, 0) + 1
        q = a.setdefault("quality", {})
        if isinstance(q, dict):
            q["cullBranchFallbackReason"] = reason
    stats = CullStats()
    runtime_mode = resolve_effective_mode(cfg)
    requested_mode = str(cfg.mode or "rules").lower().strip()
    use_ml = False
    l1_ml_fallback = False
    if runtime_mode == "ml":
        if trip_dir is not None:
            apply_aesthetic_scores(images, trip_dir=trip_dir, cfg=cfg)
        use_ml = any(_aesthetic_score(a) is not None for a in images)
        if not use_ml:
            runtime_mode = "rules"
            l1_ml_fallback = True
    elif requested_mode in ("ml", "auto"):
        l1_ml_fallback = runtime_mode == "rules"

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
            sc = _preliminary_score(
                a,
                sharp_lo=sharp_lo,
                sharp_hi=sharp_hi,
                use_ml=use_ml,
                cfg=cfg,
            )
            q = a.setdefault("quality", {})
            if isinstance(q, dict):
                q["cullScore"] = round(sc, 4)

    pass4 = _pass4_warn(images, cfg=cfg, max_photos=max_photos)

    summary: dict[str, Any] = {
        "enabled": True,
        "failOpen": False,
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
        "scoreThreshold": pass3_meta.get("scoreThreshold"),
        "scoreTopkRatio": pass3_meta.get("scoreTopkRatio"),
        "scoreKeepApplied": pass3_meta.get("scoreKeepApplied"),
        "mlFallbackRateL1": 1.0 if l1_ml_fallback else 0.0,
        "branchFallbackRateL2": round(l2_fallback_count / n_scan, 4) if n_scan > 0 else 0.0,
        "branchFallbackByReasonL2": dict(branch_fallback_counts),
        "failOpenRateL3": 0.0,
        **pass4,
    }
    if n_scan > 0:
        summary["branchPortraitRatio"] = round(branch_counts["portrait"] / n_scan, 4)
        summary["branchLandscapeRatio"] = round(branch_counts["landscape"] / n_scan, 4)
        summary["branchGrayRatio"] = round(branch_counts["gray"] / n_scan, 4)
    summary["cullUserLine"] = _build_user_line(summary)
    summary["cpuMs"] = round((time.perf_counter() - t0) * 1000.0, 3)
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
                _clear_cull_exclude_reason(a)
        summary = {
            "enabled": True,
            "failOpen": True,
            "error": str(exc),
            "layoutEligibleCount": len(_image_assets(body)),
            "failOpenRateL3": 1.0,
            "cpuMs": 0.0,
        }
        curation = trip.setdefault("curation", {})
        curation["cullSummary"] = dict(summary)
        curation.pop("cullUserLine", None)
        curation.pop("excludedByCullAssetIds", None)
        if ingest_stats is not None:
            ingest_stats["cull_error"] = str(exc)
            ingest_stats["cull_fail_open"] = True
            ingest_stats["cull_l1_ml_fallback_rate"] = 0.0
            ingest_stats["cull_l2_branch_fallback_rate"] = 0.0
            ingest_stats["cull_l3_fail_open_rate"] = 1.0
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
        ingest_stats["cull_fail_open"] = bool(summary.get("failOpen"))
        ingest_stats["cull_l1_ml_fallback_rate"] = float(summary.get("mlFallbackRateL1") or 0.0)
        ingest_stats["cull_l2_branch_fallback_rate"] = float(
            summary.get("branchFallbackRateL2") or 0.0
        )
        ingest_stats["cull_l3_fail_open_rate"] = float(summary.get("failOpenRateL3") or 0.0)
        for reason, count in (summary.get("excludedByReason") or {}).items():
            ingest_stats[f"cull_{reason}"] = count
        for reason, count in (summary.get("branchFallbackByReasonL2") or {}).items():
            ingest_stats[f"cull_l2_{reason}"] = int(count)

    return summary
