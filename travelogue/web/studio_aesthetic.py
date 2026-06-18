"""Studio · PA aesthetic explain payload (PA-T10 · P4-1/P4-2).

Read-only helpers over ``trip.json`` assets — never mutates the trip.
"""

from __future__ import annotations

from typing import Any

from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset
from travelogue.curation.aesthetic_score import asset_aesthetic, build_aesthetic_explain, purpose_overall
from travelogue.curation.album_profile import (
    album_profile_for_trip,
    stratum_preference_for_trip,
    stratum_selection_hint,
)
from travelogue.curation.algorithm_profile import assess_algorithm_freshness

_STRATUM_LABELS: dict[str, str] = {
    "person": "人像",
    "landscape": "风景",
    "food": "美食",
    "group": "合影",
    "general": "通用",
}

_PURPOSE_LABELS: dict[str, str] = {
    "cover": "封面",
    "hero": "主图",
    "moment": "瞬间",
}

_STRATUM_PREFERENCE_OPTIONS: tuple[dict[str, str], ...] = (
    {"value": "auto", "label": "自动"},
    {"value": "landscape", "label": "更偏风景"},
    {"value": "portrait", "label": "更偏人像"},
)


def _aesthetic_cfg():
    from travelogue.config import get_config

    return get_config().aesthetic


def _purpose_scores_for_asset(asset: dict) -> dict[str, float]:
    cfg = _aesthetic_cfg()
    out: dict[str, float] = {}
    for purpose in ("cover", "hero", "moment"):
        score = purpose_overall(asset, purpose, cfg=cfg)  # type: ignore[arg-type]
        if score is not None:
            out[purpose] = round(float(score), 4)
    return out


def build_stratum_preference_studio_summary(trip: dict) -> dict[str, Any]:
    """User stratum bias preset for Studio (P4-3)."""
    value = stratum_preference_for_trip(trip)
    profile = album_profile_for_trip(trip)
    label = next(
        (opt["label"] for opt in _STRATUM_PREFERENCE_OPTIONS if opt["value"] == value),
        value,
    )
    return {
        "value": value,
        "label": label,
        "selectionHint": stratum_selection_hint(profile, preference=value),
        "recurateHint": "修改后重新「精选照片」可应用偏好",
        "options": [dict(opt) for opt in _STRATUM_PREFERENCE_OPTIONS],
    }


def build_album_profile_studio_summary(trip: dict) -> dict[str, Any]:
    """Compact albumProfile for Studio (P4-2)."""
    profile = album_profile_for_trip(trip)
    dominant = str(profile.get("dominantStratum") or "general")
    strata = profile.get("strata") if isinstance(profile.get("strata"), dict) else {}
    strata_pct = {
        k: round(float(v) * 100.0, 1) for k, v in strata.items() if v is not None
    }
    return {
        "dominantStratum": dominant,
        "dominantLabel": _STRATUM_LABELS.get(dominant, dominant),
        "isSkewed": bool(profile.get("isSkewed")),
        "eligibleImages": profile.get("eligibleImages"),
        "strata": strata,
        "strataPct": strata_pct,
        "strataLabels": {k: _STRATUM_LABELS.get(k, k) for k in strata},
    }


def displayed_asset_ids(trip: dict) -> list[str]:
    """Asset ids referenced by chapter screens, in document order (deduped)."""
    ids: list[str] = []
    seen: set[str] = set()
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if not aid:
                    continue
                key = str(aid)
                if key in seen:
                    continue
                seen.add(key)
                ids.append(key)
    return ids


def build_asset_aesthetic_studio_row(
    asset: dict,
    *,
    limit: int = 3,
    include_purpose_scores: bool = True,
) -> dict[str, Any] | None:
    """One asset row for Studio (overall + stratum + purpose + top dimensions)."""
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    aid = asset.get("id")
    if not aid:
        return None
    explain = build_aesthetic_explain(asset, limit=limit)
    stratum = review_stratum_for_asset(asset)
    row: dict[str, Any] = {
        "id": str(aid),
        "displayFile": asset.get("displayFile"),
        "overall": ae.get("overall"),
        "confidence": ae.get("confidence"),
        "source": ae.get("source"),
        "stratum": stratum,
        "stratumLabel": _STRATUM_LABELS.get(stratum, stratum),
        "explain": explain,
    }
    dims = ae.get("dims")
    if isinstance(dims, dict) and dims:
        row["dims"] = dims
    signals = ae.get("signals") if isinstance(ae.get("signals"), dict) else {}
    if signals.get("mllmScore") is not None:
        row["mllmScore"] = signals.get("mllmScore")
    critique = ae.get("critique")
    if isinstance(critique, str) and critique.strip():
        row["critique"] = critique.strip()
    elif isinstance(critique, dict) and critique:
        row["critique"] = critique
    if include_purpose_scores:
        purposes = _purpose_scores_for_asset(asset)
        if purposes:
            row["purposes"] = purposes
            row["purposeLabels"] = dict(_PURPOSE_LABELS)
    return row


