"""Playwright probe for screen-portrait-3-editorial (PRD §12.5 · probe ≠ web render)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from travelogue.layout_engine.editorial.portrait_row import (
    editorial_row_ar_from_assets,
)
from travelogue.paths import JOURNAL_SCREENS_CSS, TEMPLATE_VISUAL_JOURNAL

EditorialProbeVariant = Literal["contain", "cover"]

OVERLAYS_CSS = TEMPLATE_VISUAL_JOURNAL / "journal-screens-overlays.css"

# Fixed probe assets (native AR) · stable across runs.
_PROBE_ASSETS: tuple[tuple[int, int, str], ...] = (
    (800, 1200, "#5b7a99"),
    (900, 1600, "#7a6b5c"),
    (700, 1400, "#6b8f71"),
)

EDITORIAL_PROBE_IDS: tuple[str, ...] = (
    "screen-portrait-3-editorial-contain",
    "screen-portrait-3-editorial-cover",
)


def editorial_probe_id(variant: EditorialProbeVariant) -> str:
    return f"screen-portrait-3-editorial-{variant}"


def editorial_baseline_path(probe_id: str) -> Path:
    from travelogue.layout_templates.probe_screenshot import BASELINE_DIR

    return BASELINE_DIR / f"{probe_id}.png"


def _svg_data_uri(width: int, height: int, color: str) -> str:
    import base64

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="{color}"/>'
        f'<rect x="0" y="{int(height * 0.85)}" width="100%" height="{int(height * 0.15)}" '
        f'fill="rgba(0,0,0,0.12)"/></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_editorial_probe_html(*, variant: EditorialProbeVariant) -> str:
    """Minimal page exercising editorial overlay CSS (linked from repo templates)."""
    fit_class = f"layout-slot__img--{variant}"
    asset_ids = [f"probe-{i}" for i in range(3)]
    assets_map = {
        aid: {"id": aid, "nativeWidth": w, "nativeHeight": h}
        for aid, (w, h, _color) in zip(asset_ids, _PROBE_ASSETS, strict=True)
    }
    row_style = ""
    if variant == "cover":
        ar = editorial_row_ar_from_assets(asset_ids, assets_map)
        row_style = f' style="--editorial-row-ar: {ar:.6f};"'

    slots_html = []
    for idx, (w, h, color) in enumerate(_PROBE_ASSETS):
        src = _svg_data_uri(w, h, color)
        slots_html.append(
            f'<figure class="layout-slot" data-slot="{idx}">'
            f'<img class="layout-slot__img {fit_class}" alt="" src="{src}" />'
            f"</figure>"
        )

    screens_css = JOURNAL_SCREENS_CSS.as_uri()
    overlays_css = OVERLAYS_CSS.as_uri()

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-layout="web" data-layout-engine="screens">
<head>
<meta charset="utf-8" />
<title>probe · screen-portrait-3-editorial · {variant}</title>
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
  <div class="layout-screen" data-pattern="screen-portrait-3-editorial"
       data-layout-hint="portrait-row-editorial"{row_style}>
    <div class="layout-screen__grid layout-screen__grid--3col">
      {"".join(slots_html)}
    </div>
  </div>
</div>
</body>
</html>
"""


def run_editorial_screenshot_probe(
    *,
    update_baselines: bool = False,
    tolerance: float | None = None,
) -> dict[str, Any]:
    """Capture editorial contain/cover probe PNGs (skipped without playwright)."""
    from travelogue.layout_templates.probe_screenshot import (
        DEFAULT_PIXEL_TOLERANCE,
        _capture_png,
        compare_probe_png,
        playwright_capture_available,
    )

    tol = DEFAULT_PIXEL_TOLERANCE if tolerance is None else tolerance
    available, reason = playwright_capture_available()
    if not available:
        return {"ok": True, "skipped": True, "reason": reason or "playwright unavailable"}

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for variant in ("contain", "cover"):
        probe_id = editorial_probe_id(variant)
        html = build_editorial_probe_html(variant=variant)
        try:
            png = _capture_png(html, width=1440, height=900)
        except Exception as exc:  # pragma: no cover
            warnings.append(f"{probe_id}: capture failed ({exc})")
            continue
        path = editorial_baseline_path(probe_id)
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
