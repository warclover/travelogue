"""Cover joint curator (API-CSE-07/08/16) · style × asset pick."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from travelogue.cover_engine.fit import style_avoid_penalty, style_fit_score
from travelogue.cover_engine.registry import (
    get_default_style_id,
    get_profile,
    get_style,
    is_assignable,
    list_assignable_styles,
)
from travelogue.cover_engine.telemetry import record_cover_joint_event
from travelogue.cover_engine.types import CoverJointExplain

_DEFAULT_W_FIT = 0.35
_DEFAULT_W_AVOID = 0.50
_DEFAULT_TOP_K = 8
_DEFAULT_LOW_CONFIDENCE = 0.05


def _trip_id(trip: dict) -> str:
    return str(trip.get("tripId") or "")


def _asset_by_id(assets: list[dict], asset_id: str) -> dict | None:
    for a in assets:
        if a.get("id") == asset_id:
            return a
    return None


def _quality_norm(raw_score: float, *, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    # squash to ~[0, 1]
    return max(0.0, min(1.0, float(raw_score) / max_score))


def iter_joint_candidates(
    trip: dict,
    *,
    layout: str = "web",
    k: int = _DEFAULT_TOP_K,
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
) -> list[dict[str, Any]]:
    """Top-K quality-ranked cover candidates (reuse score_ranked; no full rescan)."""
    from travelogue.curation.curate_scoring import score_ranked_cover_ids
    from travelogue.domain.cover_view import layout_eligible_assets

    pool = assets if assets is not None else layout_eligible_assets(trip)
    ranked = score_ranked_cover_ids(
        pool,
        export_layout=layout,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
        limit=max(1, int(k)),
    )
    out: list[dict[str, Any]] = []
    for row in ranked:
        aid = str(row.get("assetId") or "")
        asset = _asset_by_id(pool, aid)
        if not asset:
            continue
        out.append(
            {
                "asset": asset,
                "quality": float(row.get("score") or 0.0),
            }
        )
    return out


def score_pair(
    asset: dict,
    style_id: str,
    *,
    quality: float = 0.0,
    quality_max: float = 1.0,
    w_fit: float = _DEFAULT_W_FIT,
    w_avoid: float = _DEFAULT_W_AVOID,
) -> CoverJointExplain:
    profile = get_profile(style_id)
    fit = style_fit_score(asset, profile)
    avoid = style_avoid_penalty(asset, profile)
    qn = _quality_norm(quality, max_score=max(quality_max, 1e-6))
    joint = qn + w_fit * fit - w_avoid * avoid
    return CoverJointExplain(
        source="joint-v6",
        style_id=style_id,
        asset_id=str(asset.get("id") or ""),
        joint=round(joint, 6),
        quality=round(qn, 6),
        fit=round(fit, 6),
        avoid_penalty=round(avoid, 6),
        low_confidence=joint < _DEFAULT_LOW_CONFIDENCE,
    )


def _tie_break_key(trip_id: str, style_id: str, asset_id: str) -> int:
    digest = hashlib.sha256(f"{trip_id}|{style_id}|{asset_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def pick_cover_style_and_asset(
    trip: dict,
    *,
    layout: str = "web",
    k: int = _DEFAULT_TOP_K,
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    w_fit: float = _DEFAULT_W_FIT,
    w_avoid: float = _DEFAULT_W_AVOID,
) -> CoverJointExplain:
    """Main path: assignable styles × Top-K; tie-break via tripId hash."""
    styles = list_assignable_styles()
    if not styles:
        return CoverJointExplain(
            source="hash-fallback",
            style_id=get_default_style_id(),
            asset_id="",
            low_confidence=True,
        )

    candidates = iter_joint_candidates(
        trip,
        layout=layout,
        k=k,
        assets=assets,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
    )
    if not candidates:
        return hash_fallback_pick(
            trip,
            layout=layout,
            assets=assets,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
            cover_scoring=cover_scoring,
            cover_scoring_v2=cover_scoring_v2,
            scoring_version=scoring_version,
        )

    qmax = max(c["quality"] for c in candidates) or 1.0
    tid = _trip_id(trip)
    best: CoverJointExplain | None = None
    best_key = -1
    best_unsafe: CoverJointExplain | None = None
    best_unsafe_key = -1

    hard_gate = False
    try:
        from travelogue.config import get_config

        hard_gate = bool(get_config().bookends.title_safe.opening_hard_gate)
    except Exception:
        hard_gate = True

    from travelogue.cover_engine.opening.title_safe import mark_title_safe

    for c in candidates:
        asset = c["asset"]
        for rec in styles:
            explain = score_pair(
                asset,
                rec.id,
                quality=c["quality"],
                quality_max=qmax,
                w_fit=w_fit,
                w_avoid=w_avoid,
            )
            key = _tie_break_key(tid, explain.style_id, explain.asset_id)
            unsafe = bool(
                mark_title_safe(asset, rec.id, hard_gate=hard_gate).get("titleUnsafe")
            )
            if hard_gate and unsafe:
                if best_unsafe is None or explain.joint > best_unsafe.joint or (
                    math.isclose(explain.joint, best_unsafe.joint) and key > best_unsafe_key
                ):
                    best_unsafe = explain
                    best_unsafe_key = key
                continue
            if best is None or explain.joint > best.joint or (
                math.isclose(explain.joint, best.joint) and key > best_key
            ):
                best = explain
                best_key = key

    if best is None and best_unsafe is not None:
        # fail-open: only unsafe pairs existed
        best = best_unsafe

    if best is None:
        raise ValueError("cover joint pick produced no candidate")
    return best


def hash_fallback_pick(
    trip: dict,
    *,
    layout: str = "web",
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
) -> CoverJointExplain:
    """When joint disabled / empty pool: hash % n on active styles + pick_cover_asset_id."""
    from travelogue.curation.curate_scoring import pick_cover_asset_id
    from travelogue.domain.cover_view import layout_eligible_assets

    styles = list_assignable_styles()
    style_id = get_default_style_id()
    if styles:
        digest = hashlib.sha256(_trip_id(trip).encode("utf-8")).hexdigest()
        style_id = styles[int(digest[:8], 16) % len(styles)].id

    pool = assets if assets is not None else layout_eligible_assets(trip)
    asset_id = ""
    if pool:
        asset_id = pick_cover_asset_id(
            pool,
            export_layout=layout,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
            cover_scoring=cover_scoring,
            cover_scoring_v2=cover_scoring_v2,
            scoring_version=scoring_version,
        )
    return CoverJointExplain(
        source="hash-fallback",
        style_id=style_id,
        asset_id=asset_id,
        joint=0.0,
        quality=0.0,
        fit=0.0,
        avoid_penalty=0.0,
        low_confidence=True,
    )


def _explain_to_dict(explain: CoverJointExplain) -> dict[str, Any]:
    return {
        "source": explain.source,
        "styleId": explain.style_id,
        "assetId": explain.asset_id,
        "joint": explain.joint,
        "quality": explain.quality,
        "fit": explain.fit,
        "avoidPenalty": explain.avoid_penalty,
        "lowConfidence": explain.low_confidence,
    }


def apply_joint_pick(
    trip: dict,
    explain: CoverJointExplain,
    *,
    lock: bool = True,
    layout: str = "web",
) -> dict:
    """Write cover + style + explain; optionally set coverJointLocked."""
    meta = trip.setdefault("meta", {})
    curation = trip.setdefault("curation", {})

    if explain.style_id and is_assignable(explain.style_id):
        meta["coverOpeningStyle"] = explain.style_id
    elif not meta.get("coverOpeningStyle"):
        meta["coverOpeningStyle"] = get_default_style_id()

    asset_id = (explain.asset_id or "").strip()
    if asset_id:
        cover_by = curation.setdefault("coverByLayout", {})
        if not isinstance(cover_by, dict):
            cover_by = {}
            curation["coverByLayout"] = cover_by
        cover_by[layout] = asset_id
        # Primary coverAssetId stays mobile-oriented when auto; for web-only write web.
        export_layout = trip.get("exportLayout") or "auto"
        if export_layout == "web" or layout == "mobile":
            trip["coverAssetId"] = asset_id
        elif export_layout == "auto":
            # Keep mobile primary if present; always set web slot.
            if not trip.get("coverAssetId"):
                trip["coverAssetId"] = asset_id

    curation["coverStyleExplain"] = _explain_to_dict(explain)
    if lock:
        from travelogue.cover_engine.lock import set_opening_locked

        set_opening_locked(trip, True)

    from travelogue.cover_engine.lock import is_opening_locked

    record_cover_joint_event(
        _trip_id(trip),
        explain,
        locked=is_opening_locked(trip),
    )
    return trip


def repick_cover_for_style(
    trip: dict,
    style_id: str,
    *,
    layout: str = "web",
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    w_fit: float = _DEFAULT_W_FIT,
    w_avoid: float = _DEFAULT_W_AVOID,
) -> CoverJointExplain:
    """Studio primary path: lock style, re-pick best asset under that style."""
    if not is_assignable(style_id):
        raise ValueError(f"style not assignable: {style_id!r}")

    candidates = iter_joint_candidates(
        trip,
        layout=layout,
        assets=assets,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
    )
    if not candidates:
        from travelogue.curation.curate_scoring import pick_cover_asset_id
        from travelogue.domain.cover_view import layout_eligible_assets

        pool = assets if assets is not None else layout_eligible_assets(trip)
        asset_id = pick_cover_asset_id(pool, export_layout=layout) if pool else ""
        explain = CoverJointExplain(
            source="manual",
            style_id=style_id,
            asset_id=asset_id,
            low_confidence=True,
        )
        apply_joint_pick(trip, explain, lock=True, layout=layout)
        return explain

    qmax = max(c["quality"] for c in candidates) or 1.0
    tid = _trip_id(trip)
    best: CoverJointExplain | None = None
    best_key = -1
    for c in candidates:
        explain = score_pair(
            c["asset"],
            style_id,
            quality=c["quality"],
            quality_max=qmax,
            w_fit=w_fit,
            w_avoid=w_avoid,
        )
        explain = CoverJointExplain(
            source="manual",
            style_id=explain.style_id,
            asset_id=explain.asset_id,
            joint=explain.joint,
            quality=explain.quality,
            fit=explain.fit,
            avoid_penalty=explain.avoid_penalty,
            low_confidence=explain.low_confidence,
        )
        key = _tie_break_key(tid, style_id, explain.asset_id)
        if best is None or explain.joint > best.joint or (
            math.isclose(explain.joint, best.joint) and key > best_key
        ):
            best = explain
            best_key = key

    if best is None:
        raise ValueError("cover joint repick produced no candidate")
    apply_joint_pick(trip, best, lock=True, layout=layout)
    return best


def apply_style_keep_cover(trip: dict, style_id: str) -> CoverJointExplain:
    """Secondary Studio path: change style, keep current web/cover asset."""
    if not is_assignable(style_id):
        raise ValueError(f"style not assignable: {style_id!r}")
    curation = trip.get("curation") or {}
    cover_by = curation.get("coverByLayout") or {}
    asset_id = ""
    if isinstance(cover_by, dict):
        asset_id = str(cover_by.get("web") or "")
    if not asset_id:
        asset_id = str(trip.get("coverAssetId") or "")

    fit = 0.0
    avoid = 0.0
    if asset_id:
        from travelogue.domain.cover_view import layout_eligible_assets

        asset = _asset_by_id(layout_eligible_assets(trip), asset_id)
        if asset:
            profile = get_profile(style_id)
            fit = style_fit_score(asset, profile)
            avoid = style_avoid_penalty(asset, profile)

    explain = CoverJointExplain(
        source="manual",
        style_id=style_id,
        asset_id=asset_id,
        joint=fit - avoid,
        fit=fit,
        avoid_penalty=avoid,
        low_confidence=False,
    )
    meta = trip.setdefault("meta", {})
    meta["coverOpeningStyle"] = style_id
    trip.setdefault("curation", {})["coverStyleExplain"] = _explain_to_dict(explain)
    from travelogue.cover_engine.lock import set_opening_locked

    set_opening_locked(trip, True)
    record_cover_joint_event(_trip_id(trip), explain, locked=True)
    return explain
