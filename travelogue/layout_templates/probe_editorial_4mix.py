"""Playwright probe for screen-editorial-4mix (PRD §12.5 · P0 CSS validation)."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Literal

from travelogue.curation.editorial_4mix import (
    LAYOUT_HINT_EDITORIAL_4MIX,
    PATTERN_EDITORIAL_4MIX,
)
from travelogue.paths import JOURNAL_SCREENS_CSS, TEMPLATE_VISUAL_JOURNAL

Editorial4MixProbeVariant = Literal["person", "scenery"]

OVERLAYS_CSS = TEMPLATE_VISUAL_JOURNAL / "journal-screens-overlays.css"

EDITORIAL_4MIX_PROBE_IDS: tuple[str, ...] = (
    "screen-editorial-4mix-person",
    "screen-editorial-4mix-scenery",
)

# TL land, TR port, BL port, BR land
_PROBE_ASSETS: tuple[tuple[int, int, str, str], ...] = (
    (1600, 900, "#4a5568", "cover"),
    (900, 1600, "#5b7a99", "contain"),
    (800, 1400, "#7a6b5c", "contain"),
    (1400, 800, "#6b8f71", "cover"),
)


def editorial_4mix_probe_id(variant: Editorial4MixProbeVariant) -> str:
    return f"screen-editorial-4mix-{variant}"


def editorial_4mix_baseline_path(probe_id: str) -> Path:
    from travelogue.layout_templates.probe_screenshot import BASELINE_DIR

    return BASELINE_DIR / f"{probe_id}.png"


def _svg_data_uri(width: int, height: int, color: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="{color}"/>'
        f'<rect x="0" y="{int(height * 0.85)}" width="100%" height="{int(height * 0.15)}" '
        f'fill="rgba(0,0,0,0.12)"/></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_editorial_4mix_probe_html(*, variant: Editorial4MixProbeVariant = "person") -> str:
    """Minimal page exercising 4mix overlay CSS."""
    slots_html = []
    for idx, (w, h, color, fit) in enumerate(_PROBE_ASSETS):
        fit_class = f"layout-slot__img--{fit}"
        role = "landscape" if idx in (0, 3) else "portrait"
        src = _svg_data_uri(w, h, color)
        slots_html.append(
            f'<figure class="layout-slot" data-slot="{idx}" data-role="{role}">'
            f'<img class="layout-slot__img {fit_class}" alt="" src="{src}" />'
            f"</figure>"
        )

    screens_css = JOURNAL_SCREENS_CSS.as_uri()
    overlays_css = OVERLAYS_CSS.as_uri()
    kicker = "" if variant == "scenery" else '<p class="layout-copy layout-copy--kicker">地点 · 时刻</p>'
    body = "" if variant == "scenery" else '<p class="layout-copy layout-copy--body">一句感受或细节</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-layout="web" data-layout-engine="screens">
<head>
<meta charset="utf-8" />
<title>probe · {PATTERN_EDITORIAL_4MIX} · {variant}</title>
<link rel="stylesheet" href="{screens_css}" />
<link rel="stylesheet" href="{overlays_css}" />
<style>
  body {{
    margin: 0;
    padding: 24px;
    background: #f4f1ea;
    min-width: 1440px;
  }}
  .probe-rail {{
    width: min(100%, 1200px);
    margin: 0 auto;
  }}
</style>
</head>
<body>
<div class="probe-rail">
  <div class="layout-screen" data-pattern="{PATTERN_EDITORIAL_4MIX}"
       data-layout-hint="{LAYOUT_HINT_EDITORIAL_4MIX}">
    {kicker}
    <div class="layout-screen__grid layout-screen__grid--editorial-4mix">
      {"".join(slots_html)}
    </div>
    {body}
  </div>
</div>
</body>
</html>
"""


def run_editorial_4mix_screenshot_probe(
    *,
    update_baselines: bool = False,
    tolerance: float | None = None,
) -> dict[str, Any]:
    """Capture 4mix person/scenery probe PNGs (AC-4M-09 · skipped without playwright)."""
    from travelogue.layout_templates.probe_screenshot import (
        DEFAULT_PIXEL_TOLERANCE,
        _capture_png,
        compare_probe_png,
    )

    tol = DEFAULT_PIXEL_TOLERANCE if tolerance is None else tolerance
    try:
        import playwright  # noqa: F401
    except ImportError:
        return {"ok": True, "skipped": True, "reason": "playwright not installed"}

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for variant in ("person", "scenery"):
        probe_id = editorial_4mix_probe_id(variant)  # type: ignore[arg-type]
        html = build_editorial_4mix_probe_html(variant=variant)  # type: ignore[arg-type]
        try:
            png = _capture_png(html, width=1440, height=900)
        except Exception as exc:  # pragma: no cover
            warnings.append(f"{probe_id}: capture failed ({exc})")
            continue
        path = editorial_4mix_baseline_path(probe_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if update_baselines:
            path.write_bytes(png)
            rows.append({"templateId": probe_id, "baseline": str(path), "updated": True, "ok": True})
            continue
        if not path.is_file():
            warnings.append(
                f"{probe_id}: missing baseline PNG (run lte_probe_regress --update-baselines)"
            )
            rows.append(
                {
                    "templateId": probe_id,
                    "baseline": str(path),
                    "missingBaseline": True,
                    "ok": False,
                }
            )
            continue
        diff = compare_probe_png(png, path.read_bytes(), tolerance=tol)
        row = {"templateId": probe_id, "baseline": str(path), "updated": False, **diff}
        rows.append(row)
        if not diff["ok"]:
            warnings.append(
                f"{probe_id}: screenshot diff mad={diff['meanAbsDiff']:.2f} > {tol}"
            )

    ok = all(r.get("ok") for r in rows) if rows else True
    return {
        "ok": ok,
        "skipped": False,
        "compared": len([r for r in rows if not r.get("updated") and not r.get("missingBaseline")]),
        "updated": len([r for r in rows if r.get("updated")]),
        "rows": rows,
        "warnings": warnings,
    }


ROW_BBOX_JS = """
() => {
  const screen = document.querySelector('.layout-screen[data-pattern="screen-editorial-4mix"]');
  if (!screen) return null;
  const grid = screen.querySelector('.layout-screen__grid--editorial-4mix');
  if (!grid) return null;
  const slot = (n) => screen.querySelector(`.layout-slot[data-slot="${n}"]`);
  const rects = (ids) => ids.map((i) => slot(i).getBoundingClientRect());
  const gridRect = grid.getBoundingClientRect();
  const stageRect = screen.getBoundingClientRect();
  const row1 = rects([0, 1]);
  const row2 = rects([2, 3]);
  const landAreas = [0, 3].map((i) => {
    const s = slot(i).getBoundingClientRect();
    return (s.width * s.height) / (gridRect.width * gridRect.height);
  });
  return {
    row1TopDelta: Math.abs(row1[0].top - row1[1].top),
    row1BottomDelta: Math.abs(row1[0].bottom - row1[1].bottom),
    row2TopDelta: Math.abs(row2[0].top - row2[1].top),
    row2BottomDelta: Math.abs(row2[0].bottom - row2[1].bottom),
    landAreas,
    stageAspect: stageRect.width / stageRect.height,
    hasTone916: getComputedStyle(screen).aspectRatio === '9 / 16',
  };
}
"""