def _aesthetic_stale_hint(*, enabled: bool, image_count: int, scored_count: int) -> str | None:
    if enabled and image_count > 0 and scored_count == 0:
        return "审美评分未生成，请重新导入照片以应用封面/排版优化"
    return None


def build_aesthetic_entry_summary(
    trip: dict,
    *,
    enabled: bool,
    trip_dir: Any = None,
) -> dict[str, Any]:
    """Compact counts for ``GET …/entry`` (no per-asset explain)."""
    assets = trip.get("assets") or []
    images = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
    scored = sum(1 for a in images if asset_aesthetic(a))
    displayed = displayed_asset_ids(trip)
    displayed_scored = 0
    if displayed:
        by_id = {str(a["id"]): a for a in images}
        displayed_scored = sum(
            1 for aid in displayed if asset_aesthetic(by_id.get(aid) or {})
        )
    freshness = assess_algorithm_freshness(trip, trip_dir)
    aesthetic_stale = enabled and len(images) > 0 and scored == 0
    stale = aesthetic_stale or bool(freshness.get("algorithmStale"))
    if aesthetic_stale:
        stale_hint = _aesthetic_stale_hint(
            enabled=enabled,
            image_count=len(images),
            scored_count=scored,
        )
    else:
        stale_hint = freshness.get("staleHint")
    summary: dict[str, Any] = {
        "enabled": enabled,
        "scoredCount": scored,
        "displayedCount": len(displayed),
        "displayedScoredCount": displayed_scored,
        "stale": stale,
        "staleHint": stale_hint,
        "algorithmStale": bool(freshness.get("algorithmStale")),
        "aestheticStale": bool(freshness.get("aestheticStale")),
        "cullStale": bool(freshness.get("cullStale")),
        "layoutStale": bool(freshness.get("layoutStale")),
        "previewStale": bool(freshness.get("previewStale")),
        "staleHints": freshness.get("staleHints") or [],
    }
    if enabled and images:
        ap = build_album_profile_studio_summary(trip)
        summary["albumProfile"] = {
            "dominantStratum": ap.get("dominantStratum"),
            "dominantLabel": ap.get("dominantLabel"),
            "isSkewed": ap.get("isSkewed"),
        }
        summary["stratumPreference"] = build_stratum_preference_studio_summary(trip)
    return summary


def build_aesthetic_studio_payload(
    trip: dict,
    *,
    enabled: bool = True,
    asset_ids: list[str] | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    """GET /trips/{id}/aesthetic response body (without ``ok`` wrapper)."""
    assets = trip.get("assets") or []
    by_id = {str(a["id"]): a for a in assets if a.get("id")}
    want = asset_ids if asset_ids is not None else displayed_asset_ids(trip)
    if not want:
        want = list(by_id.keys())

    rows: list[dict[str, Any]] = []
    for aid in want:
        asset = by_id.get(str(aid))
        if not asset or asset.get("type") == "video":
            continue
        row = build_asset_aesthetic_studio_row(asset, limit=limit)
        if row:
            rows.append(row)

    cover_explain = (trip.get("curation") or {}).get("coverExplain") or []
    images = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
    scored_count = sum(1 for a in images if asset_aesthetic(a))
    stale = enabled and len(images) > 0 and scored_count == 0
    payload: dict[str, Any] = {
        "enabled": enabled,
        "scoredCount": scored_count,
        "stale": stale,
        "staleHint": _aesthetic_stale_hint(
            enabled=enabled,
            image_count=len(images),
            scored_count=scored_count,
        ),
        "assets": rows,
        "coverExplain": cover_explain if isinstance(cover_explain, list) else [],
        "purposeLabels": dict(_PURPOSE_LABELS),
        "stratumLabels": dict(_STRATUM_LABELS),
    }
    if enabled and images:
        payload["albumProfile"] = build_album_profile_studio_summary(trip)
        payload["stratumPreference"] = build_stratum_preference_studio_summary(trip)
    return payload
