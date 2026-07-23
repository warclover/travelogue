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

    Assets without vectors are omitted (caller keeps them on the scene group).
    A sustained streak of Δ≥threshold over ``sustain_frames`` consecutive edges
    opens a new look segment (D-SSG-09).
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
    streak = 0
    for i in range(1, len(ordered)):
        prev_id = str(ordered[i - 1].get("id"))
        cur_id = str(ordered[i].get("id"))
        dist = appearance_distance(vectors[prev_id], vectors[cur_id])
        if dist >= thr:
            streak += 1
        else:
            streak = 0
        if streak >= sustain:
            segments.append([ordered[i]])
            streak = 0
        else:
            segments[-1].append(ordered[i])
    return segments
