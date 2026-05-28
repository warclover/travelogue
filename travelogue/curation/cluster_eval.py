"""Evaluate geo segment agreement vs golden annotations (M12-0 · SP-C01)."""

from __future__ import annotations

from typing import Any


def _segment_asset_sets(segments: list[dict[str, Any]]) -> list[set[str]]:
    out: list[set[str]] = []
    for seg in segments:
        ids = seg.get("assetIds") or seg.get("asset_ids") or []
        if isinstance(ids, list) and ids:
            out.append({str(x) for x in ids})
    return out


def segment_jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def geo_segment_agreement_rate(
    golden_segments: list[dict[str, Any]],
    detected_segments: list[dict[str, Any]],
    *,
    threshold: float = 0.7,
) -> float:
    """Fraction of golden segments with best Jaccard >= threshold to any detected segment."""
    golden_sets = _segment_asset_sets(golden_segments)
    algo_sets = _segment_asset_sets(detected_segments)
    if not golden_sets:
        return 1.0
    if not algo_sets:
        return 0.0
    matched = 0
    for g in golden_sets:
        best = max(segment_jaccard(g, a) for a in algo_sets)
        if best >= threshold:
            matched += 1
    return matched / len(golden_sets)


def segments_to_eval_dict(segments: list[Any]) -> list[dict[str, Any]]:
    """Normalize GeoSegment dataclass or dict list for eval."""
    out: list[dict[str, Any]] = []
    for seg in segments:
        if hasattr(seg, "to_dict"):
            out.append(seg.to_dict())
        elif isinstance(seg, dict):
            out.append(seg)
    return out
