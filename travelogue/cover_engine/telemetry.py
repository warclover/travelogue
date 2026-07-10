"""Cover joint telemetry (API-CSE-17)."""

from __future__ import annotations

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
