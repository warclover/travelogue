"""LTE Playwright probe screenshot diff (V-P16-07)."""

from __future__ import annotations

import pytest

from travelogue.layout_templates.probe_screenshot import (
    build_probe_html,
    compare_probe_png,
    run_screenshot_probe,
)
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_build_probe_html_contains_grid_class() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    tpl = engine.get("screen-portrait-3")
    html = build_probe_html(tpl)
    assert tpl.render_grid_class in html
    assert "grid-template-columns" in html


@pytest.mark.unit
def test_compare_identical_pngs() -> None:
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (64, 36), color=(10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    out = compare_probe_png(raw, raw)
    assert out["ok"] is True
    assert out["meanAbsDiff"] == 0.0


@pytest.mark.unit
def test_run_screenshot_probe_missing_baseline_fails() -> None:
    from travelogue.layout_templates.probe_screenshot import baseline_path, run_screenshot_probe

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    path = baseline_path("screen-portrait-3")
    backup = path.read_bytes() if path.is_file() else None
    if path.is_file():
        path.unlink()
    try:
        pytest.importorskip("playwright")
        out = run_screenshot_probe(engine, template_ids=("screen-portrait-3",))
        if out.get("skipped"):
            pytest.skip(out.get("reason", "playwright unavailable"))
        assert out["ok"] is False
        assert any("missing baseline" in w for w in out.get("warnings") or [])
    finally:
        if backup is not None:
            path.write_bytes(backup)


@pytest.mark.unit
def test_run_screenshot_probe_skips_without_playwright() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    pytest.importorskip("playwright")
    out = run_screenshot_probe(engine, update_baselines=True)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["compared"] >= 1
    assert out["ok"] is True
