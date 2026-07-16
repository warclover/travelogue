"""FTUE W1 · frozen stageHint keys and user-visible copy (AC-FTUE-07).

Lives in domain so export/curation can emit hints without importing web.
"""

from __future__ import annotations

# Enum keys (may appear in job.stageHint); FE maps via STAGE_HINT_LABELS.
PREPARING_VISION = "preparing_vision"
PREPARING_BROWSER = "preparing_browser"
PROCESSING_PHOTOS = "processing_photos"

STAGE_HINT_COPY: dict[str, str] = {
    PREPARING_VISION: "正在准备本机视觉组件（仅第一次）…",
    PREPARING_BROWSER: "正在准备长图组件（仅第一次）…",
    PROCESSING_PHOTOS: "正在整理照片…",
}


def stage_hint_text(key_or_text: str) -> str:
    """Resolve frozen key → user copy; pass through unknown/custom hints."""
    raw = (key_or_text or "").strip()
    if not raw:
        return ""
    return STAGE_HINT_COPY.get(raw, raw)
