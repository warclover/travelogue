"""Share Narrative Readiness · album-level narrativePosture (SNR D-SNR-01/02)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.domain.share_face_copy import sanitize_share_copy

NarrativePosture = Literal["photo_led", "upgrade_ready", "narrative_ready"]

POSTURE_PHOTO_LED: NarrativePosture = "photo_led"
POSTURE_UPGRADE_READY: NarrativePosture = "upgrade_ready"
POSTURE_NARRATIVE_READY: NarrativePosture = "narrative_ready"


def _nonempty_safe(text: str | None, *, title: str | None, kind: str) -> bool:
    return bool(sanitize_share_copy(text, title=title, kind=kind))


def has_reader_narrative(trip: dict[str, Any] | None) -> bool:
    """True when album has a non-empty, share-safe hook or chapter lead."""
    trip = trip if isinstance(trip, dict) else None
    if not trip:
        return False
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    title = str(meta.get("displayTitle") or meta.get("title") or "").strip() or None
    if _nonempty_safe(meta.get("hook"), title=title, kind="lead"):
        return True
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("curation") or {}).get("isAppendix"):
            continue
        if _nonempty_safe(ch.get("lead") or ch.get("intro"), title=title, kind="lead"):
            return True
    return False


def resolve_narrative_posture(
    trip: dict[str, Any] | None,
    *,
    ai_surface_enabled: bool = False,
    llm_ready: bool = False,
) -> NarrativePosture:
    """D-SNR-01 · album posture for chrome banner / upgrade CTA.

    - narrative_ready: safe hook or ≥1 chapter lead
    - upgrade_ready: not ready, AI surface on, writing engine ready
    - photo_led: otherwise (incl. NAS / no Key)
    """
    if has_reader_narrative(trip):
        return POSTURE_NARRATIVE_READY
    if ai_surface_enabled and llm_ready:
        return POSTURE_UPGRADE_READY
    return POSTURE_PHOTO_LED


def trip_primary_year(trip: dict[str, Any] | None) -> int | None:
    """Majority calendar year for the trip (meta dates, else asset takenAt mode)."""
    from datetime import datetime

    trip = trip if isinstance(trip, dict) else None
    if not trip:
        return None
    years: list[int] = []
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    for key in ("dateStart", "dateEnd"):
        raw = str(meta.get(key) or "")[:10]
        if len(raw) >= 4 and raw[:4].isdigit():
            years.append(int(raw[:4]))
    if years:
        # Prefer span mid / start year when meta present
        return years[0] if len(years) == 1 else years[0]

    counts: dict[int, int] = {}
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        taken = str(asset.get("takenAt") or "")
        if not taken:
            continue
        try:
            y = datetime.fromisoformat(taken.replace("Z", "+00:00")).year
        except ValueError:
            continue
        counts[y] = counts.get(y, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def photo_year_is_outlier(
    taken_at: str | None,
    primary_year: int | None,
    *,
    min_delta: int = 2,
) -> bool:
    """D-SNR-05 · |photoYear - tripPrimaryYear| ≥ 2."""
    from datetime import datetime

    if primary_year is None or not taken_at:
        return False
    try:
        y = datetime.fromisoformat(str(taken_at).replace("Z", "+00:00")).year
    except ValueError:
        return False
    return abs(y - int(primary_year)) >= int(min_delta)
