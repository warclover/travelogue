"""Template router MVP — manual > smart > fallback (PRD §4.2)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

_log = logging.getLogger(__name__)

from travelogue.config import AppConfig, get_config
from travelogue.templates.registry import (
    DEFAULT_TEMPLATE_ID,
    check_template_health,
    get_registry,
)
from travelogue.templating.resolver import is_template_locked, sync_template_id_mirror

RouterMode = Literal["smart", "manual"]
ROUTER_VERSION = "p13-r1"
ROUTER_CONFIG_VERSION = "cfg-2026-06-03-01"
FEATURE_SNAPSHOT_VERSION = "feat-v1"

REASON_MANUAL = "R_MANUAL_OVERRIDE"
REASON_LOW_CONFIDENCE = "R_LOW_CONFIDENCE_FALLBACK"
REASON_DISABLED = "R_TEMPLATE_DISABLED_FALLBACK"
REASON_MULTI_DAY = "R_ROUTE_MULTI_DAY"
REASON_EVENT_VIDEO = "R_EVENT_VIDEO_HEAVY"
REASON_PERSON_HEAVY = "R_PERSON_RATIO_HIGH"
REASON_EVENT_KEYWORDS = "R_CAPTION_EVENT_KEYWORDS"
REASON_GEO_SPARSE = "R_GEO_CONTINUITY_LOW"
EVENT_KEYWORDS = frozenset({"活动", "婚礼", "年会", "派对", "event", "wedding", "party", "concert"})


def _cfg_router(cfg: AppConfig | None) -> Any:
    from dataclasses import replace

    from travelogue.templating.admin_store import load_runtime

    app = cfg or get_config()
    tr = app.template_router
    rt = load_runtime()
    if rt.get("template_router_enabled") is False:
        tr = replace(tr, enabled=False)
    allowed = rt.get("allowed_templates")
    if isinstance(allowed, list) and allowed:
        tr = replace(tr, allowed_templates=tuple(str(x) for x in allowed))
    rec = rt.get("recommended_templates")
    if isinstance(rec, list) and rec:
        tr = replace(tr, display_order=tuple(str(x) for x in rec))
    return tr


def _gray_traffic_allows(trip_id: str, *, cfg: AppConfig | None) -> bool:
    from travelogue.templating.admin_store import load_runtime

    rt = load_runtime()
    pct = float(rt.get("traffic_percent") or 100)
    if pct >= 100:
        return True
    if pct <= 0:
        return False
    if not trip_id:
        return False
    bucket = int(hashlib.sha256(trip_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return bucket < pct


def compute_decision_hash(selection: dict[str, Any]) -> str:
    payload = {
        "mode": selection.get("mode"),
        "requestedTemplateId": selection.get("requestedTemplateId"),
        "resolvedTemplateId": selection.get("resolvedTemplateId"),
        "reasonCodes": sorted(selection.get("reasonCodes") or []),
        "routerVersion": selection.get("routerVersion"),
        "routerConfigVersion": selection.get("routerConfigVersion"),
        "featureSnapshotVersion": selection.get("featureSnapshotVersion"),
        "registryVersion": selection.get("registryVersion"),
        "fallbackUsed": selection.get("fallbackUsed"),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _trip_day_span(trip: dict) -> int:
    meta = trip.get("meta") or {}
    start = str(meta.get("dateStart") or "")
    end = str(meta.get("dateEnd") or "")
    if not start or not end or start == end:
        return 1
    try:
        from datetime import date

        d0 = date.fromisoformat(start[:10])
        d1 = date.fromisoformat(end[:10])
        return max(1, (d1 - d0).days + 1)
    except ValueError:
        return 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _person_ratio(trip: dict) -> float:
    assets = trip.get("assets") or []
    if not assets:
        return 0.0
    people = 0
    for a in assets:
        tags = (a.get("curation") or {}).get("subjectTags") or []
        blob = " ".join(str(t).lower() for t in tags)
        if any(k in blob for k in ("person", "people", "face", "人像", "人物")):
            people += 1
    return people / len(assets)


def _event_keyword_hit(trip: dict) -> bool:
    for a in trip.get("assets") or []:
        cap = str(a.get("caption") or a.get("title") or "").lower()
        if any(k in cap for k in EVENT_KEYWORDS):
            return True
    notes = str((trip.get("meta") or {}).get("subtitle") or "")
    return any(k in notes.lower() for k in EVENT_KEYWORDS)


def _geo_continuity_score(trip: dict) -> float:
    assets = trip.get("assets") or []
    if not assets:
        return 0.0
    from travelogue.templating.l3_validate import _asset_has_geo

    geo = sum(1 for a in assets if _asset_has_geo(a))
    return geo / len(assets)


def extract_trip_features(trip: dict) -> dict[str, Any]:
    """Routing feature snapshot for replay / admin (PRD §5.11)."""
    return {
        "daySpan": _trip_day_span(trip),
        "placeCount": len((trip.get("meta") or {}).get("places") or []),
        "videoRatio": round(_video_ratio(trip), 4),
        "personRatio": round(_person_ratio(trip), 4),
        "eventKeywordHit": _event_keyword_hit(trip),
        "geoContinuity": round(_geo_continuity_score(trip), 4),
        "assetCount": len(trip.get("assets") or []),
    }


def _video_ratio(trip: dict) -> float:
    assets = trip.get("assets") or []
    if not assets:
        return 0.0
    videos = sum(1 for a in assets if str(a.get("type") or "").lower() == "video")
    return videos / len(assets)


def _route_smart(trip: dict, *, cfg: AppConfig | None) -> tuple[str, float, list[str], bool]:
    tr = _cfg_router(cfg)
    default = tr.default_template or DEFAULT_TEMPLATE_ID
    threshold = float(tr.confidence_threshold)
    reg = get_registry()

    days = _trip_day_span(trip)
    places = trip.get("meta", {}).get("places") or []
    video_ratio = _video_ratio(trip)
    person_ratio = _person_ratio(trip)
    geo_score = _geo_continuity_score(trip)
    event_kw = _event_keyword_hit(trip)

    trip_id = str(trip.get("tripId") or "")
    if event_kw or (days <= 1 and video_ratio >= 0.35):
        candidate = "event-recap"
        confidence = 0.8 if event_kw else 0.78
        reasons = [REASON_EVENT_KEYWORDS if event_kw else REASON_EVENT_VIDEO]
    elif days >= 2 and len(places) >= 2 and geo_score >= 0.2:
        candidate = DEFAULT_TEMPLATE_ID
        confidence = 0.85
        reasons = [REASON_MULTI_DAY]
    elif person_ratio >= 0.45 and days <= 2:
        candidate = "event-recap"
        confidence = 0.72
        reasons = [REASON_PERSON_HEAVY]
    elif days >= 2 and len(places) >= 2:
        candidate = DEFAULT_TEMPLATE_ID
        confidence = 0.78
        reasons = [REASON_MULTI_DAY, REASON_GEO_SPARSE]
    else:
        candidate = default
        confidence = 0.55
        reasons = [REASON_LOW_CONFIDENCE]

    fallback_used = False
    if candidate != default and not _gray_traffic_allows(trip_id, cfg=cfg):
        candidate = default
        fallback_used = True
        reasons = list(reasons) + [REASON_LOW_CONFIDENCE]
        confidence = min(confidence, threshold - 0.05)
    try:
        reg.get(candidate)
        healthy, _ = check_template_health(candidate)
        if not healthy:
            raise KeyError
    except Exception:
        candidate = default
        confidence = min(confidence, threshold - 0.01)
        reasons = [REASON_DISABLED if REASON_EVENT_VIDEO in reasons else REASON_LOW_CONFIDENCE]
        fallback_used = True

    if confidence < threshold:
        if candidate != default:
            fallback_used = True
        candidate = default
        if REASON_LOW_CONFIDENCE not in reasons:
            reasons.append(REASON_LOW_CONFIDENCE)

    return candidate, confidence, reasons, fallback_used


def route_template(
    trip: dict,
    *,
    mode: RouterMode = "smart",
    requested_template_id: str | None = None,
    cfg: AppConfig | None = None,
) -> dict[str, Any]:
    """Compute template decision without mutating trip."""
    from travelogue.templating.metrics import RouteTimer, record_route_decision, record_template_metric

    timer = RouteTimer()
    tr = _cfg_router(cfg)
    reg = get_registry()
    default = tr.default_template or DEFAULT_TEMPLATE_ID
    reason_codes: list[str] = []
    fallback_used = False
    confidence = 1.0

    allowed = set(tr.allowed_templates or (default,))

    if not tr.enabled:
        resolved = default
        reason_codes = [REASON_LOW_CONFIDENCE]
        fallback_used = True
        confidence = 1.0
    elif mode == "manual" and requested_template_id:
        resolved = requested_template_id.strip()
        reason_codes = [REASON_MANUAL]
        if resolved not in allowed:
            resolved = default
            fallback_used = True
            reason_codes = [REASON_MANUAL, REASON_DISABLED]
        else:
            try:
                reg.get(resolved)
                healthy, _ = check_template_health(resolved)
                if not healthy:
                    raise KeyError
            except Exception:
                resolved = default
                fallback_used = True
                reason_codes = [REASON_MANUAL, REASON_DISABLED]
    elif mode == "smart":
        resolved, confidence, reason_codes, fallback_used = _route_smart(trip, cfg=cfg)
        if resolved not in allowed:
            resolved = default
            fallback_used = True
            reason_codes = list(reason_codes) + [REASON_DISABLED]
    else:
        resolved, confidence, reason_codes, fallback_used = _route_smart(trip, cfg=cfg)
        if resolved not in allowed:
            resolved = default
            fallback_used = True

    selection: dict[str, Any] = {
        "mode": mode,
        "requestedTemplateId": requested_template_id if mode == "manual" else None,
        "resolvedTemplateId": resolved,
        "confidence": round(confidence, 4),
        "reasonCodes": reason_codes,
        "fallbackUsed": fallback_used,
        "routerVersion": ROUTER_VERSION,
        "routerConfigVersion": ROUTER_CONFIG_VERSION,
        "featureSnapshotVersion": FEATURE_SNAPSHOT_VERSION,
        "registryVersion": reg.version,
        "locked": is_template_locked(trip),
        "lockedAt": (trip.get("templateSelection") or {}).get("lockedAt"),
    }
    selection["decisionHash"] = compute_decision_hash(selection)
    from travelogue.templating.shadow import apply_shadow_overlay

    selection = apply_shadow_overlay(selection, cfg=cfg)
    selection["decisionHash"] = compute_decision_hash(selection)
    record_route_decision(
        trip_id=str(trip.get("tripId") or ""),
        template_id=str(selection.get("resolvedTemplateId") or default),
        mode=str(selection.get("mode") or mode),
        confidence=float(selection.get("confidence") or 0),
        fallback_used=bool(selection.get("fallbackUsed")),
        duration_ms=timer.elapsed_ms,
    )
    record_template_metric(
        "template.route.count",
        templateId=str(selection.get("resolvedTemplateId") or default),
    )
    return selection


def apply_template_selection(
    trip: dict,
    *,
    mode: RouterMode = "smart",
    requested_template_id: str | None = None,
    cfg: AppConfig | None = None,
    recompute: bool = False,
    trip_dir: Path | None = None,
    log_action: str = "apply",
) -> dict[str, Any]:
    """Write templateSelection; respect freeze rules."""
    existing = trip.get("templateSelection") or {}
    if is_template_locked(trip) and existing.get("resolvedTemplateId") and not recompute:
        return existing
    if not recompute and existing.get("resolvedTemplateId"):
        if existing.get("mode") == "manual":
            return existing
    if is_template_locked(trip) and recompute:
        _log.info("template recompute blocked: trip locked %s", trip.get("tripId"))
        return existing

    selection = route_template(
        trip,
        mode=mode,
        requested_template_id=requested_template_id,
        cfg=cfg,
    )
    if is_template_locked(trip):
        selection["locked"] = True
        if not selection.get("lockedAt"):
            selection["lockedAt"] = existing.get("lockedAt") or _utc_now()
    trip["templateSelection"] = selection
    sync_template_id_mirror(trip)
    if trip_dir is not None:
        from travelogue.templating.decision_log import append_decision

        append_decision(
            trip_dir,
            trip_id=str(trip.get("tripId") or trip_dir.name),
            action=log_action,
            selection=selection,
            extra={"recompute": recompute},
        )
    return selection


def template_user_feedback(selection: dict[str, Any]) -> dict[str, str]:
    """C 端创建结果文案（smart / manual / fallback）。"""
    sel = selection or {}
    tid = str(sel.get("resolvedTemplateId") or DEFAULT_TEMPLATE_ID)
    labels = {"visual-journal": "视觉游记", "event-recap": "活动回顾"}
    label = labels.get(tid, tid)
    if sel.get("fallbackUsed"):
        return {
            "kind": "fallback",
            "message": "已回退到默认模板（视觉游记）",
            "templateId": tid,
        }
    if sel.get("mode") == "manual":
        return {"kind": "manual", "message": f"已使用：{label}", "templateId": tid}
    return {"kind": "smart", "message": f"已为你匹配：{label}", "templateId": tid}


def replay_template_decision(trip: dict, *, cfg: AppConfig | None = None) -> dict[str, Any]:
    """Re-run router with stored mode/requested id; compare to stored hash."""
    sel = trip.get("templateSelection") or {}
    mode = sel.get("mode") or "smart"
    requested = sel.get("requestedTemplateId")
    fresh = route_template(trip, mode=mode, requested_template_id=requested, cfg=cfg)
    stored_hash = sel.get("decisionHash")
    fresh_hash = fresh.get("decisionHash")
    features = extract_trip_features(trip)
    return {
        "stored": sel,
        "replayed": fresh,
        "features": features,
        "featureSummary": (
            f"跨度 {features['daySpan']} 天 · {features['placeCount']} 地 · "
            f"视频占比 {int(features['videoRatio'] * 100)}%"
        ),
        "match": stored_hash == fresh_hash if stored_hash else None,
        "storedHash": stored_hash,
        "replayedHash": fresh_hash,
    }
