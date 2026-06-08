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
