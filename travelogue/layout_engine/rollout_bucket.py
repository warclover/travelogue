"""Deterministic rollout bucketing (layout_engine)."""

from __future__ import annotations

import hashlib


def rollout_bucket(trip_id: str, *, cohort_salt: str, traffic_percent: float) -> int:
    """Deterministic bucket 0..99 for trip_id (stable across runs)."""
    if traffic_percent <= 0:
        return 100
    if traffic_percent >= 100:
        return 0
    digest = hashlib.sha256(f"{cohort_salt}:{trip_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100
