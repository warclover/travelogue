"""Bookends Engine public API (PRD §4 · B1 Opening facade)."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from travelogue.cover_engine.lock import read_lock_state, sync_lock_mirrors
from travelogue.cover_engine.opening.title_safe import (
    annotate_title_safe_on_explain,
    mark_title_safe,
)
from travelogue.cover_engine.telemetry import record_bookends_event, write_bookends_telemetry
from travelogue.cover_engine.types import BookendsDecision
from travelogue.curation.curate_scoring import orientation_meta_for_cover


class ClosingPendingError(RuntimeError):
    """Raised when resolve_closing is called without screens (B1 / AC-BE-05)."""


class BookendsLockedError(RuntimeError):
    """Raised when force=False but bookends lock refuses rewrite (PRD §14.3)."""

    def __init__(self, message: str = "bookends locked", *, which: str = "closing"):
        super().__init__(message)
        self.which = which
        self.code = "E_BOOKENDS_LOCKED"


def _bookends_cfg():
    try:
        from travelogue.config import get_config

        return get_config().bookends
    except Exception:
        from travelogue.config.bookends import BookendsConfig

        return BookendsConfig()


def _opening_confidence(trip: dict) -> tuple[float, bool]:
    """PRD §5.4 opening-only confidence (closing_pending → use opening_conf)."""
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    style_explain = curation.get("coverStyleExplain")
    joint_low = False
    if isinstance(style_explain, dict):
        joint_low = bool(style_explain.get("lowConfidence"))
    opening_conf = 0.45 if joint_low else 1.0
    # closing_pending: confidence = opening_conf
    low = opening_conf < 0.55 or joint_low
    return opening_conf, low


def _combined_confidence(
    trip: dict,
    *,
    closing_pending: bool,
    closing_asset_id: str | None,
    degraded: bool,
) -> tuple[float, bool]:
    opening_conf, joint_low = _opening_confidence(trip)
    if closing_pending:
        return opening_conf, joint_low or opening_conf < 0.55
    if closing_asset_id is None and degraded:
        closing_conf = 0.0
    elif degraded:
        closing_conf = 0.55
    else:
        closing_conf = 0.85
    confidence = 0.6 * opening_conf + 0.4 * closing_conf
    low = confidence < 0.55 or joint_low
    return confidence, low


def _decision_from_trip(
    trip: dict,
    *,
    cover_asset_id: str,
    closing_pending: bool = True,
    closing_asset_id: str | None = None,
    closing_style_id: str | None = None,
    degraded: bool = False,
    explain: dict[str, Any] | None = None,
    telemetry: dict[str, Any] | None = None,
) -> BookendsDecision:
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    cover_by = curation.get("coverByLayout") if isinstance(curation.get("coverByLayout"), dict) else {}
    cover_by_layout = {
        k: str(v)
        for k, v in cover_by.items()
        if isinstance(k, str) and v
    }
    style_id = str(meta.get("coverOpeningStyle") or "")
    lock = read_lock_state(trip)
    conf, low = _combined_confidence(
        trip,
        closing_pending=closing_pending,
        closing_asset_id=closing_asset_id,
        degraded=degraded,
    )
    cfg = _bookends_cfg()
    versions = {
        "openingQuality": str(cfg.opening_quality_version),
        "closingScorer": str(cfg.closing_scorer_version),
        "pairing": str(cfg.pairing_version),
    }
    return BookendsDecision(
        cover_asset_id=str(cover_asset_id or ""),
        cover_by_layout=cover_by_layout,
        cover_opening_style=style_id,
        closing_asset_id=closing_asset_id,
        closing_style_id=closing_style_id,
        closing_pending=closing_pending,
        confidence=conf,
        low_confidence=low,
        degraded=degraded,
        lock=lock,
        locked=lock.all_locked,
        explain=explain or {},
        scoring_versions=versions,
        telemetry=telemetry or {},
    )


def _annotate_opening_title_safe(trip: dict) -> dict[str, Any]:
    """B1: mark only; never changes Top1 / selected assets."""
    cfg = _bookends_cfg()
    hard_gate = bool(cfg.title_safe.opening_hard_gate)
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    style_id = str(meta.get("coverOpeningStyle") or "")
    cover_by = curation.get("coverByLayout") if isinstance(curation.get("coverByLayout"), dict) else {}
    asset_id = str((cover_by.get("web") if isinstance(cover_by, dict) else "") or "")
    if not asset_id:
        asset_id = str(trip.get("coverAssetId") or "")
    if not style_id or not asset_id:
        return {"titleUnsafe": False, "reasons": [], "hardGateApplied": False}

    assets = trip.get("assets") if isinstance(trip.get("assets"), list) else []
    asset = next((a for a in assets if isinstance(a, dict) and a.get("id") == asset_id), None)
    if not isinstance(asset, dict):
        return {"titleUnsafe": False, "reasons": [], "hardGateApplied": False}

    mark = mark_title_safe(asset, style_id, hard_gate=hard_gate)
    if hard_gate and mark.get("titleUnsafe"):
        mark = {**mark, "hardGateApplied": True}
    else:
        mark = {**mark, "hardGateApplied": False}
    style_explain = curation.get("coverStyleExplain")
    if isinstance(style_explain, dict):
        curation["coverStyleExplain"] = annotate_title_safe_on_explain(style_explain, mark)
    return mark


def resolve_opening(
    trip: dict,
    *,
    layout: str | None = None,
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    featured_min_for_cover_pool: int = 2,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    force: bool = False,
    joint_enabled: bool | None = None,
) -> BookendsDecision:
    """Opening facade: wrap pick_cover_* / joint / apply_joint_pick (B1).

    Does not resolve closing. Returns closing_pending=True.
    """
    t0 = time.perf_counter()
    from travelogue.curation.curate import _sync_trip_covers_core

    cover_id = _sync_trip_covers_core(
        trip,
        export_layout=layout,
        assets=assets,
        featured_weight=featured_weight,
        featured_min_for_cover_pool=featured_min_for_cover_pool,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
        force=force,
        joint_enabled=joint_enabled,
    )
    sync_lock_mirrors(trip)
    title_mark = _annotate_opening_title_safe(trip)

    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    lock = read_lock_state(trip)
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    style_explain = curation.get("coverStyleExplain") if isinstance(curation, dict) else None
    explain: dict[str, Any] = {
        "phase": "opening",
        "coverStyleExplain": style_explain if isinstance(style_explain, dict) else {},
        "titleSafe": title_mark,
    }
    telemetry = {
        "openingStyle": str((trip.get("meta") or {}).get("coverOpeningStyle") or ""),
        "closingPending": True,
        "lowConfidence": bool(isinstance(style_explain, dict) and style_explain.get("lowConfidence")),
        "degraded": False,
        "resolveOpeningMs": ms,
        "titleUnsafe": bool(title_mark.get("titleUnsafe")),
    }
    cfg = _bookends_cfg()
    if cfg.telemetry:
        write_bookends_telemetry(trip, telemetry)
        record_bookends_event(str(trip.get("tripId") or ""), "bookends_resolve_opening", telemetry)

    return _decision_from_trip(
        trip,
        cover_asset_id=cover_id,
        closing_pending=True,
        explain=explain,
        telemetry=telemetry,
    )


def apply_closing_decision(
    trip: dict,
    decision: BookendsDecision,
    *,
    lock: bool | None = None,
) -> BookendsDecision:
    """Persist closing fields on trip (explicit null allowed)."""
    from travelogue.cover_engine.lock import set_closing_locked

    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        return decision
    curation["closingAssetId"] = decision.closing_asset_id  # may be None
    meta = trip.setdefault("meta", {})
    if decision.closing_asset_id and decision.closing_style_id:
        meta["coverClosingStyle"] = decision.closing_style_id
    elif not decision.closing_asset_id:
        meta.pop("coverClosingStyle", None)

    explain = decision.explain or {}
    curation["bookendsExplain"] = {
        **(curation.get("bookendsExplain") if isinstance(curation.get("bookendsExplain"), dict) else {}),
        **explain,
    }
    curation["bookendsVersions"] = dict(decision.scoring_versions)
    if decision.degraded:
        curation["bookendsDegraded"] = True
    else:
        curation.pop("bookendsDegraded", None)

    should_lock = _bookends_cfg().lock_after_resolve if lock is None else bool(lock)
    if should_lock:
        set_closing_locked(trip, True)
    sync_lock_mirrors(trip)
    return _decision_from_trip(
        trip,
        cover_asset_id=decision.cover_asset_id,
        closing_pending=False,
        closing_asset_id=decision.closing_asset_id,
        closing_style_id=decision.closing_style_id,
        degraded=decision.degraded,
        explain=decision.explain,
        telemetry=decision.telemetry,
    )


def resolve_closing(
    trip: dict,
    *,
    layout: str | None = None,
    force: bool = False,
    screens: Any = None,
    occupied_ids: set[str] | None = None,
    persist: bool = True,
    lock: bool | None = None,
) -> BookendsDecision:
    """Resolve closing after screens exist (PRD §4.5.1 / B2a).

    Never reuses cover. No candidates → closing_asset_id=None + degraded.
    """
    from travelogue.cover_engine.closing.gate import trip_has_screens
    from travelogue.cover_engine.closing.pick import pick_closing_with_meta
    from travelogue.cover_engine.lock import is_closing_locked
    from travelogue.cover_engine.pairing.explain import build_closing_explain

    t0 = time.perf_counter()
    if not trip_has_screens(trip, screens=screens):
        raise ClosingPendingError(
            "resolve_closing requires screens (post-layout); closing_pending"
        )

    cfg = _bookends_cfg()
    layout_name = layout or trip.get("exportLayout") or "auto"
    if layout_name == "mobile" and not cfg.mobile_closing:
        # R-BE-10 · do not persist independent mobile closing
        cover_id = str(trip.get("coverAssetId") or "")
        decision = _decision_from_trip(
            trip,
            cover_asset_id=cover_id,
            closing_pending=False,
            closing_asset_id=None,
            closing_style_id=None,
            degraded=False,
            explain={"phase": "closing", "skipped": "mobile_closing_disabled"},
            telemetry={"closingPending": False, "mobileClosingSkipped": True},
        )
        return decision

    if is_closing_locked(trip) and not force:
        curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
        existing = curation.get("closingAssetId") if "closingAssetId" in curation else None
        cover_id = str(trip.get("coverAssetId") or "")
        # FRP · locked closing skips demote/exclude re-pick.
        try:
            from travelogue.curation.food_policy import annotate_trip_food_policy

            annotate_trip_food_policy(trip, slot="closing", applied="override")
        except Exception:
            pass
        return _decision_from_trip(
            trip,
            cover_asset_id=cover_id,
            closing_pending=False,
            closing_asset_id=existing if "closingAssetId" in curation else None,
            closing_style_id=str((trip.get("meta") or {}).get("coverClosingStyle") or "") or None,
            degraded=bool(curation.get("bookendsDegraded"))
            or (existing is None and "closingAssetId" in curation),
            explain={"phase": "closing", "skipped": "locked"},
            telemetry={"closingLocked": True},
        )

    prefer_landscape = layout_name in ("web", "auto")
    pairing = cfg.pairing
    result = pick_closing_with_meta(
        trip,
        prefer_landscape=prefer_landscape,
        exclude_ids=occupied_ids,
        soft_weight=float(pairing.soft_weight),
        near_dup_seconds=float(pairing.near_dup_seconds),
        require_hard=bool(pairing.require_hard) and str(cfg.pairing_version) != "off",
    )
    closing_id = result["closing_asset_id"]
    degraded = bool(result["degraded"])
    style_id = "colophon-default" if closing_id else None
    explain = build_closing_explain(
        closing_asset_id=closing_id,
        degraded=degraded,
        scores=result.get("scores") or {},
        hard_filtered=int(result.get("hard_filtered") or 0),
        unused=bool(result.get("unused")),
        pairing_version=str(cfg.pairing_version),
        excluded_by_moment=list(result.get("excluded_by_moment") or []),
    )
    if degraded:
        explain["statusCode"] = "E_BOOKENDS_NO_CLOSING_CANDIDATE"
    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    telemetry = {
        "closingStyle": style_id or "",
        "closingPending": False,
        "lowConfidence": degraded,
        "degraded": degraded,
        "pairingHardFiltered": int(result.get("hard_filtered") or 0),
        "resolveClosingMs": ms,
        "versions": {
            "closingScorer": str(cfg.closing_scorer_version),
            "pairing": str(cfg.pairing_version),
        },
    }
    cover_id = str(trip.get("coverAssetId") or "")
    decision = _decision_from_trip(
        trip,
        cover_asset_id=cover_id,
        closing_pending=False,
        closing_asset_id=closing_id,
        closing_style_id=style_id,
        degraded=degraded,
        explain=explain,
        telemetry=telemetry,
    )
    if cfg.telemetry:
        write_bookends_telemetry(trip, telemetry)
        record_bookends_event(str(trip.get("tripId") or ""), "bookends_resolve_closing", telemetry)
    if persist:
        decision = apply_closing_decision(trip, decision, lock=lock)
    return decision


def maybe_resolve_closing_after_layout(
    trip: dict,
    *,
    layout: str | None = None,
    force: bool = False,
) -> BookendsDecision | None:
    """Unique write hook after layout (ADR-017 / IMPLEMENTATION).

    Skips when bookends disabled, closing locked, or closingAssetId already set
    (including explicit null).
    """
    cfg = _bookends_cfg()
    if not cfg.enabled:
        return None
    from travelogue.cover_engine.closing.gate import trip_has_screens
    from travelogue.cover_engine.lock import is_closing_locked

    if not trip_has_screens(trip):
        return None
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        return None
    if is_closing_locked(trip) and not force:
        return None
    if "closingAssetId" in curation and not force:
        return None
    try:
        return resolve_closing(trip, layout=layout, force=force, persist=True)
    except ClosingPendingError:
        return None
    except Exception:
        # NFR fail-open → null closing, no cover reuse
        curation["closingAssetId"] = None
        curation["bookendsDegraded"] = True
        return None


def resolve_bookends(
    trip: dict,
    *,
    layout: str | None = None,
    force: bool = False,
    assets: list[dict] | None = None,
    **opening_kwargs: Any,
) -> BookendsDecision:
    """Orchestrate opening + closing when screens exist."""
    from travelogue.cover_engine.closing.gate import trip_has_screens

    opening = resolve_opening(
        trip,
        layout=layout,
        force=force,
        assets=assets,
        **opening_kwargs,
    )
    if not trip_has_screens(trip):
        return opening
    try:
        return resolve_closing(trip, layout=layout, force=force, persist=True)
    except ClosingPendingError:
        return opening


def restore_auto(
    trip: dict,
    *,
    layout: str | None = None,
    **kwargs: Any,
) -> BookendsDecision:
    """Unlock both sides and re-resolve opening + closing when possible."""
    from travelogue.cover_engine.closing.gate import trip_has_screens
    from travelogue.cover_engine.lock import write_lock_state

    write_lock_state(trip, opening=False, closing=False)
    curation = trip.setdefault("curation", {})
    if isinstance(curation, dict):
        curation.pop("closingAssetId", None)
        curation.pop("closingUserPicked", None)
        curation.pop("bookendsDegraded", None)
    # Always force rewrite after unlock; ignore caller force= to avoid kw dup.
    kwargs.pop("force", None)
    opening = resolve_opening(trip, layout=layout, force=True, **kwargs)
    if trip_has_screens(trip):
        try:
            return resolve_closing(trip, layout=layout, force=True, persist=True)
        except ClosingPendingError:
            return opening
    return opening


class ClosingConflictError(RuntimeError):
    """User-picked closing conflicts with new opening (R-BE-14)."""

    def __init__(self, message: str = "closing conflict", *, violations: list[str] | None = None):
        super().__init__(message)
        self.violations = list(violations or [])


def decision_to_dict(decision: BookendsDecision) -> dict[str, Any]:
    explain = decision.explain or {}
    return {
        "coverAssetId": decision.cover_asset_id,
        "coverByLayout": decision.cover_by_layout,
        "coverOpeningStyle": decision.cover_opening_style,
        "closingAssetId": decision.closing_asset_id,
        "closingStyleId": decision.closing_style_id,
        "closingPending": decision.closing_pending,
        "confidence": decision.confidence,
        "lowConfidence": decision.low_confidence,
        "degraded": decision.degraded,
        "lock": {"opening": decision.lock.opening, "closing": decision.lock.closing},
        "locked": decision.locked,
        "explain": explain,
        "userOneLiner": str(
            explain.get("userOneLiner")
            or (trip_user_one_liner_fallback(decision))
        ),
        "scoringVersions": decision.scoring_versions,
        "telemetry": decision.telemetry,
    }


def trip_user_one_liner_fallback(decision: BookendsDecision) -> str:
    if decision.closing_pending:
        return "排版完成后会自动选择封底。"
    if decision.degraded or not decision.closing_asset_id:
        return "可选照片太少，已省略封底图，避免与封面重复。"
    return "封面与封底已成对挑选。"


def build_status_banner(
    *,
    closing_pending: bool,
    degraded: bool,
    low_confidence: bool,
) -> dict[str, str] | None:
    """FE-BE-07 · Studio status strip (user-facing copy only)."""
    if closing_pending:
        return {
            "kind": "pending",
            "code": "E_BOOKENDS_CLOSING_PENDING",
            "message": "排版完成后会自动选择封底",
        }
    if degraded:
        return {
            "kind": "degraded",
            "code": "E_BOOKENDS_NO_CLOSING_CANDIDATE",
            "message": "可选照片太少，已省略封底图",
        }
    if low_confidence:
        return {
            "kind": "lowConfidence",
            "code": "E_BOOKENDS_LOW_CONFIDENCE",
            "message": "备选有限，封面与封底是相对合适的一对",
        }
    return None


def build_bookends_studio_payload(trip: dict) -> dict[str, Any]:
    """Studio GET payload: Decision snapshot + candidates (PRD §7.2)."""
    from travelogue.cover_engine.closing.gate import trip_has_screens
    from travelogue.cover_engine.closing.pick import pick_closing_with_meta
    from travelogue.cover_engine.joint import iter_joint_candidates
    from travelogue.cover_engine.registry import get_style
    from travelogue.cover_engine.studio import studio_style_options
    from travelogue.domain.closing_view import cover_ids_to_exclude

    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    has_screens = trip_has_screens(trip)
    closing_pending = "closingAssetId" not in curation and has_screens is False
    if has_screens and "closingAssetId" not in curation:
        closing_pending = True
    closing_id = curation.get("closingAssetId") if "closingAssetId" in curation else None
    if closing_id is not None:
        closing_id = str(closing_id) if closing_id else None
    degraded = bool(curation.get("bookendsDegraded")) or (
        "closingAssetId" in curation and curation.get("closingAssetId") is None
    )
    explain = curation.get("bookendsExplain") if isinstance(curation.get("bookendsExplain"), dict) else {}
    style_explain = (
        curation.get("coverStyleExplain")
        if isinstance(curation.get("coverStyleExplain"), dict)
        else {}
    )
    low_confidence = bool(
        degraded
        or style_explain.get("lowConfidence")
        or (isinstance(explain, dict) and explain.get("lowConfidence"))
    )
    style_id = str(meta.get("coverOpeningStyle") or "")
    style_rec = get_style(style_id) if style_id else None

    decision = _decision_from_trip(
        trip,
        cover_asset_id=str(trip.get("coverAssetId") or ""),
        closing_pending=closing_pending,
        closing_asset_id=closing_id,
        closing_style_id=str(meta.get("coverClosingStyle") or "") or None,
        degraded=degraded,
        explain=explain if explain else {"phase": "snapshot"},
        telemetry=curation.get("bookendsTelemetry")
        if isinstance(curation.get("bookendsTelemetry"), dict)
        else {},
    )
    # Reflect low confidence from opening explain when not degraded
    if low_confidence and not decision.low_confidence:
        decision = replace(decision, low_confidence=True)
    payload = decision_to_dict(decision)
    banner = build_status_banner(
        closing_pending=closing_pending,
        degraded=degraded,
        low_confidence=low_confidence and not degraded and not closing_pending,
    )
    payload.update(
        {
            "ok": True,
            "panelTitle": "封面与封底",
            "panelSubtitle": "画册的第一眼与最后一眼",
            "closingUserPicked": bool(curation.get("closingUserPicked")),
            "openingLocked": bool(decision.lock.opening),
            "closingLocked": bool(decision.lock.closing),
            "hasScreens": has_screens,
            "mobileClosingEnabled": bool(_bookends_cfg().mobile_closing),
            "coverStyleLabel": (
                (style_rec.studio_label or style_rec.label) if style_rec else style_id
            ),
            "coverStyleOptions": studio_style_options(),
            "openingCandidates": [],
            "closingCandidates": [],
            "closingPreviewOnly": bool(closing_pending),
            "statusBanner": banner,
            "statusCode": (banner or {}).get("code") if banner else None,
            "softWarnings": list(curation.get("bookendsSoftWarnings") or []),
        }
    )

    assets_map: dict[str, dict] = {}
    for raw in trip.get("assets") or []:
        if isinstance(raw, dict) and raw.get("id"):
            assets_map[str(raw["id"])] = raw

    def _cand(aid: str, **extra: Any) -> dict[str, Any]:
        asset = assets_map.get(aid) or {}
        row = {
            "assetId": aid,
            "displayFile": str(asset.get("displayFile") or "").strip() or None,
        }
        row.update(extra)
        return row

    cover_id = str(trip.get("coverAssetId") or "")
    cover_by = (
        curation.get("coverByLayout")
        if isinstance(curation.get("coverByLayout"), dict)
        else {}
    )
    mobile_id = str(cover_by.get("mobile") or cover_id or "").strip()
    web_id = str(cover_by.get("web") or cover_id or "").strip()
    # Spread hero defaults to web/desktop cover (primary acceptance surface)
    hero_cover_id = web_id or cover_id
    payload["mobileCoverAssetId"] = mobile_id or None
    payload["webCoverAssetId"] = web_id or None
    if hero_cover_id:
        payload["coverThumb"] = _cand(hero_cover_id)
    if closing_id:
        payload["closingThumb"] = _cand(closing_id)
    elif degraded:
        payload["closingThumb"] = None
    if mobile_id:
        payload["mobileCoverThumb"] = _cand(mobile_id)
    if web_id:
        payload["webCoverThumb"] = _cand(web_id)

    orient_by = (
        curation.get("coverOrientationByLayout")
        if isinstance(curation.get("coverOrientationByLayout"), dict)
        else {}
    )
    mobile_orient = orient_by.get("mobile") if isinstance(orient_by.get("mobile"), dict) else {}
    web_orient = orient_by.get("web") if isinstance(orient_by.get("web"), dict) else {}
    # Lazily annotate when sync hasn't written orientation meta yet
    if not mobile_orient and mobile_id:
        mobile_orient = orientation_meta_for_cover(
            list(assets_map.values()), mobile_id, export_layout="mobile"
        )
    if not web_orient and web_id:
        web_orient = orientation_meta_for_cover(
            list(assets_map.values()), web_id, export_layout="web"
        )
    payload["coverOrientationByLayout"] = {
        "mobile": mobile_orient or None,
        "web": web_orient or None,
    }
    mobile_fallback = bool(mobile_orient.get("orientationFallback"))
    web_fallback = bool(web_orient.get("orientationFallback"))
    payload["orientationFallback"] = {
        "mobile": mobile_fallback,
        "web": web_fallback,
    }
    payload["mobileCoverHint"] = (
        str(mobile_orient.get("userOneLiner") or "")
        if mobile_fallback
        else (
            "为竖屏另选"
            if mobile_id and web_id and mobile_id != web_id
            else "手机版封面可能与网页不同；封底目前仅网页成书。"
        )
    )
    if mobile_fallback and mobile_orient.get("userOneLiner"):
        soft = list(payload.get("softWarnings") or [])
        code = "orientation_fallback_mobile"
        if not any(isinstance(w, dict) and w.get("code") == code for w in soft):
            soft.append(
                {
                    "code": code,
                    "message": str(mobile_orient["userOneLiner"]),
                    "layout": "mobile",
                }
            )
            payload["softWarnings"] = soft

    # Opening Top-3 (FE-BE-03)
    try:
        for i, row in enumerate(iter_joint_candidates(trip, layout="web", k=3)[:3]):
            asset = row.get("asset") or {}
            aid = str(asset.get("id") or "")
            if aid:
                payload["openingCandidates"].append(
                    _cand(aid, quality=float(row.get("quality") or 0), rank=i)
                )
    except Exception:
        pass
    if hero_cover_id and not any(
        c.get("assetId") == hero_cover_id for c in payload["openingCandidates"]
    ):
        payload["openingCandidates"].insert(0, _cand(hero_cover_id, rank=0, current=True))
        payload["openingCandidates"] = payload["openingCandidates"][:3]

    # Closing candidates (scored); allow preview-only while pending
    covers = cover_ids_to_exclude(trip)
    if has_screens:
        try:
            cfg = _bookends_cfg()
            result = pick_closing_with_meta(
                trip,
                prefer_landscape=True,
                soft_weight=float(cfg.pairing.soft_weight),
                near_dup_seconds=float(cfg.pairing.near_dup_seconds),
                require_hard=bool(cfg.pairing.require_hard),
            )
            scores = result.get("scores") or {}
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]
            for i, (aid, score) in enumerate(ranked):
                if aid in covers:
                    continue
                payload["closingCandidates"].append(
                    _cand(aid, score=float(score), rank=i)
                )
        except Exception:
            pass
    else:
        # Ephemeral preview before layout (PRD §4.5 pending)
        from travelogue.domain.closing_view import _asset_valid_for_closing

        preview_ids = [
            aid
            for aid, asset in assets_map.items()
            if aid not in covers and _asset_valid_for_closing(aid, assets_map)
        ][:5]
        for i, aid in enumerate(preview_ids):
            payload["closingCandidates"].append(_cand(aid, rank=i, preview=True))

    if closing_id and not any(
        c.get("assetId") == closing_id for c in payload["closingCandidates"]
    ):
        payload["closingCandidates"].insert(0, _cand(closing_id, rank=0, current=True))

    # Prefer stored one-liner
    if isinstance(explain, dict) and explain.get("userOneLiner"):
        payload["userOneLiner"] = str(explain["userOneLiner"])
    elif closing_pending:
        payload["userOneLiner"] = "排版完成后会自动选择封底。"
    return payload


def repick_opening(
    trip: dict,
    *,
    asset_id: str | None = None,
    style_id: str | None = None,
    keep_cover: bool = False,
    confirm_closing_conflict: bool = False,
    layout: str | None = None,
) -> BookendsDecision:
    """Studio: change opening; cascade closing per R-BE-14."""
    from travelogue.cover_engine.joint import (
        apply_joint_pick,
        apply_style_keep_cover,
        repick_cover_for_style,
    )
    from travelogue.cover_engine.lock import set_opening_locked
    from travelogue.cover_engine.pairing.policy import pairing_hard_violations
    from travelogue.cover_engine.types import CoverJointExplain
    from travelogue.domain.closing_view import cover_ids_to_exclude

    layout_name = layout or trip.get("exportLayout") or "auto"
    meta = trip.setdefault("meta", {})
    curation = trip.setdefault("curation", {})
    style = (style_id or str(meta.get("coverOpeningStyle") or "")).strip()
    aid = (asset_id or "").strip()

    if style and keep_cover:
        apply_style_keep_cover(trip, style)
    elif style and not aid:
        repick_cover_for_style(trip, style, layout="web")
    elif aid:
        if style:
            meta["coverOpeningStyle"] = style
        explain = CoverJointExplain(
            source="manual",
            style_id=str(meta.get("coverOpeningStyle") or style or ""),
            asset_id=aid,
            low_confidence=False,
        )
        apply_joint_pick(trip, explain, lock=True, layout="web")
    else:
        raise ValueError("assetId or styleId required")

    set_opening_locked(trip, True)

    # Cascade vs current closing
    closing_raw = curation.get("closingAssetId") if "closingAssetId" in curation else None
    closing_id = str(closing_raw).strip() if closing_raw else ""
    toast = None
    if closing_id:
        assets_map = {
            str(a.get("id")): a
            for a in (trip.get("assets") or [])
            if isinstance(a, dict) and a.get("id")
        }
        cover_id = next(iter(cover_ids_to_exclude(trip)), "")
        cover = assets_map.get(cover_id)
        closing_asset = assets_map.get(closing_id)
        viol = pairing_hard_violations(cover, closing_asset) if closing_asset else []
        if viol:
            user_picked = bool(curation.get("closingUserPicked"))
            if user_picked and not confirm_closing_conflict:
                raise ClosingConflictError(
                    "closing conflicts with new cover",
                    violations=viol,
                )
            # Auto re-resolve closing
            try:
                resolve_closing(trip, layout=layout_name, force=True, persist=True)
                toast = "已为你重选封底"
                curation["closingUserPicked"] = False
            except ClosingPendingError:
                pass

    decision = build_bookends_studio_payload(trip)
    # Return as BookendsDecision via snapshot fields
    snap = _decision_from_trip(
        trip,
        cover_asset_id=str(trip.get("coverAssetId") or ""),
        closing_pending=bool(decision.get("closingPending")),
        closing_asset_id=decision.get("closingAssetId"),
        closing_style_id=decision.get("closingStyleId"),
        degraded=bool(decision.get("degraded")),
        explain={
            **(decision.get("explain") or {}),
            "cascadeToast": toast,
            "phase": "repick-opening",
        },
        telemetry=decision.get("telemetry") or {},
    )
    return snap


def repick_closing(
    trip: dict,
    *,
    asset_id: str | None = None,
    layout: str | None = None,
) -> BookendsDecision:
    """Studio: set closing asset (user picked) or auto-resolve."""
    from travelogue.cover_engine.lock import set_closing_locked
    from travelogue.domain.closing_view import cover_ids_to_exclude

    layout_name = layout or trip.get("exportLayout") or "auto"
    curation = trip.setdefault("curation", {})
    aid = (asset_id or "").strip()
    if aid:
        if aid in cover_ids_to_exclude(trip):
            raise ValueError("closing cannot reuse cover")
        curation["closingAssetId"] = aid
        curation["closingUserPicked"] = True
        curation.pop("bookendsDegraded", None)
        meta = trip.setdefault("meta", {})
        meta["coverClosingStyle"] = "colophon-default"
        set_closing_locked(trip, True)
        sync_lock_mirrors(trip)
        return _decision_from_trip(
            trip,
            cover_asset_id=str(trip.get("coverAssetId") or ""),
            closing_pending=False,
            closing_asset_id=aid,
            closing_style_id="colophon-default",
            degraded=False,
            explain={
                "phase": "repick-closing",
                "userOneLiner": "已按你的选择固定封底。",
                "closingUserPicked": True,
            },
            telemetry={},
        )
    curation.pop("closingUserPicked", None)
    return resolve_closing(trip, layout=layout_name, force=True, persist=True)
