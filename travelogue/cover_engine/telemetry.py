"""Cover joint + Bookends telemetry (API-CSE-17 / PRD §9)."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.types import CoverJointExplain


def record_cover_joint_event(
    trip_id: str,
    explain: CoverJointExplain,
    *,
    locked: bool = False,
) -> None:
    """Best-effort jsonl event; never raises to callers."""
    if not trip_id:
        return
    try:
        from travelogue.services.studio_homepage_telemetry import append_studio_homepage_event

        append_studio_homepage_event(
            "cover_joint_pick",
            {
                "tripId": trip_id,
                "source": explain.source,
                "coverOpeningStyle": explain.style_id,
                "coverAssetId": explain.asset_id,
                "joint": explain.joint,
                "quality": explain.quality,
                "fit": explain.fit,
                "avoidPenalty": explain.avoid_penalty,
                "lowConfidence": explain.low_confidence,
                "locked": locked,
            },
        )
    except Exception:
        pass


def record_bookends_event(trip_id: str, event: str, payload: dict[str, Any]) -> None:
    """Best-effort bookends telemetry shell; never raises."""
    if not trip_id:
        return
    try:
        from travelogue.services.studio_homepage_telemetry import append_studio_homepage_event

        body = dict(payload)
        body["tripId"] = trip_id
        append_studio_homepage_event(event, body)
    except Exception:
        pass


def write_bookends_telemetry(trip: dict, telemetry: dict[str, Any]) -> None:
    """Persist curation.bookendsTelemetry snapshot (PRD §9)."""
    curation = trip.setdefault("curation", {})
    if not isinstance(curation, dict):
        return
    prev = curation.get("bookendsTelemetry")
    merged = dict(prev) if isinstance(prev, dict) else {}
    merged.update(telemetry)
    curation["bookendsTelemetry"] = merged
