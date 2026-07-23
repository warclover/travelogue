"""SSG M2 · look boundary splitting from appearance distances (pure logic)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

import numpy as np

from travelogue.vision.look_appearance import appearance_distance


def _parse_taken_at(raw: Any) -> datetime:
    if raw is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def split_look_segments(
    assets: Sequence[dict],
    vectors: Mapping[str, np.ndarray],
    *,
    delta_threshold: float,
    sustain_frames: int,
) -> list[list[dict]]:
    """Split look-eligible assets (time-ordered) into look segments.

    Distance is measured against the **current look reference** (first frame of
    the open segment), not only the previous frame. A candidate streak of
    ``sustain_frames`` frames with Δ≥threshold commits a new look; a shorter
    streak is absorbed (flash rejection · D-SSG-09 / AC-SSG-12).
    """
    eligible = [a for a in assets if str(a.get("id") or "") in vectors]
    if not eligible:
        return []
    ordered = sorted(
        eligible,
        key=lambda a: (_parse_taken_at(a.get("takenAt")), str(a.get("id") or "")),
    )
    if len(ordered) == 1:
        return [list(ordered)]

    sustain = max(1, int(sustain_frames))
    thr = float(delta_threshold)
    segments: list[list[dict]] = [[ordered[0]]]
    ref_id = str(ordered[0].get("id"))
    pending: list[dict] = []
    streak = 0

    for asset in ordered[1:]:
        cur_id = str(asset.get("id"))
        dist = appearance_distance(vectors[ref_id], vectors[cur_id])
        if dist >= thr:
            streak += 1
            pending.append(asset)
            if streak >= sustain:
                segments.append(list(pending))
                ref_id = str(pending[0].get("id"))
                pending = []
                streak = 0
            continue
        # Back below threshold → flash / noise; absorb pending into current look
        if pending:
            segments[-1].extend(pending)
            pending = []
        streak = 0
        segments[-1].append(asset)

    if pending:
        segments[-1].extend(pending)
    return segments
