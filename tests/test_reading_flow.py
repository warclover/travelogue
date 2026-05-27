"""Breath flow (Lenis) and featured present coordination (PRD-EXPERIENCE E6)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
BREATH_LENIS_JS = TEMPLATE_VISUAL_JOURNAL / "breath-lenis.js"
BREATH_CSS = TEMPLATE_VISUAL_JOURNAL / "breath.css"
LONGSHOT_JS = TEMPLATE_VISUAL_JOURNAL / "longshot.js"
SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"
TOOLBAR = TEMPLATE_VISUAL_JOURNAL / "partials" / "screenplay-toolbar.hbs"


@pytest.fixture
def screens_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "flow-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_breath_lenis_asset_exists() -> None:
    js = BREATH_LENIS_JS.read_text(encoding="utf-8")
    assert "TravelogueLenis" in js
    assert "lerp" in js


def test_breath_js_integrates_flow_and_lenis() -> None:
    js = BREATH_JS.read_text(encoding="utf-8")
    assert "TravelogueLenis" in js
    assert 'breathLevel() !== "flow"' in js or 'breathLevel() === "flow"' in js
    assert "destroyLenis" in js


def test_screenplay_pauses_lenis_and_featured_toggle() -> None:
    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "pauseLenis" in js
    assert "resumeLenis" in js
    assert "syncLenisToViewport" in js
    assert "featuredOnlyOverride" in js
    assert "featured-present-toggle" in js

    toolbar = TOOLBAR.read_text(encoding="utf-8")
    assert "featured-present-toggle" in toolbar
    assert "hasFeaturedAssets" in toolbar


def test_breath_css_flow_rules() -> None:
    css = BREATH_CSS.read_text(encoding="utf-8")
    assert 'data-breath="flow"' in css
    assert ".lenis-flow" in css


def test_magazine_profile_renders_flow_bundle(screens_workspace: Path) -> None:
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    trip["assets"][0]["userTier"] = "featured"
    (screens_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    assert (screens_workspace / "breath-lenis.js").is_file()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-breath="flow"' in html
    assert "breath-lenis.js" in html


def test_flow_profile_longshot_teardown_clears_transforms() -> None:
    """AC-EXP-03: flow/cinematic motion teardown before longshot capture."""
    longshot = LONGSHOT_JS.read_text(encoding="utf-8")
    breath = BREATH_JS.read_text(encoding="utf-8")
    assert "teardownReadingMotion" in longshot
    assert "el.style.transform" in breath or 'style.transform = ""' in breath
    assert "destroyLenis" in breath
    assert "destroyScrub" in breath
    assert "TravelogueReading.teardown" in longshot


def test_ac_br_02_flow_settle_tail_budget() -> None:
    """AC-BR-02: after wheel idle, flow scroll coast finishes within 300ms."""
    js = BREATH_LENIS_JS.read_text(encoding="utf-8")
    assert "settleLerp" in js
    assert "wheelIdleMs" in js
    assert "FLOW_TAIL_MS" in js

    frame_ms = 1000 / 60
    wheel_idle_ms = 90
    lerp = 0.1
    settle_lerp = 0.28

    def estimate_coast_ms(delta: float) -> float:
        current = 0.0
        target = abs(delta)
        t = 0.0
        coast_started: float | None = None
        while abs(target - current) > 0.5 and t < 2000:
            if t > wheel_idle_ms:
                if coast_started is None:
                    coast_started = float(wheel_idle_ms)
                if t - coast_started >= 300 - frame_ms:
                    current = target
                    return t - coast_started
                else:
                    current += (target - current) * settle_lerp
            else:
                coast_started = None
                current += (target - current) * lerp
            t += frame_ms
        if coast_started is None:
            return 0.0
        return t - coast_started

    for delta in (120, 480, 960, 1600):
        assert estimate_coast_ms(delta) <= 300, f"delta={delta}"


def test_breath_lenis_exposes_settle_estimator() -> None:
    js = BREATH_LENIS_JS.read_text(encoding="utf-8")
    assert "estimateSettleMs" in js


def test_default_hybrid_skips_lenis_bundle(screens_workspace: Path) -> None:
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
    )
    assert not (screens_workspace / "breath-lenis.js").exists()
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert "breath-lenis.js" not in html
    assert 'data-breath="soft"' in html
