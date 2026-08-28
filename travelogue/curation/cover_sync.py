"""Opening cover write path (extracted from curate.py · god-module split)."""

from __future__ import annotations

import logging

from travelogue.curation.curate_scoring import (
    build_cover_explain,
    build_cover_layout_review,
    cover_asset_pool,
    median_sharpness,
    orientation_meta_for_cover,
    pick_cover_asset_id_with_meta,
)
from travelogue.curation.curate_scoring import (
    cover_candidates as _cover_candidates,
)
from travelogue.domain.cover_view import layout_eligible_assets

_log = logging.getLogger(__name__)


def _cover_scoring_runtime(
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
):
    from travelogue.config import get_config

    cur = get_config().curate
    cs = cover_scoring if cover_scoring is not None else cur.cover_scoring
    cs_v2 = cover_scoring_v2 if cover_scoring_v2 is not None else cur.cover_scoring_v2
    ver = scoring_version or cur.cover_scoring_version
    return cs, cs_v2, ver


def _cover_explain_for(
    assets: list[dict],
    cover_id: str,
    export_layout: str,
    *,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    enable_phase6_cover_factors: bool = True,
) -> list[dict]:
    from travelogue.curation.cover_scoring_params import resolve_person_demote
    from travelogue.curation.cover_scoring_v2 import resolve_person_demote_v2

    asset = next((a for a in assets if a.get("id") == cover_id), None)
    if not asset:
        return []
    params, params_v2, ver = _cover_scoring_runtime(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured = [a for a in pool if a.get("userTier") == "featured"]
    search = featured if featured else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search)
        if ver == "v2"
        else resolve_person_demote(params, search)
    )
    return build_cover_explain(
        asset,
        export_layout,
        median_sharp=median_sharpness(search),
        cover_scoring=params,
        cover_scoring_v2=params_v2,
        scoring_version=ver,
        pool=search,
        person_demote_mult=person_demote,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
    )


