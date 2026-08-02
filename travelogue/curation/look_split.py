"""SSG M2 · look boundary splitting from appearance distances (pure logic)."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np

from travelogue.media.face_embed import l2_normalize
from travelogue.vision.look_appearance import appearance_distance

LOOK_REFERENCE_MODES = frozenset({"first", "ema", "medoid"})


def normalize_look_reference_mode(raw: Any) -> tuple[str, str | None]:
    """Return ``(effective_mode, skip_reason|None)``. Unknown → ``first`` + reason."""
    text = str(raw if raw is not None else "first").strip().lower()
    if text in LOOK_REFERENCE_MODES:
        return text, None
    return "first", f"unknown_look_reference_mode:{raw}"


def _parse_taken_at(raw: Any) -> datetime:
    if raw is None:
        return datetime.min.replace(tzinfo=UTC)
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _asset_id(asset: dict) -> str:
    return str(asset.get("id") or "")


def _medoid_vector(
    members: Sequence[dict],
    vectors: Mapping[str, np.ndarray],
) -> np.ndarray:
    ids = [_asset_id(a) for a in members if _asset_id(a) in vectors]
    if not ids:
        raise ValueError("medoid requires at least one vector")
    if len(ids) == 1:
        return np.asarray(vectors[ids[0]], dtype=np.float64).copy()
    best_id = ids[0]
    best_score = float("inf")
    for cand in ids:
        score = 0.0
        for other in ids:
            if other == cand:
                continue
            score += appearance_distance(vectors[cand], vectors[other])
        if score < best_score:
            best_score = score
            best_id = cand
    return np.asarray(vectors[best_id], dtype=np.float64).copy()


def _ema_update(
    ref: np.ndarray,
    cur: np.ndarray,
    *,
    alpha: float,
) -> np.ndarray:
    a = min(1.0, max(0.0, float(alpha)))
    blended = (1.0 - a) * np.asarray(ref, dtype=np.float64) + a * np.asarray(
        cur, dtype=np.float64
    )
    return l2_normalize(blended)


def _init_reference(
    mode: str,
    members: Sequence[dict],
    vectors: Mapping[str, np.ndarray],
) -> tuple[str, np.ndarray]:
    first_id = _asset_id(members[0])
    if mode == "medoid":
        return first_id, _medoid_vector(members, vectors)
    return first_id, np.asarray(vectors[first_id], dtype=np.float64).copy()


def _refresh_reference_after_absorb(
    mode: str,
    *,
    ref_id: str,
    ref_vec: np.ndarray,
    segment: Sequence[dict],
    cur_id: str,
    vectors: Mapping[str, np.ndarray],
    ema_alpha: float,
) -> tuple[str, np.ndarray]:
    if mode == "first":
        return ref_id, ref_vec
    if mode == "ema":
        return ref_id, _ema_update(ref_vec, vectors[cur_id], alpha=ema_alpha)
    # medoid of the open segment
    return ref_id, _medoid_vector(segment, vectors)


def split_look_segments(
    assets: Sequence[dict],
    vectors: Mapping[str, np.ndarray],
    *,
    delta_threshold: float,
    sustain_frames: int,
    reference_mode: str = "first",
    ema_alpha: float = 0.3,
    meta_out: MutableMapping[str, Any] | None = None,
) -> list[list[dict]]:
    """Split look-eligible assets (time-ordered) into look segments.

    Distance is measured against the **current look reference**, not only the
    previous frame. Default reference is the first frame of the open segment
    (``reference_mode=first`` · ALG-V3 PL-A5). Opt-in ``ema`` / ``medoid`` update
    the reference as the segment grows. A candidate streak of
    ``sustain_frames`` frames with Δ≥threshold commits a new look; a shorter
    streak is absorbed (flash rejection · D-SSG-09 / AC-SSG-12).
    """
    mode, skip_reason = normalize_look_reference_mode(reference_mode)
    if meta_out is not None:
        meta_out["lookReferenceMode"] = mode
        meta_out["lookReferenceModeRequested"] = str(
            reference_mode if reference_mode is not None else "first"
        )
        if skip_reason:
            meta_out["lookReferenceSkipReason"] = skip_reason

    eligible = [a for a in assets if _asset_id(a) in vectors]
    if not eligible:
        return []
    ordered = sorted(
        eligible,
        key=lambda a: (_parse_taken_at(a.get("takenAt")), _asset_id(a)),
    )
    if len(ordered) == 1:
        return [list(ordered)]

    sustain = max(1, int(sustain_frames))
    thr = float(delta_threshold)
    segments: list[list[dict]] = [[ordered[0]]]
    ref_id, ref_vec = _init_reference(mode, segments[0], vectors)
    pending: list[dict] = []
    streak = 0

    for asset in ordered[1:]:
        cur_id = _asset_id(asset)
        # ``first`` keeps historical id lookup; ema/medoid use maintained vector.
        if mode == "first":
            dist = appearance_distance(vectors[ref_id], vectors[cur_id])
        else:
            dist = appearance_distance(ref_vec, vectors[cur_id])
        if dist >= thr:
            streak += 1
            pending.append(asset)
            if streak >= sustain:
                segments.append(list(pending))
                ref_id, ref_vec = _init_reference(mode, pending, vectors)
                pending = []
                streak = 0
            continue
        # Back below threshold → flash / noise; absorb pending into current look
        if pending:
            segments[-1].extend(pending)
            pending = []
        streak = 0
        segments[-1].append(asset)
        ref_id, ref_vec = _refresh_reference_after_absorb(
            mode,
            ref_id=ref_id,
            ref_vec=ref_vec,
            segment=segments[-1],
            cur_id=cur_id,
            vectors=vectors,
            ema_alpha=ema_alpha,
        )

    if pending:
        segments[-1].extend(pending)
    return segments
