"""Offline screen render chain validation (PRD §7 · layout.render.error_rate)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from travelogue.curation.mosaic.constants import MOSAIC_UNIFIED_PATTERN_IDS
from travelogue.curation.mosaic.lte_adapter import (
    read_templates_from_lte,
    resolve_render_grid_class,
)

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
            if pid and str(pid).startswith("screen-"):
                out.append(str(pid))
    return out


def _lte_validator_ok(pattern_id: str, css: str) -> bool | None:
    """Run LTE Validator (geometry + css bundle) when template exists."""
    if not read_templates_from_lte():
        return None
    try:
        from travelogue.layout_templates.css_gen import validate_css_bundle
        from travelogue.layout_templates.registry import get_engine
        from travelogue.layout_templates.validator import validate_template_def

        tpl = get_engine().get(pattern_id)
    except KeyError:
        return None
    geom = validate_template_def(tpl, mode="ci")
    if not geom.ok:
        return False
    messages = validate_css_bundle(tpl, journal_css_text=css)
    blocking = [m for m in messages if not str(m).startswith("WARN")]
    return len(blocking) == 0


def screen_pattern_render_ok(pattern_id: str, *, css: str | None = None) -> bool:
    """patternId maps to grid CSS validated by LTE Validator + journal-screens.css."""
    text = css if css is not None else _journal_screens_css()
    lte_ok = _lte_validator_ok(pattern_id, text)
    if lte_ok is False:
        return False
    grid_class = resolve_render_grid_class(pattern_id)
    if not grid_class:
        return False
    if grid_class not in text:
        return False
    if lte_ok is True:
        return True
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
