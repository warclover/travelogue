"""Long-shot chapter pagination + WeChat UX (Plan A surface)."""



from __future__ import annotations
from tests._repo_root import repo_root

import json
import re
from pathlib import Path

import pytest

from travelogue.curation.chapter_items import count_chapter_screen_slots
from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_html, render_trip

ROOT = repo_root(__file__)
LONGSHOT_JS = ROOT / "templates" / "visual-journal" / "longshot.js"
TOOLBAR = ROOT / "templates" / "visual-journal" / "partials" / "longshot-toolbar.hbs"
LONGSHOT_CSS = ROOT / "templates" / "visual-journal" / "longshot.css"
LINZHI = ROOT / "trips" / "linzhi"


def test_longshot_js_chapter_mode_api() -> None:
    js = LONGSHOT_JS.read_text(encoding="utf-8")
    assert "captureLongShotByChapter" in js
    assert "MODE_CHAPTER" in js
    assert "SINGLE_PAGE_MAX_IMAGES = 30" in js
    assert "applyChapterVisibility" in js
    assert "showPreviewModal" in js
    assert "longshot-wechat-banner" in js
    assert "guardFileProtocol" in js
    assert "longshot-file-banner" in js


def test_toolbar_caption_controls() -> None:
    html = TOOLBAR.read_text(encoding="utf-8")
    assert "longshot-save" in html
    assert "share-toggle" in html
    assert "longshot-caption-toggle" in html
    assert "longshot-caption-edit" in html
    assert "data-longshot-mode" not in html
    assert "data-longshot-scale-option" not in html


def test_export_panel_in_longshot_js() -> None:
    js = LONGSHOT_JS.read_text(encoding="utf-8")
    assert "openExportPanel" in js
    assert "longshot-export-sheet" in js
    assert "data-longshot-mode" in js
    assert "data-longshot-scale-option" in js
    assert "data-longshot-include-captions" in js
    assert "data-caption-display" in js
    assert "applyCaptionDisplay" in js
    assert "initCaptionDisplay" in js


def test_longshot_css_caption_display() -> None:
    css = LONGSHOT_CSS.read_text(encoding="utf-8")
    assert "data-caption-display" in css
    assert ".longshot-toolbar__btn--secondary" in css
    assert "body.longshot-capturing .cover-hero__text h1" in css
    assert "font-size: 26px" in css


def test_longshot_split_mat_title_horizontal_on_capture() -> None:
    """split-mat 竖排书名在长图截图态须横排，且按字数分档字号。"""
    css = LONGSHOT_CSS.read_text(encoding="utf-8")
    marker = 'body.longshot-capturing .cover-opening[data-cover-opening="split-mat"] .cover-opening__title--vertical,'
    start = css.index(marker)
    end = css.index("/* ≤8 字", start)
    capture_block = css[start:end]
    assert "writing-mode: horizontal-tb" in capture_block
    assert "vertical-rl" not in capture_block
    assert "clamp(24px, 6.5vw, 28px)" in css
    assert "font-size: 21px" in css
    assert "font-size: 19px" in css


def test_longshot_css_preview_and_wechat() -> None:
    css = LONGSHOT_CSS.read_text(encoding="utf-8")
    assert ".longshot-preview" in css
    assert ".longshot-wechat-banner" in css
    assert ".longshot-export-sheet" in css
    assert ".longshot-segment__btn" in css


def test_longshot_surface_has_chapter_sections() -> None:
    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    chapters = re.findall(r'<section class="chapter"[^>]*data-chapter-id="([^"]+)"', html)
    assert len(chapters) >= 2
    slots = sum(count_chapter_screen_slots(ch) for ch in trip["chapters"])
    cards = len(re.findall(r'data-block="media-card"', html))
    assert cards >= slots


@pytest.mark.skipif(not LINZHI.is_dir(), reason="linzhi trip not present")
def test_linzhi_plan_a_longshot_surface() -> None:
    """Plan A: index-longshot from screens; bridge on index.html."""
    longshot = (LINZHI / LONGSHOT_INDEX_NAME).read_text(encoding="utf-8")
    index = (LINZHI / "index.html").read_text(encoding="utf-8")

    assert 'data-layout="longshot"' in longshot
    assert 'data-longshot="on"' in longshot
    assert 'data-block="layout-screen"' not in longshot
    assert "longshot-save" in longshot
    assert "openExportPanel" in (LINZHI / "longshot.js").read_text(encoding="utf-8")

    assert f'data-longshot-mobile-url="{LONGSHOT_INDEX_NAME}"' in index
    assert 'data-longshot-bridge="on"' in index

    chapters = len(re.findall(r'data-chapter-id="', longshot))
    imgs = len(re.findall(r"<img ", longshot))
    assert chapters >= 4
    assert imgs > 30


@pytest.mark.skipif(not (LINZHI / "trip.json").is_file(), reason="linzhi trip.json missing")
def test_render_linzhi_writes_longshot_bundle() -> None:
    render_trip(LINZHI / "trip.json", validate=False, layout_engine="screens")
    assert (LINZHI / LONGSHOT_INDEX_NAME).is_file()
    assert (LINZHI / "longshot.js").is_file()
    js = (LINZHI / "longshot.js").read_text(encoding="utf-8")
    assert "captureLongShotByChapter" in js
