"""PAIR-H* hard filters and PAIR-S* soft contrast (PRD §3.3 / §3.4)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from travelogue.domain.closing_view import (
    _read_dominant_tone,
    _tone_saturation,
    asset_is_landscape,
    cover_ids_to_exclude,
)


def _parse_taken_at(asset: dict) -> datetime | None:
    raw = asset.get("takenAt") or asset.get("taken_at") or asset.get("capturedAt")
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _face_max_area_ratio(asset: dict) -> float:
    faces = asset.get("faces")
    if not isinstance(faces, (list, tuple)) or not faces:
        # Heuristic: faceCount with tight center focal ≈ large face
        try:
            count = int(asset.get("faceCount") or asset.get("face_count") or 0)
        except (TypeError, ValueError):
            count = 0
        if count <= 0:
            return 0.0
        fp = asset.get("focalPoint") if isinstance(asset.get("focalPoint"), dict) else {}
        try:
            fx = float(fp.get("x", 0.5))
            fy = float(fp.get("y", 0.45))
        except (TypeError, ValueError):
            return 0.15
        if abs(fx - 0.5) < 0.12 and abs(fy - 0.42) < 0.14:
            return 0.28
        return 0.08
    best = 0.0
    for face in faces:
        if not isinstance(face, dict):
            continue
        box = face.get("bbox") or face.get("box") or face
        try:
            w = float(box.get("w") or box.get("width") or 0)
            h = float(box.get("h") or box.get("height") or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        # normalized ratios preferred; absolute px → approximate via asset size
        if w > 1.0 or h > 1.0:
            aw = float(asset.get("width") or 1) or 1.0
            ah = float(asset.get("height") or 1) or 1.0
            w, h = w / aw, h / ah
        best = max(best, max(0.0, w) * max(0.0, h))
    return best


def _burst_id(asset: dict) -> str:
    for key in ("burstId", "burst_id", "burstGroupId", "groupId"):
        val = asset.get(key)
        if val:
            return str(val)
    return ""


def _aspect_close(a: dict, b: dict, *, tol: float = 0.25) -> bool:
    try:
        aw = float(a.get("width") or 0)
        ah = float(a.get("height") or 0)
        bw = float(b.get("width") or 0)
        bh = float(b.get("height") or 0)
        if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
            return False
        return abs((aw / ah) - (bw / bh)) <= tol
    except (TypeError, ValueError):
        return False


def pairing_hard_violations(
    cover: dict | None,
    candidate: dict,
    *,
    near_dup_seconds: float = 3.0,
    large_face_area: float = 0.18,
) -> list[str]:
    """Return PAIR-H* violation codes; empty means pass."""
    violations: list[str] = []
    if not cover:
        return violations
    cover_id = str(cover.get("id") or "")
    cand_id = str(candidate.get("id") or "")
    if cover_id and cand_id and cover_id == cand_id:
        violations.append("PAIR-H1")

    # PAIR-H2 · same burst or near-dup takenAt
    cb = _burst_id(cover)
    kb = _burst_id(candidate)
    if cb and kb and cb == kb:
        violations.append("PAIR-H2")
    else:
        t0 = _parse_taken_at(cover)
        t1 = _parse_taken_at(candidate)
        if t0 and t1:
            delta = abs((t1 - t0).total_seconds())
            if delta <= float(near_dup_seconds) and _aspect_close(cover, candidate):
                violations.append("PAIR-H2")

    # PAIR-H3 · cover large face → avoid closing large face
    cover_face = _face_max_area_ratio(cover)
    cand_face = _face_max_area_ratio(candidate)
    if cover_face >= large_face_area and cand_face >= large_face_area:
        violations.append("PAIR-H3")

    return violations


def filter_pairing_hard(
    candidates: list[str],
    assets: dict[str, dict],
    trip: dict,
    *,
    near_dup_seconds: float = 3.0,
) -> tuple[list[str], int]:
    """Filter PAIR-H*; returns (kept, hard_filtered_count)."""
    cover_ids = cover_ids_to_exclude(trip)
    cover = None
    for cid in cover_ids:
        if cid in assets:
            cover = assets[cid]
            break
    kept: list[str] = []
    filtered = 0
    for aid in candidates:
        asset = assets.get(aid)
        if not asset:
            continue
        viol = pairing_hard_violations(
            cover, asset, near_dup_seconds=near_dup_seconds
        )
        if viol:
            filtered += 1
            continue
        kept.append(aid)
    return kept, filtered


def pairing_soft_bonus(
    cover: dict | None,
    candidate: dict,
    *,
    soft_weight: float = 0.35,
) -> float:
    """PAIR-S* soft contrast bonus in ~[0, soft_weight]."""
    if not cover or soft_weight <= 0:
        return 0.0
    score = 0.0

    cover_face = _face_max_area_ratio(cover)
    cand_face = _face_max_area_ratio(candidate)
    # S1: cover person → prefer empty closing
    if cover_face >= 0.08 and cand_face < 0.05:
        score += 0.4
    # S2: cover landscape → closing detail/evening ok
    if asset_is_landscape(cover) and not asset_is_landscape(candidate):
        score += 0.25
    tags = candidate.get("subjectTags") or candidate.get("tags") or []
    tag_set = {str(t).casefold() for t in tags if t}
    if tag_set & {"night", "evening", "dusk", "sunset"}:
        score += 0.2

    # S3: saturation / luma delta in a healthy band
    sat_c = _tone_saturation(_read_dominant_tone(cover))
    sat_k = _tone_saturation(_read_dominant_tone(candidate))
    delta = abs(sat_c - sat_k)
    if 0.08 <= delta <= 0.55:
        score += 0.35

    return min(float(soft_weight), score * float(soft_weight))
