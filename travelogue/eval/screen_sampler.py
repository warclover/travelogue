"""Reproducible screen sampling for P19 VLM judge (DQ-01)."""

from __future__ import annotations

import hashlib
import random
from typing import Any


def _content_screens(chapters: list[dict]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ch in chapters:
        ch_id = str(ch.get("id") or "")
        for idx, screen in enumerate(ch.get("screens") or []):
            pid = str(screen.get("patternId") or "")
            if not pid or pid in {"breath-pause", "screen-breath"}:
                continue
            slots = screen.get("slots") or []
            asset_ids = tuple(
                sorted(str(s.get("assetId") or "") for s in slots if s.get("assetId"))
            )
            rows.append(
                {
                    "chapterId": ch_id,
                    "screenIndex": idx,
                    "globalIndex": len(rows),
                    "patternId": pid,
                    "assetIds": asset_ids,
                    "screenId": str(screen.get("screenId") or f"{ch_id}:{idx}"),
                }
            )
    return rows


def screens_signature(chapters: list[dict], *, trip_id: str = "") -> str:
    parts: list[str] = [trip_id]
    for row in _content_screens(chapters):
        parts.append(
            f"{row['chapterId']}|{row['patternId']}|{','.join(row['assetIds'])}"
        )
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def _seed_from_trip(trip_id: str, signature: str) -> int:
    raw = f"{trip_id}:{signature}"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


def sample_screen_indices(
    chapters: list[dict],
    *,
    trip_id: str,
    max_screens: int = 12,
) -> list[int]:
    """Return global indices into content screens (stable for A/B pairs)."""
    screens = _content_screens(chapters)
    if not screens:
        return []
    if len(screens) <= max_screens:
        return list(range(len(screens)))

    sig = screens_signature(chapters, trip_id=trip_id)
    rng = random.Random(_seed_from_trip(trip_id, sig))
    chosen: set[int] = set()

    # Chapter openers (first content screen per chapter).
    seen_ch: set[str] = set()
    for i, row in enumerate(screens):
        ch = row["chapterId"]
        if ch not in seen_ch:
            seen_ch.add(ch)
            chosen.add(i)

    # Hero / mosaic patterns.
    for i, row in enumerate(screens):
        pid = row["patternId"]
        if "mosaic" in pid or pid.endswith("-1") or "hero" in pid:
            chosen.add(i)

    # Breath-adjacent pairs (screen after multi-slot).
    for i, row in enumerate(screens):
        pid = row["patternId"]
        slot_count = len(row["assetIds"])
        if slot_count >= 3 and i + 1 < len(screens):
            chosen.add(i)
            chosen.add(i + 1)

    # Random fill.
    pool = list(range(len(screens)))
    rng.shuffle(pool)
    for i in pool:
        if len(chosen) >= max_screens:
            break
        chosen.add(i)

    indices = sorted(chosen)
    if len(indices) > max_screens:
        indices = sorted(rng.sample(indices, max_screens))
    return indices


def sample_screens(
    chapters: list[dict],
    *,
    trip_id: str,
    max_screens: int = 12,
) -> list[dict[str, Any]]:
    screens = _content_screens(chapters)
    idxs = sample_screen_indices(chapters, trip_id=trip_id, max_screens=max_screens)
    return [screens[i] for i in idxs if i < len(screens)]
