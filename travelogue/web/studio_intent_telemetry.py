"""Local studio intent telemetry (PRD-PHASE4 §13 · AC-P4-TEL-01)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_studio_intent_telemetry(
    trip: dict,
    *,
    tier_mode: str | None = None,
    g1_pending: bool = False,
    g1_confirmed: bool = False,
) -> dict[str, Any]:
    intent = trip.get("intent") or {}
    travel_plan = intent.get("travelPlan") or {}
    assets = trip.get("assets") or []
    featured_count = sum(1 for a in assets if a.get("userTier") == "featured")
    user_notes = str(trip.get("userNotes") or intent.get("userNotes") or "").strip()
    anchor_count = 0
    for ch in trip.get("chapters") or []:
        anchors = (ch.get("curation") or {}).get("memoryAnchors") or []
        anchor_count += len([a for a in anchors if str(a).strip()])
    plan_path = (trip.get("curation") or {}).get("intentHints") or {}
    has_plan_cities = bool(plan_path.get("planCities") or travel_plan.get("cities"))
    return {
        "recordedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tripId": trip.get("tripId"),
        "hasUserNotes": bool(user_notes),
        "featuredCount": featured_count,
        "tierMode": tier_mode or "single",
        "planUploaded": bool(travel_plan) or has_plan_cities,
        "g1Pending": bool(g1_pending),
        "g1Confirmed": bool(g1_confirmed),
        "anchorCount": anchor_count,
        "intentTitle": str(intent.get("title") or (trip.get("meta") or {}).get("title") or "")[:20],
    }


def write_studio_intent_telemetry(
    trip: dict,
    trip_dir: Path,
    *,
    tier_mode: str | None = None,
    g1_pending: bool = False,
    g1_confirmed: bool = False,
) -> Path:
    payload = build_studio_intent_telemetry(
        trip,
        tier_mode=tier_mode,
        g1_pending=g1_pending,
        g1_confirmed=g1_confirmed,
    )
    runs_dir = trip_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    dest = runs_dir / "studio-intent.json"
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest
