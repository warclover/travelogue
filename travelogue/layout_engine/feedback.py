"""LSE-CAP-05 layoutFeedback projection + export (§4.5.5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.curation.feedback import G1EditRecord, edit_weight_for_record
from travelogue.util.datetime_ import utc_now_iso

SIDECAR_NAME = "layout-feedback.jsonl"
PAIRWISE_DISTANCE_LO = 0.05
PAIRWISE_DISTANCE_HI = 0.85


def is_valid_pairwise_label(record: G1EditRecord) -> bool:
    if record.edit_type != "pattern_change":
        return False
    if record.distance < PAIRWISE_DISTANCE_LO or record.distance > PAIRWISE_DISTANCE_HI:
        return False
    return edit_weight_for_record(record) >= 0.5


def project_layout_feedback(record: G1EditRecord) -> dict[str, Any]:
    """Map G1EditRecord → layoutFeedback sidecar event."""
    before_patterns = _screen_pattern_pairs(record.before_snapshot)
    after_patterns = _screen_pattern_pairs(record.after_snapshot)
    return {
        "schemaVersion": 1,
        "tripId": record.trip_id,
        "editType": record.edit_type,
        "distance": round(record.distance, 4),
        "weight": round(edit_weight_for_record(record), 4),
        "pairwiseEligible": is_valid_pairwise_label(record),
        "beforePatterns": before_patterns,
        "afterPatterns": after_patterns,
        "emittedAt": utc_now_iso(),
    }


def append_layout_feedback(
    trip_dir: Path,
    record: G1EditRecord,
    *,
    export_pairwise: bool = True,
) -> Path | None:
    if not export_pairwise and not is_valid_pairwise_label(record):
        return None
    event = project_layout_feedback(record)
    runs = trip_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    path = runs / SIDECAR_NAME
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def read_layout_feedback_events(trip_dir: Path, *, limit: int = 200) -> list[dict[str, Any]]:
    path = trip_dir / "runs" / SIDECAR_NAME
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    return events[-limit:]


def _screen_pattern_pairs(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for ch in snapshot.get("chapters") or snapshot.get("chapterPlan") or []:
        ch_id = str(ch.get("id") or "")
        for scr in ch.get("screens") or []:
            pid = str(scr.get("patternId") or "")
            if pid:
                out.append({"chapterId": ch_id, "patternId": pid})
    return out
