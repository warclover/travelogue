"""Featured-subject cohort helpers for Studio API and intent writes."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

_SUBJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")


def normalize_featured_subjects(raw: Any) -> list[dict[str, Any]]:
    """Validate and normalize ``intent.featuredSubjects`` payload."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("featuredSubjects must be an array")
    if len(raw) > 4:
        raise ValueError("featuredSubjects max 4 entries")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("featuredSubjects entries must be objects")
        sid = str(item.get("id") or "").strip().lower()
        if not sid or not _SUBJECT_ID_RE.match(sid):
            raise ValueError(
                "featuredSubjects.id must match ^[a-z][a-z0-9-]{0,31}$"
            )
        if sid in seen:
            raise ValueError(f"duplicate featuredSubjects id: {sid}")
        seen.add(sid)
        seeds_raw = item.get("seedAssetIds") or item.get("seed_asset_ids") or []
        if not isinstance(seeds_raw, list):
            raise ValueError("seedAssetIds must be an array")
        seed_ids = []
        for s in seeds_raw:
            aid = str(s).strip()
            if aid and aid not in seed_ids:
                seed_ids.append(aid)
        if not seed_ids:
            raise ValueError(f"featuredSubjects[{sid}] needs at least one seedAssetId")
        if len(seed_ids) > 12:
            raise ValueError(f"featuredSubjects[{sid}] max 12 seedAssetIds")
        label = str(item.get("label") or sid).strip()[:16] or sid
        out.append({"id": sid, "label": label, "seedAssetIds": seed_ids})
    return out


def validate_seeds_exist(subjects: list[dict], assets_by_id: Mapping[str, dict]) -> None:
    for subj in subjects:
        for aid in subj.get("seedAssetIds") or []:
            asset = assets_by_id.get(aid)
            if not asset:
                raise ValueError(f"unknown seed asset: {aid}")
            if asset.get("type") != "image":
                raise ValueError(f"seed asset must be image: {aid}")


def suggest_seed_asset_ids(
    trip: dict,
    *,
    subject_id: str,
    limit: int = 8,
) -> list[str]:
    """Heuristic seed candidates: faces detected, not already used as seeds."""
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    subjects = (trip.get("intent") or {}).get("featuredSubjects") or []
    used: set[str] = set()
    for subj in subjects:
        if not isinstance(subj, dict):
            continue
        for aid in subj.get("seedAssetIds") or []:
            used.add(str(aid))

    rows: list[tuple[float, str]] = []
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image" or not asset.get("layoutEligible", True):
            continue
        aid = asset.get("id")
        if not aid or aid in used:
            continue
        q = asset.get("quality") or {}
        if int(q.get("faceCount") or 0) < 1:
            continue
        sharp = float(q.get("sharpness") or 0.0)
        kind = aspect_kind_for_asset(asset)
        bonus = 0.1 if kind in ("portrait", "tall") else 0.0
        rows.append((sharp + bonus, str(aid)))
    rows.sort(key=lambda x: (-x[0], x[1]))
    return [aid for _s, aid in rows[:limit]]


def build_cohort_studio_payload(trip: dict, *, cohort_enabled: bool) -> dict[str, Any]:
    """GET /trips/{id}/cohort response body (without ok wrapper)."""
    from travelogue.curation.cohort_faces import featured_subjects_from_trip

    intent = trip.get("intent") or {}
    subjects = featured_subjects_from_trip(trip)
    summary = (trip.get("curation") or {}).get("cohort")
    assets_out: list[dict[str, Any]] = []
    for asset in trip.get("assets") or []:
        if asset.get("type") != "image":
            continue
        aid = asset.get("id")
        if not aid:
            continue
        q = asset.get("quality") or {}
        cohort = (asset.get("curation") or {}).get("cohort") or {}
        assets_out.append(
            {
                "id": aid,
                "displayFile": asset.get("displayFile"),
                "takenAt": asset.get("takenAt"),
                "faceCount": int(q.get("faceCount") or cohort.get("faceCount") or 0),
                "duo": bool(cohort.get("duo")),
                "confidence": cohort.get("confidence"),
                "method": cohort.get("method"),
                "subjectsPresent": list(cohort.get("subjectsPresent") or []),
                "userTier": asset.get("userTier"),
            }
        )
    suggestions: dict[str, list[str]] = {}
    for subj in subjects:
        suggestions[subj["id"]] = suggest_seed_asset_ids(trip, subject_id=subj["id"])
    return {
        "enabled": cohort_enabled,
        "featuredSubjects": subjects or intent.get("featuredSubjects") or [],
        "summary": summary,
        "assets": assets_out,
        "suggestedSeeds": suggestions,
    }
