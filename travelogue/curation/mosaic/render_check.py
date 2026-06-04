"""Offline screen render chain validation (PRD §7 · layout.render.error_rate)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from travelogue.curation.mosaic.constants import MOSAIC_UNIFIED_PATTERN_IDS, PATTERN_GRID_CLASS

_SCREENS_CSS = (
    Path(__file__).resolve().parents[3] / "templates" / "visual-journal" / "journal-screens.css"
)


@lru_cache(maxsize=1)
def _journal_screens_css() -> str:
    return _SCREENS_CSS.read_text(encoding="utf-8")


def _screen_pattern_ids(chapters: list[dict]) -> list[str]:
    out: list[str] = []
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = screen.get("patternId")
            if pid and pid.startswith("screen-"):
                out.append(pid)
    return out


def screen_pattern_render_ok(pattern_id: str, *, css: str | None = None) -> bool:
    """patternId maps to a grid class present in journal-screens.css."""
    text = css if css is not None else _journal_screens_css()
    grid_class = PATTERN_GRID_CLASS.get(pattern_id)
    if not grid_class:
        from travelogue.curation.screen_planner import PATTERN_GRID_CLASS as planner_classes

        grid_class = planner_classes.get(pattern_id)
    if not grid_class:
        return False
    if grid_class not in text:
        return False
    if f'data-pattern="{pattern_id}"' in text:
        return True
    return grid_class in text


def compute_layout_render_error_rate(
    chapters: list[dict],
    *,
    scope: str = "mcs_unified",
) -> dict[str, Any]:
    """
    scope=mcs_unified: only MOSAIC_UNIFIED_PATTERN_IDS (Phase 15 KPI).
    scope=all_screen: every screen-* pattern on the trip.
    """
    css = _journal_screens_css()
    pids = _screen_pattern_ids(chapters)
    if scope == "mcs_unified":
        pids = [p for p in pids if p in MOSAIC_UNIFIED_PATTERN_IDS]
    checked = len(pids)
    errors = sum(1 for p in pids if not screen_pattern_render_ok(p, css=css))
    rate = round(errors / checked, 6) if checked else 0.0
    return {
        "layout.render.error_rate": rate,
        "layoutRenderChecked": checked,
        "layoutRenderErrors": errors,
    }