def _sync_trip_covers_core(
    trip: dict,
    *,
    export_layout: str | None = None,
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    featured_min_for_cover_pool: int = 2,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    force: bool = False,
    joint_enabled: bool | None = None,
) -> str:
    """Core Opening write path (called via cover_engine.api.resolve_opening)."""
    from travelogue.cover_engine.lock import is_opening_locked, sync_lock_mirrors

    assets = assets if assets is not None else layout_eligible_assets(trip)
    try:
        from travelogue.vision.subject_backfill import ensure_subject_classes

        ensure_subject_classes(trip, assets, cache_only=True)
    except Exception as exc:
        _log.warning("subjectClass cover backfill failed: %s", exc)
    layout = export_layout or trip.get("exportLayout") or "auto"
    curation = trip.setdefault("curation", {})
    sync_lock_mirrors(trip)
    cs, cs_v2, ver = _cover_scoring_runtime(cover_scoring, cover_scoring_v2, scoring_version)
    p6 = bool(enable_phase6_cover_factors and cs.enable_phase6_factors)
    scoring_kwargs = {
        "cover_scoring": cs,
        "cover_scoring_v2": cs_v2,
        "scoring_version": ver,
    }

    use_joint = joint_enabled
    if use_joint is None:
        try:
            from travelogue.config import get_config

            use_joint = bool(get_config().curate.cover_joint_enabled)
        except Exception:
            use_joint = True

    def _write_blind_review(cover_id: str, profile: str) -> None:
        curation.setdefault("coverBlindReview", {})[profile] = build_cover_layout_review(
            assets,
            cover_id,
            export_layout=profile,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )

    def _apply_web_joint() -> str:
        from travelogue.config import get_config
        from travelogue.cover_engine.joint import (
            apply_joint_pick,
            hash_fallback_pick,
            pick_cover_style_and_asset,
        )

        joint_kwargs = {
            "assets": assets,
            "featured_weight": featured_weight,
            "enable_phase6_cover_factors": p6,
            **scoring_kwargs,
        }
        try:
            cfg = get_config().curate
            top_k = int(getattr(cfg, "cover_joint_top_k", 8) or 8)
            w_fit = float(getattr(cfg, "cover_joint_w_fit", 0.35))
            w_avoid = float(getattr(cfg, "cover_joint_w_avoid", 0.50))
        except Exception:
            top_k, w_fit, w_avoid = 8, 0.35, 0.50

        if use_joint:
            explain = pick_cover_style_and_asset(
                trip,
                layout="web",
                k=top_k,
                w_fit=w_fit,
                w_avoid=w_avoid,
                **joint_kwargs,
            )
        else:
            explain = hash_fallback_pick(trip, layout="web", **joint_kwargs)
        apply_joint_pick(trip, explain, lock=True, layout="web")
        return str(explain.asset_id or "")

    web_locked = is_opening_locked(trip) and not force

    if layout == "auto":
        mobile_id, mobile_orient = pick_cover_asset_id_with_meta(
            assets,
            export_layout="mobile",
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        web_orient: dict[str, object] | None = None
        if web_locked:
            cover_by = curation.get("coverByLayout") or {}
            web_id = str((cover_by.get("web") if isinstance(cover_by, dict) else "") or "")
            if not web_id:
                web_id, web_orient = pick_cover_asset_id_with_meta(
                    assets,
                    export_layout="web",
                    featured_weight=featured_weight,
                    enable_phase6_cover_factors=p6,
                    **scoring_kwargs,
                )
            else:
                web_orient = orientation_meta_for_cover(
                    assets, web_id, export_layout="web"
                )
        else:
            web_id = _apply_web_joint()
            if web_id:
                web_orient = orientation_meta_for_cover(
                    assets, web_id, export_layout="web"
                )
            else:
                web_id, web_orient = pick_cover_asset_id_with_meta(
                    assets,
                    export_layout="web",
                    featured_weight=featured_weight,
                    enable_phase6_cover_factors=p6,
                    **scoring_kwargs,
                )

        curation["coverByLayout"] = {"mobile": mobile_id, "web": web_id}
        curation["coverOrientationByLayout"] = {
            "mobile": mobile_orient,
            "web": web_orient
            or orientation_meta_for_cover(assets, web_id, export_layout="web"),
        }
        trip["coverAssetId"] = mobile_id
        trip["coverCandidates"] = _cover_candidates(
            assets,
            mobile_id,
            export_layout="mobile",
            featured_weight=featured_weight,
            featured_min=featured_min_for_cover_pool,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        curation["coverCandidatesByLayout"] = {
            "mobile": _cover_candidates(
                assets,
                mobile_id,
                export_layout="mobile",
                featured_weight=featured_weight,
                featured_min=featured_min_for_cover_pool,
                enable_phase6_cover_factors=p6,
                **scoring_kwargs,
            ),
            "web": _cover_candidates(
                assets,
                web_id,
                export_layout="web",
                featured_weight=featured_weight,
                featured_min=featured_min_for_cover_pool,
                enable_phase6_cover_factors=p6,
                **scoring_kwargs,
            ),
        }
        mobile_explain = _cover_explain_for(
            assets,
            mobile_id,
            "mobile",
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        web_explain = _cover_explain_for(
            assets,
            web_id,
            "web",
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        if mobile_explain:
            curation["coverExplain"] = mobile_explain
        else:
            curation.pop("coverExplain", None)
        if mobile_explain or web_explain:
            curation["coverExplainByLayout"] = {
                "mobile": mobile_explain,
                "web": web_explain,
            }
        else:
            curation.pop("coverExplainByLayout", None)
        soft_warnings = list(curation.get("bookendsSoftWarnings") or [])
        for side, orient in (("mobile", mobile_orient), ("web", web_orient)):
            if not isinstance(orient, dict) or not orient.get("orientationFallback"):
                continue
            line = orient.get("userOneLiner")
            if not line:
                continue
            code = f"orientation_fallback_{side}"
            if any(isinstance(w, dict) and w.get("code") == code for w in soft_warnings):
                continue
            soft_warnings.append(
                {
                    "code": code,
                    "message": str(line),
                    "layout": side,
                }
            )
        if soft_warnings:
            curation["bookendsSoftWarnings"] = soft_warnings
        _write_blind_review(mobile_id, "mobile")
        _write_blind_review(web_id, "web")
        return mobile_id

    if layout == "web":
        if web_locked:
            cover_by = curation.get("coverByLayout") or {}
            cover_id = str((cover_by.get("web") if isinstance(cover_by, dict) else "") or "")
            if not cover_id:
                cover_id = str(trip.get("coverAssetId") or "")
            if cover_id:
                try:
                    from travelogue.curation.food_policy import annotate_trip_food_policy

                    annotate_trip_food_policy(trip, slot="cover", applied="override")
                except Exception:
                    pass
                return cover_id
        else:
            cover_id = _apply_web_joint()
            if cover_id:
                trip["coverAssetId"] = cover_id
                trip["coverCandidates"] = _cover_candidates(
                    assets,
                    cover_id,
                    export_layout="web",
                    featured_weight=featured_weight,
                    featured_min=featured_min_for_cover_pool,
                    enable_phase6_cover_factors=p6,
                    **scoring_kwargs,
                )
                curation.pop("coverByLayout", None)
                curation.pop("coverCandidatesByLayout", None)
                curation.pop("coverExplainByLayout", None)
                curation["coverOrientationByLayout"] = {
                    "web": orientation_meta_for_cover(
                        assets, cover_id, export_layout="web"
                    )
                }
                explain = _cover_explain_for(
                    assets,
                    cover_id,
                    "web",
                    enable_phase6_cover_factors=p6,
                    **scoring_kwargs,
                )
                if explain:
                    curation["coverExplain"] = explain
                else:
                    curation.pop("coverExplain", None)
                _write_blind_review(cover_id, "web")
                return cover_id

    cover_id, cover_orient = pick_cover_asset_id_with_meta(
        assets,
        export_layout=layout,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    trip["coverAssetId"] = cover_id
    trip["coverCandidates"] = _cover_candidates(
        assets,
        cover_id,
        export_layout=layout,
        featured_weight=featured_weight,
        featured_min=featured_min_for_cover_pool,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    curation.pop("coverByLayout", None)
    curation.pop("coverCandidatesByLayout", None)
    curation.pop("coverExplainByLayout", None)
    if layout in ("mobile", "web"):
        curation["coverOrientationByLayout"] = {layout: cover_orient}
    else:
        curation.pop("coverOrientationByLayout", None)
    explain = _cover_explain_for(
        assets,
        cover_id,
        layout,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    if explain:
        curation["coverExplain"] = explain
    else:
        curation.pop("coverExplain", None)
    _write_blind_review(cover_id, layout)
    return cover_id
