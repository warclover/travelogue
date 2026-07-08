"""G1 edit-distance feedback (layout kernel). with denoising (Phase 3a schema; training in 3c)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EditType = Literal[
    "reorder",
    "swap_hero",
    "exclude_asset",
    "pattern_change",
    "chapter_merge",
    "other",
]


@dataclass
class G1EditRecord:
    trip_id: str
    edit_type: EditType
    before_snapshot: dict[str, Any]
    after_snapshot: dict[str, Any]
    distance: float
    user_id: str | None = None
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tripId": self.trip_id,
            "editType": self.edit_type,
            "distance": round(self.distance, 4),
            "weight": round(self.weight, 4),
            "userId": self.user_id,
        }


def g1_edit_distance(before: dict, after: dict) -> float:
    """Normalized 0..1 distance between two chapter-plan snapshots."""
    before_ids = _chapter_asset_sets(before)
    after_ids = _chapter_asset_sets(after)
    if not before_ids and not after_ids:
        return 0.0
    union = before_ids | after_ids
    if not union:
        return 0.0
    inter = before_ids & after_ids
    return 1.0 - len(inter) / len(union)


def classify_edit_type(before: dict, after: dict) -> EditType:
    """Heuristic edit classification for denoising."""
    b_heroes = _chapter_heroes(before)
    a_heroes = _chapter_heroes(after)
    if b_heroes != a_heroes:
        return "swap_hero"
    b_patterns = _screen_patterns(before)
    a_patterns = _screen_patterns(after)
    if b_patterns != a_patterns:
        return "pattern_change"
    b_ids = _chapter_asset_sets(before)
    a_ids = _chapter_asset_sets(after)
    if len(a_ids) < len(b_ids):
        return "exclude_asset"
    if len(before.get("chapters") or before.get("chapterPlan") or []) != len(
        after.get("chapters") or after.get("chapterPlan") or []
    ):
        return "chapter_merge"
    if b_ids != a_ids:
        return "reorder"
    return "other"


def edit_weight_for_record(record: G1EditRecord) -> float:
    """
    Down-weight noisy single edits; full weight for structural changes.
    Cohort aggregation happens in filter_edits_for_training.
    """
    if record.edit_type == "other":
        return 0.2
    if record.edit_type == "reorder" and record.distance < 0.05:
        return 0.3
    return 1.0


def filter_edits_for_training(
    records: list[G1EditRecord],
    *,
    min_trip_count: int = 3,
    min_weighted_count: float = 2.0,
) -> list[G1EditRecord]:
    """
    Keep only edit patterns that appear across multiple trips (denoising).
    Individual whim edits stay in log but drop out of training pool.
    """
    from collections import defaultdict

    buckets: dict[tuple[str, EditType], list[G1EditRecord]] = defaultdict(list)
    for rec in records:
        buckets[(rec.trip_id, rec.edit_type)].append(rec)

    trip_types: dict[EditType, set[str]] = defaultdict(set)
    for (trip_id, edit_type), _group in buckets.items():
        trip_types[edit_type].add(trip_id)

    out: list[G1EditRecord] = []
    for rec in records:
        if len(trip_types[rec.edit_type]) < min_trip_count:
            continue
        w = edit_weight_for_record(rec) * rec.weight
        if w >= 0.5:
            rec.weight = w
            out.append(rec)
    return out

