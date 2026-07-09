"""Playwright probe screenshots for LTE templates (V-P16-07)."""

from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from travelogue.layout_templates.css_gen import grid_templates_for, slot_cells
from travelogue.layout_templates.models import TemplateDef
from travelogue.layout_templates.registry import get_engine

PACKAGE_ROOT = Path(__file__).resolve().parent
BASELINE_DIR = PACKAGE_ROOT / "probes" / "baselines"
DEFAULT_PROBE_TEMPLATE_IDS: tuple[str, ...] = (
    "screen-mosaic-5-hero-3-2-plus-4",
    "screen-portrait-3",
)

# Max mean absolute channel diff (0–255) for cover/contain layout smoke.
DEFAULT_PIXEL_TOLERANCE = 12.0


def baseline_path(template_id: str) -> Path:
    return BASELINE_DIR / f"{template_id}.png"


def build_probe_html(template: TemplateDef) -> str:
    """Minimal standalone HTML exercising grid placement (object-fit cover fill)."""
    cols, rows = grid_templates_for(template)
    stage = template.stage
    gap = stage.gap or "3px"
    grid_class = template.render_grid_class
    slot_rules: list[str] = []
    slot_nodes: list[str] = []
    for slot in template.slots:
        cells = slot_cells(stage, slot.rect)
        if not cells:
            continue
        cols_idx = sorted(c for c, _ in cells)
        rows_idx = sorted(r for _, r in cells)
        c0, c1 = cols_idx[0], cols_idx[-1]
        r0, r1 = rows_idx[0], rows_idx[-1]
        hue = (slot.index * 47) % 360
        slot_rules.append(
            f".{grid_class} .layout-slot[data-slot=\"{slot.index}\"] {{"
            f"grid-column: {c0} / {c1 + 1}; grid-row: {r0} / {r1 + 1};"
            f"background: hsl({hue}, 55%, 42%);"
            f"}}"
        )
        slot_nodes.append(
            f'<div class="layout-slot" data-slot="{slot.index}">'
            f'<div class="layout-slot__fill"></div></div>'
        )
    return f"""<!DOCTYPE html>
<html lang="en" data-layout="web">
<head>
<meta charset="utf-8" />
<style>
html, body {{ margin: 0; padding: 0; background: #111; }}
.layout-screen {{
  width: 960px;
  aspect-ratio: {stage.aspect.replace(":", " / ")};
  margin: 0;
  overflow: hidden;
  background: #222;
}}
.{grid_class} {{
  display: grid;
  width: 100%;
  height: 100%;
  gap: {gap};
  grid-template-columns: {cols};
  grid-template-rows: {rows};
}}
.layout-slot {{ min-width: 0; min-height: 0; overflow: hidden; }}
.layout-slot__fill {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
}}
{chr(10).join(slot_rules)}
</style>
</head>
<body>
<div class="layout-screen">
  <div class="layout-screen__grid {grid_class}">
    {chr(10).join(slot_nodes)}
  </div>
</div>
</body>
</html>
"""


def playwright_capture_available() -> tuple[bool, str | None]:
    """True when the playwright package and Chromium binary are present."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright not installed"
    try:
        with sync_playwright() as p:
            exe = Path(p.chromium.executable_path)
            if not exe.is_file():
                return False, "playwright browser unavailable (chromium not installed)"
    except Exception as exc:  # pragma: no cover - env specific
        return False, f"playwright browser unavailable ({exc})"
    return True, None


def _capture_png(html: str, *, width: int = 980, height: int = 620) -> bytes:
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "probe.html"
        html_path.write_text(html, encoding="utf-8")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(html_path.resolve().as_uri())
            page.wait_for_timeout(100)
            png = page.locator(".layout-screen").screenshot(type="png")
            browser.close()
            return png


def _mean_abs_diff(a_bytes: bytes, b_bytes: bytes) -> float:
    from PIL import Image

    a = Image.open(BytesIO(a_bytes)).convert("RGB")
    b = Image.open(BytesIO(b_bytes)).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = 0.0
    count = a.size[0] * a.size[1] * 3
    pa, pb = a.tobytes(), b.tobytes()
    for x, y in zip(pa, pb, strict=False):
        diff += abs(x - y)
    return diff / max(count, 1)


def compare_probe_png(actual: bytes, baseline: bytes, *, tolerance: float = DEFAULT_PIXEL_TOLERANCE) -> dict[str, Any]:
    mad = _mean_abs_diff(actual, baseline)
    return {
        "meanAbsDiff": round(mad, 4),
        "tolerance": tolerance,
        "ok": mad <= tolerance,
    }


def run_screenshot_probe(
    engine=None,
    *,
    template_ids: tuple[str, ...] | None = None,
    update_baselines: bool = False,
    tolerance: float = DEFAULT_PIXEL_TOLERANCE,
) -> dict[str, Any]:
    """Capture probe PNGs and diff against baselines (skipped without playwright)."""
    available, reason = playwright_capture_available()
    if not available:
        return {"ok": True, "skipped": True, "reason": reason or "playwright unavailable"}

    engine = engine or get_engine()
    ids = template_ids or DEFAULT_PROBE_TEMPLATE_IDS
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for tid in ids:
        try:
            template = engine.get(tid)
        except KeyError:
            warnings.append(f"{tid}: template not found")
            continue
        html = build_probe_html(template)
        try:
            png = _capture_png(html)
        except Exception as exc:  # pragma: no cover - env specific
            warnings.append(f"{tid}: capture failed ({exc})")
            continue
        path = baseline_path(tid)
        if update_baselines:
            path.write_bytes(png)
            rows.append({"templateId": tid, "baseline": str(path), "updated": True, "ok": True})
            continue
        if not path.is_file():
            warnings.append(f"{tid}: missing baseline PNG (run lte_probe_regress --update-baselines)")
            rows.append(
                {
                    "templateId": tid,
                    "baseline": str(path),
                    "updated": False,
                    "missingBaseline": True,
                    "ok": False,
                }
            )
            continue
        baseline = path.read_bytes()
        diff = compare_probe_png(png, baseline, tolerance=tolerance)
        row = {"templateId": tid, "baseline": str(path), "updated": False, **diff}
        rows.append(row)
        if not diff["ok"]:
            warnings.append(
                f"{tid}: screenshot diff mad={diff['meanAbsDiff']:.2f} > {tolerance}"
            )

    return {
        "ok": len(warnings) == 0,
        "skipped": False,
        "compared": len(rows),
        "warnings": warnings,
        "rows": rows,
    }
