"""§4.10 render binding checks · AC-P17-30."""

from __future__ import annotations

import re
from pathlib import Path

from travelogue.paths import ROOT

_JOURNAL_SCREENS = ROOT / "templates" / "visual-journal" / "journal-screens.css"

# object-fit: contain + portrait row layouts keep fixed anchors (PRD §4.10.1 exempt)
_EXEMPT_CONTAIN_MARKERS = (
    "layout-slot__img--contain",
    "person-pair",
    "person-triple",
    "person-grid-8",
)


def journal_screens_css_path() -> Path:
    return _JOURNAL_SCREENS


def focal_object_position_css(*, focal_x: float = 0.5, focal_y: float = 0.45) -> str:
    """Expected cover object-position when journal-screens.css binds --focal-x/y."""
    fx = max(0.0, min(1.0, float(focal_x)))
    fy = max(0.0, min(1.0, float(focal_y)))
    return f"calc({fx} * 100%) calc({fy} * 100%)"


def slot_style_includes_focal(asset: dict) -> bool:
    fp = asset.get("focalPoint") or {}
    try:
        float(fp.get("x", 0.5))
        float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        return False
    return True


def cover_rules_use_focal_variables(css: str | None = None) -> list[str]:
    """Return cover selectors that still hardcode object-position (should be empty)."""
    text = css if css is not None else _JOURNAL_SCREENS.read_text(encoding="utf-8")
    violations: list[str] = []
    blocks = re.findall(
        r"([^{}]+)\{([^{}]*object-position\s*:\s*[^;{}]+[^{}]*)\}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for selector, body in blocks:
        if "cover" not in selector.lower():
            continue
        if any(marker in selector for marker in _EXEMPT_CONTAIN_MARKERS):
            continue
        if "contain" in selector.lower():
            continue
        if "var(--focal-x" in body or "var(--focal-y" in body:
            continue
        if re.search(r"object-position\s*:\s*center\s*;", body, re.I):
            violations.append(selector.strip())
        elif re.search(r"object-position\s*:\s*center\s+30%", body, re.I):
            violations.append(selector.strip())
        elif re.search(r"object-position\s*:\s*top\s+center", body, re.I):
            continue
    return violations
