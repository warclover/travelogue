"""Shared helpers for Studio UI Detail runtime e2e gates."""

from __future__ import annotations

import re
from typing import Any


_RGB_RE = re.compile(
    r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)",
    re.I,
)
_SRGB_RE = re.compile(
    r"color\(\s*srgb\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)",
    re.I,
)


def color_family_key(color: str) -> str:
    """Collapse opacity variants of the same RGB into one semantic family."""
    raw = (color or "").strip().lower()
    if not raw:
        return ""
    m = _RGB_RE.search(raw)
    if m:
        r, g, b = (int(round(float(m.group(i)))) for i in (1, 2, 3))
        return f"{r},{g},{b}"
    m = _SRGB_RE.search(raw)
    if m:
        r, g, b = (int(round(float(m.group(i)) * 255)) for i in (1, 2, 3))
        return f"{r},{g},{b}"
    return raw


def semantic_color_count(colors: list[str] | None) -> int:
    keys = {color_family_key(c) for c in (colors or []) if c}
    keys.discard("")
    return len(keys)


def findings_from_panel_metrics(
    metrics: dict[str, Any],
    *,
    surface: str,
    font_cap: int = 5,
    color_cap: int = 4,
) -> list[dict[str, Any]]:
    """Contract-oriented findings: unique fonts + semantic color families."""
    if metrics.get("error"):
        return [
            {
                "id": "D-UID-HARNESS",
                "severity": "P0",
                "surface": surface,
                "detail": metrics["error"],
            }
        ]
    out: list[dict[str, Any]] = []
    font_count = int(metrics.get("fontSizeCount") or 0)
    if font_count > font_cap:
        out.append(
            {
                "id": "D-UID-03",
                "severity": "P1",
                "surface": surface,
                "detail": f"字号种类 {font_count}: {metrics.get('uniqueFontSizes')}",
            }
        )
    colors = list(metrics.get("uniqueColors") or [])
    family_n = semantic_color_count(colors)
    if family_n > color_cap:
        out.append(
            {
                "id": "D-UID-04",
                "severity": "P1",
                "surface": surface,
                "detail": (
                    f"语义色族 {family_n}（原始色串 {len(colors)}）: "
                    f"{metrics.get('uniqueColors')}"
                ),
            }
        )
    return out


def assert_no_blocking_findings(
    findings: list[dict[str, Any]], *, label: str = "ui-detail"
) -> None:
    p0 = [f for f in findings if f.get("severity") == "P0"]
    p1 = [f for f in findings if f.get("severity") == "P1"]
    assert p0 == [], f"{label} P0: {p0}"
    assert p1 == [], f"{label} P1: {p1}"
