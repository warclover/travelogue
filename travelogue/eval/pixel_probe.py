"""P19 pixel-layer checks: focal CSS + LTE slot aspect sanity."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from travelogue.curation.mosaic.grid_specs import gap_cells
from travelogue.curation.mosaic.legacy_specs import explicit_grid_specs
from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.registry import get_engine

_STAGE_16_9 = 16 / 9
_3P2L_PATTERN = "screen-mosaic-5-3portrait-2land-balanced"
_2P3L_PATTERN = "screen-mosaic-5-2p3l-equal"

_REPO = Path(__file__).resolve().parents[2]
_JOURNAL_SCREENS_CSS = _REPO / "templates" / "visual-journal" / "journal-screens.css"

_FORBIDDEN_OBJECT_POSITION = re.compile(
    r"object-position:\s*(top\s+center|center)\s*;",
    re.IGNORECASE,
)


def scan_journal_screens_focal_css(css_path: Path | None = None) -> dict[str, Any]:
    path = css_path or _JOURNAL_SCREENS_CSS
    text = path.read_text(encoding="utf-8")
    matches = list(_FORBIDDEN_OBJECT_POSITION.finditer(text))
    lines = [text[:m.start()].count("\n") + 1 for m in matches]
    return {
        "ok": not matches,
        "path": str(path),
        "violations": len(matches),
        "lines": lines,
    }


def audit_lte_slot_display_aspect(template_ids: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Ensure ga templates expose sane displayAspect per slot (R-P19-203 smoke)."""
    engine = get_engine()
    ids = template_ids or tuple(t.id for t in engine.list_active())
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for tid in ids:
        try:
            template = engine.get(tid)
        except KeyError:
            warnings.append(f"{tid}: missing")
            continue
        for slot in template.slots:
            da = slot.display_aspect
            if da is None:
                da = slot_display_aspect(slot.rect, template.stage)
            if da <= 0.05 or da > 20.0:
                warnings.append(f"{tid}: slot {slot.index} aspect {da:.4f} out of range")
            rows.append(
                {
                    "templateId": tid,
                    "slot": slot.index,
                    "displayAspect": round(float(da), 4),
                }
            )
    return {
        "ok": not warnings,
        "templates": len(ids),
        "slots": len(rows),
        "warnings": warnings,
    }


def _mosaic_slot_aspect(spec: tuple[int, int, int, int], *, stage: float = _STAGE_16_9) -> float:
    c0, c1, r0, r1 = spec
    col_frac = (c1 - c0 + 1) / 3.0
    row_frac = (r1 - r0 + 1) / 3.0
    return (col_frac * stage) / row_frac


def audit_3p2l_mosaic_geometry() -> dict[str, Any]:
    """R-P19-204 · 3P+2L balanced mosaic slot AR smoke (P16-P-03 class defects)."""
    specs = explicit_grid_specs().get(_3P2L_PATTERN)
    warnings: list[str] = []
    if not specs:
        return {"ok": False, "patternId": _3P2L_PATTERN, "warnings": ["template missing"]}
    gaps = gap_cells(specs)
    if gaps:
        warnings.append(f"gap_cells={sorted(gaps)}")
    for i, spec in enumerate(specs[:3]):
        ar = _mosaic_slot_aspect(spec)
        if ar >= 1.0:
            warnings.append(f"portrait slot {i} aspect {ar:.3f} not tall")
    for i, spec in enumerate(specs[3:], start=3):
        ar = _mosaic_slot_aspect(spec)
        if ar <= 1.0:
            warnings.append(f"landscape slot {i} aspect {ar:.3f} not wide")
    return {"ok": not warnings, "patternId": _3P2L_PATTERN, "warnings": warnings}


def audit_2p3l_equal_geometry() -> dict[str, Any]:
    """R-P19-204 · 2P+3L equal mosaic fills 3×3 without orphan gap cells."""
    specs = explicit_grid_specs().get(_2P3L_PATTERN)
    warnings: list[str] = []
    if not specs:
        return {"ok": False, "patternId": _2P3L_PATTERN, "warnings": ["template missing"]}
    gaps = gap_cells(specs)
    if gaps:
        warnings.append(f"gap_cells={sorted(gaps)}")
    return {"ok": not warnings, "patternId": _2P3L_PATTERN, "warnings": warnings}


def run_p19_pixel_probe(
    *,
    css_path: Path | None = None,
    template_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    focal = scan_journal_screens_focal_css(css_path)
    aspect = audit_lte_slot_display_aspect(template_ids)
    mosaic_3p2l = audit_3p2l_mosaic_geometry()
    mosaic_2p3l = audit_2p3l_equal_geometry()
    warnings: list[str] = []
    if not focal["ok"]:
        warnings.append(f"focal_css: {focal['violations']} hardcoded object-position rules")
    warnings.extend(aspect.get("warnings") or [])
    warnings.extend(mosaic_3p2l.get("warnings") or [])
    warnings.extend(mosaic_2p3l.get("warnings") or [])
    return {
        "ok": focal["ok"] and aspect["ok"] and mosaic_3p2l["ok"] and mosaic_2p3l["ok"],
        "focalCss": focal,
        "slotAspect": aspect,
        "mosaic3p2l": mosaic_3p2l,
        "mosaic2p3l": mosaic_2p3l,
        "warnings": warnings,
    }
