"""Lite copy v1.1 · trip-level metrics (server-side, narrate/render)."""

from __future__ import annotations

from travelogue.services.decor_line import _GENERIC_RE, _contains_banned
from travelogue.util.datetime_ import utc_now_iso

COPY_METRICS_PHASE = "lite-copy-v1.1"

ALLOWED_COPY_UI_EVENTS = frozenset(
    {
        "preview_open",
        "photos_only_on",
        "photos_only_off",
    }
)


def compute_intent_adoption_rate(trip: dict) -> float:
    chapters = trip.get("chapters") or []
    if not chapters:
        return 0.0
    adopted = 0
    for ch in chapters:
        intent = (ch.get("curation") or {}).get("copyIntent") or {}
        if any(str(intent.get(key) or "").strip() for key in ("mood", "focus", "note")):
            adopted += 1
    return round(adopted / len(chapters), 3)


def _chapter_decor_lines(trip: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for ch in trip.get("chapters") or []:
        ch_id = str(ch.get("id") or "")
        line = str(ch.get("decorLine") or "").strip()
        if ch_id:
            out.append((ch_id, line))
    return out


def count_generic_hits(text: str) -> int:
    if not text:
        return 0
    hits = len(_GENERIC_RE.findall(text))
    if _contains_banned(text):
        hits += 1
    return hits


def compute_copy_metrics(trip: dict) -> dict:
    """Aggregate decorLine / hook / epilogue stats for observability."""
    chapters = trip.get("chapters") or []
    decor_pairs = _chapter_decor_lines(trip)
    decor_filled = sum(1 for _, line in decor_pairs if line)
    chapter_total = max(len(chapters), len(decor_pairs))
    empty = chapter_total - decor_filled if chapter_total else 0

    hook = str((trip.get("meta") or {}).get("hook") or "").strip()
    epilogue = str(trip.get("epilogue") or "").strip()
    copy_parts = [hook, epilogue] + [line for _, line in decor_pairs if line]
    copy_total_chars = sum(len(p) for p in copy_parts)
    generic_hits = sum(count_generic_hits(p) for p in copy_parts)

    edited_decor = sum(
        1
        for ch in chapters
        if (str(ch.get("decorLine") or "").strip() and ch.get("edited"))
    )
    edited_any = sum(
        1
        for ch in chapters
        if ch.get("edited") and (str(ch.get("decorLine") or "").strip() or str(ch.get("lead") or "").strip())
    )
    meta_edited = bool((trip.get("meta") or {}).get("edited"))

    fill_rate = round(decor_filled / chapter_total, 3) if chapter_total else 0.0
    empty_rate = round(empty / chapter_total, 3) if chapter_total else 0.0
    edit_retention = (
        round((edited_decor + (1 if meta_edited and hook else 0)) / max(decor_filled, 1), 3)
        if decor_filled or meta_edited
        else 0.0
    )

    return {
        "phase": COPY_METRICS_PHASE,
        "computedAt": utc_now_iso(),
        "chapterCount": chapter_total,
        "decorLineCount": decor_filled,
        "decorLineEmptyCount": empty,
        "decor_line_fill_rate": fill_rate,
        "decor_line_empty_rate": empty_rate,
        "copy_total_chars": copy_total_chars,
        "generic_phrase_hits": generic_hits,
        "edited_decor_line_count": edited_decor,
        "edited_copy_field_count": edited_any + (1 if meta_edited else 0),
        "inline_edit_retention_rate": edit_retention,
        "intent_adoption_rate": compute_intent_adoption_rate(trip),
        "hook_chars": len(hook),
        "epilogue_chars": len(epilogue),
    }


def record_copy_ui_event(trip: dict, event: str) -> dict:
    """Increment client-side copy UI counters (photos-only toggle, preview open)."""
    if event not in ALLOWED_COPY_UI_EVENTS:
        raise ValueError(f"unknown copy ui event: {event}")
    curation = trip.setdefault("curation", {})
    prev = dict(curation.get("copyMetrics") or {})
    counts = dict(prev.get("clientEventCounts") or {})
    counts[event] = int(counts.get(event) or 0) + 1
    on = int(counts.get("photos_only_on") or 0)
    off = int(counts.get("photos_only_off") or 0)
    toggles = on + off
    metrics = compute_copy_metrics(trip)
    metrics["clientEventCounts"] = counts
    metrics["photos_only_rate"] = round(on / toggles, 3) if toggles else 0.0
    curation["copyMetrics"] = metrics
    return metrics


def record_copy_metrics(trip: dict) -> dict:
    """Write metrics under curation.copyMetrics and return payload."""
    curation = trip.setdefault("curation", {})
    prev = dict(curation.get("copyMetrics") or {})
    metrics = compute_copy_metrics(trip)
    if prev.get("clientEventCounts"):
        metrics["clientEventCounts"] = prev["clientEventCounts"]
        metrics["photos_only_rate"] = prev.get("photos_only_rate", 0.0)
    curation["copyMetrics"] = metrics
    return metrics


def merge_copy_run_note(trip: dict, *, agent: str, note: str) -> None:
    """Append a lightweight observability note to pipeline.runs."""
    pipe = trip.setdefault("pipeline", {})
    runs = pipe.setdefault("runs", [])
    runs.append(
        {
            "runId": f"copy-metrics-{utc_now_iso()}",
            "agent": agent,
            "note": note,
            "finishedAt": utc_now_iso(),
        }
    )
