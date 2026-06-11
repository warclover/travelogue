"""Unified MCS / layout reject reason codes (P19 S3-05 · R-P19-301)."""

from __future__ import annotations

from typing import Any

REJECT_PATTERN_DISABLED = "pattern_disabled"
REJECT_ORDERING_FAILED = "ordering_failed"
REJECT_MAIN_AR_INELIGIBLE = "main_ar_ineligible"
REJECT_GEOMETRY_INVALID = "geometry_invalid"
REJECT_HARD_INVALID = "hard_invalid"
REJECT_RHYTHM_STATE = "rhythm_state"
REJECT_CONSECUTIVE_PATTERN = "consecutive_pattern"

ALL_REJECT_REASONS = frozenset(
    {
        REJECT_PATTERN_DISABLED,
        REJECT_ORDERING_FAILED,
        REJECT_MAIN_AR_INELIGIBLE,
        REJECT_GEOMETRY_INVALID,
        REJECT_HARD_INVALID,
        REJECT_RHYTHM_STATE,
        REJECT_CONSECUTIVE_PATTERN,
    }
)

# Window-level log buckets (compact; full list stays in debug `rejectedTemplates`).
_WINDOW_BUCKET_BY_REASON: dict[str, str] = {
    REJECT_GEOMETRY_INVALID: "geometryRejectedTemplates",
    REJECT_MAIN_AR_INELIGIBLE: "mainArRejectedTemplates",
    REJECT_RHYTHM_STATE: "rhythmRejectedTemplates",
    REJECT_CONSECUTIVE_PATTERN: "rhythmRejectedTemplates",
    REJECT_PATTERN_DISABLED: "constraintRejectedTemplates",
    REJECT_ORDERING_FAILED: "constraintRejectedTemplates",
    REJECT_HARD_INVALID: "constraintRejectedTemplates",
}

_WINDOW_BUCKET_KEYS = frozenset(_WINDOW_BUCKET_BY_REASON.values())


def make_rejection(
    template_id: str,
    reason: str,
    *,
    detail: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "templateId": str(template_id),
        "reason": str(reason),
    }
    if detail:
        row["detail"] = str(detail)
    return row


def compact_rejection_row(item: dict[str, Any]) -> dict[str, Any]:
    tid = str(item.get("templateId") or item.get("patternId") or "")
    reason = str(item.get("reason") or "")
    row: dict[str, Any] = {"templateId": tid, "reason": reason}
    detail = item.get("detail")
    if detail:
        row["detail"] = str(detail)
    return row


def partition_rejections(
    rejected: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group reject rows into window-log bucket keys."""
    buckets: dict[str, list[dict[str, Any]]] = {k: [] for k in _WINDOW_BUCKET_KEYS}
    for item in rejected:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("reason") or "")
        bucket = _WINDOW_BUCKET_BY_REASON.get(reason)
        if not bucket:
            continue
        buckets[bucket].append(compact_rejection_row(item))
    return {k: v for k, v in buckets.items() if v}


def reject_reason_counts(rejected: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in rejected:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("reason") or "")
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return counts
