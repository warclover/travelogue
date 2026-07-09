"""PRD screen-editorial-4mix · PR-1 P0 + PR-2 P1a tests."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from travelogue.config import AppConfig
from travelogue.config.layout import Editorial4MixConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.editorial.four_mix import (
    LAYOUT_HINT_EDITORIAL_4MIX,
    PATTERN_EDITORIAL_4MIX,
    apply_editorial_4mix_to_screen,
    chess_order_asset_ids,
    is_editorial_4mix_enabled,
    maybe_editorial_4mix,
)
from travelogue.layout_engine.mosaic.builders import build_screen
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_4,
)
from travelogue.layout_engine.mosaic.pattern_catalog import default_registry
from travelogue.layout_engine.planner.screen_planner import _fits_for_screen, grid_class_for_pattern
from travelogue.layout_templates.probe_editorial_4mix import (
    ROW_BBOX_JS,
    build_editorial_4mix_probe_html,
)
from travelogue.layout_templates.registry import get_layout_template, reset_engine_cache_for_tests
from travelogue.paths import JOURNAL_SCREENS_CSS, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.context import build_layout_screen


def _probe_html_with_inlined_css() -> str:
    from travelogue.layout_templates.probe_editorial import OVERLAYS_CSS

    html = build_editorial_4mix_probe_html(variant="person")
    css = (
        JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
        + "\n"
        + OVERLAYS_CSS.read_text(encoding="utf-8")
    )
    stripped = re.sub(r'<link rel="stylesheet" href="[^"]+" />\s*', "", html)
    return stripped.replace("</head>", f"<style>\n{css}\n</style>\n</head>")


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


def _cfg_with_4mix(*, enabled: bool = True) -> AppConfig:
    from travelogue.config import get_config

    base = get_config()
    e4 = Editorial4MixConfig(enabled=enabled)
    layout = replace(base.layout, editorial_4mix=e4)
    return replace(base, layout=layout)


def _mixed_4_assets() -> tuple[dict[str, str], dict[str, dict]]:
    aspects = {
        "l1": "landscape",
        "l2": "landscape",
        "p1": "portrait",
        "p2": "portrait",
    }
    assets_map = {
        "l1": {
            "id": "l1",
            "nativeWidth": 1600,
            "nativeHeight": 900,
            "takenAt": "2024-06-01T10:00:00Z",
            "layoutEligible": True,
            "sharpness": 90,
        },
        "l2": {
            "id": "l2",
            "nativeWidth": 1400,
            "nativeHeight": 800,
            "takenAt": "2024-06-01T10:01:00Z",
            "layoutEligible": True,
            "sharpness": 70,
        },
        "p1": {
            "id": "p1",
            "nativeWidth": 900,
            "nativeHeight": 1600,
            "takenAt": "2024-06-01T10:02:00Z",
            "layoutEligible": True,
            "tags": ["person"],
        },
        "p2": {
            "id": "p2",
            "nativeWidth": 800,
            "nativeHeight": 1400,
            "takenAt": "2024-06-01T10:03:00Z",
            "layoutEligible": True,
            "tags": ["person"],
        },
    }
    return aspects, assets_map


@pytest.mark.unit
def test_lte_template_loads() -> None:
    tpl = get_layout_template(PATTERN_EDITORIAL_4MIX)
    assert tpl.id == PATTERN_EDITORIAL_4MIX
    assert tpl.status == "experimental"
    assert tpl.render_grid_class == "layout-screen__grid--editorial-4mix"
    assert tpl.photo_count_min == 4
    assert tpl.photo_count_max == 4
    assert tuple(int(x) for x in (tpl.stage.cols or ())) == (2, 3)
    assert tuple(int(x) for x in (tpl.stage.rows or ())) == (3, 2)


@pytest.mark.unit
def test_grid_class_for_pattern() -> None:
    assert grid_class_for_pattern(PATTERN_EDITORIAL_4MIX) == (
        "layout-screen__grid--editorial-4mix"
    )


@pytest.mark.unit
def test_fits_for_4mix_person_land_cover_port_contain() -> None:
    assets = {
        "l1": {"id": "l1", "tags": ["scenery"]},
        "p1": {"id": "p1", "tags": ["person"]},
        "p2": {"id": "p2", "tags": ["person"]},
        "l2": {"id": "l2", "tags": ["scenery"]},
    }
    fits = _fits_for_screen(
        PATTERN_EDITORIAL_4MIX,
        ["l1", "p1", "p2", "l2"],
        assets_map=assets,
    )
    assert fits == ["cover", "contain", "contain", "cover"]


@pytest.mark.unit
def test_skip_stage_aspect_in_render_context() -> None:
    screen = {
        "patternId": PATTERN_EDITORIAL_4MIX,
        "layoutHint": LAYOUT_HINT_EDITORIAL_4MIX,
        "layoutGeometry": {"stageAspect": "16:9", "gridClass": "layout-screen__grid--editorial-4mix"},
        "slots": [
            {"assetId": "a", "slot": 0, "fit": "cover"},
            {"assetId": "b", "slot": 1, "fit": "contain"},
            {"assetId": "c", "slot": 2, "fit": "contain"},
            {"assetId": "d", "slot": 3, "fit": "cover"},
        ],
    }
    assets = {
        aid: {"id": aid, "nativeWidth": 1200, "nativeHeight": 800 if aid in ("a", "d") else 900}
        for aid in ("a", "b", "c", "d")
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="t",
        export_layout="web",
    )
    assert "--screen-aspect:" not in ctx["screenStyle"]
    assert ctx["gridClass"] == "layout-screen__grid--editorial-4mix"


@pytest.mark.unit
def test_css_dual_file_has_4mix_overlay_rules() -> None:
    main_css = JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
    overlays = (TEMPLATE_VISUAL_JOURNAL / "journal-screens-overlays.css").read_text(encoding="utf-8")
    for css in (main_css, overlays):
        assert 'data-pattern="screen-editorial-4mix"' in css
        assert "layout-screen__grid--editorial-4mix" in css
        assert "object-position: bottom center" in css
        assert ':not([data-pattern="screen-editorial-4mix"])' in css


@pytest.mark.e2e
def test_ac_4m_03_land_slot_area_ratio() -> None:
    """AC-4M-03 · Land TL/BR 槽面积 22–28% 舞台（@1440）。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _probe_html_with_inlined_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.set_content(html, wait_until="load")
        result = page.evaluate(ROW_BBOX_JS)
        browser.close()
    assert result is not None
    assert all(0.22 <= a <= 0.28 for a in result["landAreas"]), result["landAreas"]


@pytest.mark.e2e
def test_ac_4m_04_row1_bbox_align() -> None:
    """AC-4M-04 · Row1 TL 横与 TR 竖顶/底 bbox 偏差 ≤2px。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _probe_html_with_inlined_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.set_content(html, wait_until="load")
        result = page.evaluate(ROW_BBOX_JS)
        browser.close()
    assert result is not None
    assert result["row1TopDelta"] <= 2.5, result
    assert result["row1BottomDelta"] <= 2.5, result


@pytest.mark.e2e
def test_ac_4m_05_row2_bbox_align() -> None:
    """AC-4M-05 · Row2 BL 竖与 BR 横顶/底 bbox 偏差 ≤2px。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _probe_html_with_inlined_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.set_content(html, wait_until="load")
        result = page.evaluate(ROW_BBOX_JS)
        browser.close()
    assert result is not None
    assert result["row2TopDelta"] <= 2.5, result
    assert result["row2BottomDelta"] <= 2.5, result


@pytest.mark.e2e
def test_ac_4m_07_intrinsic_stage_not_916() -> None:
    """AC-4M-07 · 无固定 9:16 tone 信箱；intrinsic 舞台。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _probe_html_with_inlined_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.set_content(html, wait_until="load")
        result = page.evaluate(ROW_BBOX_JS)
        browser.close()
    assert result is not None
    assert result["hasTone916"] is False
    assert result["stageAspect"] > 1.2


@pytest.mark.unit
def test_is_editorial_4mix_enabled_priority() -> None:
    cfg = _cfg_with_4mix(enabled=False)
    trip = {"tripId": "demo", "export": {"editorial4Mix": True}}
    assert is_editorial_4mix_enabled(trip, cfg)
    cfg2 = replace(
        cfg,
        layout=replace(
            cfg.layout,
            editorial_4mix=Editorial4MixConfig(
                enabled=False,
                trip_allowlist=("on-allowlist",),
            ),
        ),
    )
    assert is_editorial_4mix_enabled({"tripId": "on-allowlist"}, cfg2)
    assert not is_editorial_4mix_enabled({"tripId": "other"}, cfg2)


@pytest.mark.unit
def test_editorial_4mix_chess_reorder() -> None:
    aspects, assets_map = _mixed_4_assets()
    ordered = chess_order_asset_ids(
        ["p1", "l2", "p2", "l1"],
        assets_map,
        aspects=aspects,
    )
    assert ordered is not None
    assert ordered[0] in ("l1", "l2")
    assert ordered[3] in ("l1", "l2")
    assert ordered[0] != ordered[3]
    assert ordered[1] in ("p1", "p2")
    assert ordered[2] in ("p1", "p2")
    assert ordered[1] != ordered[2]


@pytest.mark.unit
def test_maybe_editorial_4mix_replaces_p2l2_when_enabled() -> None:
    aspects, assets_map = _mixed_4_assets()
    ids = ["l1", "p1", "p2", "l2"]
    cfg = _cfg_with_4mix(enabled=True)
    pid, hint = maybe_editorial_4mix(
        PATTERN_PORTRAIT_2_LANDSCAPE_2,
        ids,
        assets_map,
        cfg=cfg,
        aspects=aspects,
    )
    assert pid == PATTERN_EDITORIAL_4MIX
    assert hint == LAYOUT_HINT_EDITORIAL_4MIX


@pytest.mark.unit
def test_maybe_editorial_4mix_disabled_is_noop() -> None:
    aspects, assets_map = _mixed_4_assets()
    ids = ["l1", "p1", "p2", "l2"]
    cfg = _cfg_with_4mix(enabled=False)
    pid, hint = maybe_editorial_4mix(
        PATTERN_PORTRAIT_2_LANDSCAPE_2,
        ids,
        assets_map,
        cfg=cfg,
        aspects=aspects,
    )
    assert pid == PATTERN_PORTRAIT_2_LANDSCAPE_2
    assert hint is None


@pytest.mark.unit
def test_build_screen_p2l2_becomes_4mix_when_enabled() -> None:
    aspects, assets_map = _mixed_4_assets()
    reg = default_registry()
    pattern = reg[PATTERN_PORTRAIT_2_LANDSCAPE_2]
    ordered = ["p1", "l1", "l2", "p2"]
    cfg = _cfg_with_4mix(enabled=True)
    screen = build_screen(
        pattern,
        ordered,
        assets_map=assets_map,
        cfg=cfg,
    )
    assert screen["patternId"] == PATTERN_EDITORIAL_4MIX
    assert screen["layoutHint"] == LAYOUT_HINT_EDITORIAL_4MIX
    assert [s["slot"] for s in screen["slots"]] == [0, 1, 2, 3]
    assert screen["slots"][0]["role"] == "landscape"
    assert screen["slots"][1]["role"] == "portrait"
    assert screen.get("layoutGeometry", {}).get("gridClass") == (
        "layout-screen__grid--editorial-4mix"
    )


@pytest.mark.unit
def test_editorial_4mix_prefers_over_mosaic_4_when_enabled() -> None:
    aspects, assets_map = _mixed_4_assets()
    reg = default_registry()
    p2l2 = build_screen(
        reg[PATTERN_PORTRAIT_2_LANDSCAPE_2],
        ["p1", "l1", "l2", "p2"],
        assets_map=assets_map,
        cfg=_cfg_with_4mix(enabled=True),
    )
    p4 = build_screen(
        reg[PATTERN_PORTRAIT_4],
        ["p1", "p2", "p1", "p2"],
        assets_map=assets_map,
        cfg=_cfg_with_4mix(enabled=True),
    )
    assert p2l2["patternId"] == PATTERN_EDITORIAL_4MIX
    assert p4["patternId"] == PATTERN_PORTRAIT_4


@pytest.mark.unit
def test_editorial_composite_mutex_2land_and_4mix() -> None:
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.can_emit_pattern(PATTERN_EDITORIAL_4MIX)
    st.note_screen(PATTERN_EDITORIAL_4MIX)
    assert not st.can_emit_pattern(PATTERN_EDITORIAL_4MIX)
    assert not st.can_emit_pattern("screen-editorial-2land")


@pytest.mark.unit
def test_4mix_not_counted_as_dense_collage() -> None:
    from travelogue.layout_contract.planner_state import is_dense_collage_pattern

    assert not is_dense_collage_pattern(PATTERN_EDITORIAL_4MIX)


@pytest.mark.unit
def test_apply_editorial_4mix_reorders_slots() -> None:
    aspects, assets_map = _mixed_4_assets()
    screen = {
        "patternId": PATTERN_PORTRAIT_2_LANDSCAPE_2,
        "slots": [
            {"assetId": "p1", "slot": 0, "fit": "contain", "role": "portrait"},
            {"assetId": "l1", "slot": 1, "fit": "cover", "role": "landscape"},
            {"assetId": "l2", "slot": 2, "fit": "cover", "role": "landscape"},
            {"assetId": "p2", "slot": 3, "fit": "contain", "role": "portrait"},
        ],
    }
    out = apply_editorial_4mix_to_screen(
        screen,
        assets_map,
        cfg=_cfg_with_4mix(enabled=True),
        aspects=aspects,
    )
    assert out["patternId"] == PATTERN_EDITORIAL_4MIX
    aids = [s["assetId"] for s in out["slots"]]
    assert aids[0] in ("l1", "l2") and aids[3] in ("l1", "l2")
    assert aids[1] in ("p1", "p2") and aids[2] in ("p1", "p2")


def _4mix_screen(*, copy: dict | None = None) -> dict:
    screen = {
        "screenId": "ch01-s4mix",
        "patternId": PATTERN_EDITORIAL_4MIX,
        "layoutHint": LAYOUT_HINT_EDITORIAL_4MIX,
        "layoutGeometry": {"gridClass": "layout-screen__grid--editorial-4mix"},
        "slots": [
            {"assetId": "l1", "slot": 0, "fit": "cover", "role": "landscape"},
            {"assetId": "p1", "slot": 1, "fit": "contain", "role": "portrait"},
            {"assetId": "p2", "slot": 2, "fit": "contain", "role": "portrait"},
            {"assetId": "l2", "slot": 3, "fit": "cover", "role": "landscape"},
        ],
    }
    if copy is not None:
        screen["copy"] = copy
    return screen


def _4mix_assets_map() -> dict[str, dict]:
    _, assets = _mixed_4_assets()
    return assets


@pytest.mark.unit
def test_build_layout_screen_editorial_4mix_copy_context() -> None:
    ctx = build_layout_screen(
        _4mix_screen(copy={"kicker": "林芝 · 清晨", "body": "云开了半面。"}),
        _4mix_assets_map(),
        meta_title="t",
        export_layout="web",
        chapter_id="ch-01",
        is_draft=True,
    )
    assert ctx["hasCopyKicker"] is True
    assert ctx["copyKicker"] == "林芝 · 清晨"
    assert ctx["editCopyKickerPath"] == "chapters.ch-01.screens.ch01-s4mix.copy.kicker"
    assert ctx["hasCopyBody"] is True
    assert ctx["copyBody"] == "云开了半面。"
    assert ctx["editCopyBodyPath"] == "chapters.ch-01.screens.ch01-s4mix.copy.body"


@pytest.mark.unit
def test_build_layout_screen_draft_empty_copy_shows_placeholders() -> None:
    ctx = build_layout_screen(
        _4mix_screen(),
        _4mix_assets_map(),
        meta_title="t",
        export_layout="web",
        chapter_id="ch-01",
        is_draft=True,
    )
    assert ctx["hasCopyKicker"] is True
    assert ctx["copyKicker"] == ""
    assert ctx["copyKickerEmpty"] is True
    assert ctx["hasCopyBody"] is True
    assert ctx["copyBodyEmpty"] is True


@pytest.mark.unit
def test_build_layout_screen_share_omits_empty_copy() -> None:
    ctx = build_layout_screen(
        _4mix_screen(),
        _4mix_assets_map(),
        meta_title="t",
        export_layout="web",
        chapter_id="ch-01",
        is_draft=False,
    )
    assert "hasCopyKicker" not in ctx
    assert "hasCopyBody" not in ctx


@pytest.mark.unit
def test_build_layout_screen_strips_copy_in_photos_share() -> None:
    ctx = build_layout_screen(
        _4mix_screen(copy={"kicker": "林芝", "body": "湖像刚醒。"}),
        _4mix_assets_map(),
        meta_title="t",
        export_layout="web",
        chapter_id="ch-01",
        strip_narrative_copy=True,
    )
    assert "hasCopyKicker" not in ctx
    assert "hasCopyBody" not in ctx


@pytest.mark.unit
def test_copy_patch_screen_copy_kicker_body() -> None:
    from travelogue.web.copy_patch import apply_copy_patches

    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "chapters": [{"id": "ch-01", "screens": [_4mix_screen()]}],
    }
    apply_copy_patches(
        trip,
        [
            {"path": "chapters.ch-01.screens.ch01-s4mix.copy.kicker", "value": "改 kicker"},
            {"path": "chapters.ch-01.screens.ch01-s4mix.copy.body", "value": "改 body"},
        ],
    )
    copy = trip["chapters"][0]["screens"][0]["copy"]
    assert copy["kicker"] == "改 kicker"
    assert copy["body"] == "改 body"


@pytest.mark.unit
def test_copy_display_css_hides_layout_copy() -> None:
    css = (TEMPLATE_VISUAL_JOURNAL / "copy-display.css").read_text(encoding="utf-8")
    assert 'html[data-copy-display="photos"] .layout-copy' in css


def _4mix_render_trip(*, copy: dict | None = None) -> dict:
    aspects, assets_map = _mixed_4_assets()
    assets = []
    for aid, asset in assets_map.items():
        w = int(asset["nativeWidth"])
        h = int(asset["nativeHeight"])
        assets.append(
            {
                **asset,
                "type": "image",
                "width": w,
                "height": h,
                "paths": {"w800": f"assets/{aid}-w800.webp", "w1600": f"assets/{aid}-w1600.webp"},
            }
        )
    return {
        "tripId": "4mix-copy-render",
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "meta": {"title": "测试", "hook": ""},
        "coverAssetId": "l1",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": assets,
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "章",
                "screens": [_4mix_screen(copy=copy)],
            }
        ],
    }


@pytest.mark.unit
def test_render_4mix_copy_inline_edit_paths() -> None:
    from travelogue.render.engine import render_html

    trip = _4mix_render_trip(copy={"kicker": "林芝 · 清晨", "body": "慢得不像话。"})
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        reading_profile_override="legacy",
    )
    assert 'data-pattern="screen-editorial-4mix"' in html
    assert 'data-editable="screen-copy-kicker"' in html
    assert 'data-edit-path="chapters.ch-01.screens.ch01-s4mix.copy.kicker"' in html
    assert "林芝 · 清晨" in html
    assert "慢得不像话。" in html


@pytest.mark.unit
def test_render_4mix_photos_share_hides_copy_via_css_attr() -> None:
    from travelogue.render.copy_display import COPY_DISPLAY_PHOTOS
    from travelogue.render.engine import render_html

    trip = _4mix_render_trip(copy={"kicker": "林芝", "body": "湖像刚醒。"})
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        copy_display_override=COPY_DISPLAY_PHOTOS,
        reading_profile_override="legacy",
    )
    assert 'data-pattern="screen-editorial-4mix"' in html
    assert 'data-copy-display="photos"' in html
    assert "layout-copy--kicker" in html
    assert 'data-editable="screen-copy-kicker"' not in html


@pytest.mark.e2e
def test_ac_4m_10_photos_draft_hides_copy() -> None:
    """AC-4M-10 · photos 模式 copy 不可见（CSS collapse，非透明占位）。"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    copy_css = (TEMPLATE_VISUAL_JOURNAL / "copy-display.css").read_text(encoding="utf-8")
    screens_css = JOURNAL_SCREENS_CSS.read_text(encoding="utf-8")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-layout="web" data-layout-engine="screens" data-copy-display="photos">
<head><meta charset="utf-8" />
<style>{screens_css}</style>
<style>{copy_css}</style>
</head>
<body>
<div class="layout-screen" data-pattern="{PATTERN_EDITORIAL_4MIX}">
  <p class="layout-copy layout-copy--kicker" data-block="screen-copy">林芝</p>
  <div class="layout-screen__grid layout-screen__grid--editorial-4mix"></div>
  <p class="layout-copy layout-copy--body" data-block="screen-copy">慢。</p>
</div>
</body>
</html>"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.set_content(html, wait_until="load")
        visible = page.evaluate(
            """() => {
              const nodes = document.querySelectorAll('.layout-copy');
              return {
                count: nodes.length,
                anyVisible: Array.from(nodes).some(el => {
                  const s = getComputedStyle(el);
                  return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
                }),
              };
            }"""
        )
        browser.close()
    assert visible["count"] == 2
    assert visible["anyVisible"] is False


def _4mix_mobile_screen() -> dict:
    return {
        "screenId": "ch01-s4mix",
        "patternId": PATTERN_EDITORIAL_4MIX,
        "layoutHint": LAYOUT_HINT_EDITORIAL_4MIX,
        "layoutGeometry": {"gridClass": "layout-screen__grid--editorial-4mix"},
        "copy": {"kicker": "林芝", "body": "慢。"},
        "slots": [
            {"assetId": "l1", "slot": 0, "fit": "cover", "role": "landscape"},
            {"assetId": "p1", "slot": 1, "fit": "contain", "role": "portrait"},
            {"assetId": "p2", "slot": 2, "fit": "contain", "role": "portrait"},
            {"assetId": "l2", "slot": 3, "fit": "cover", "role": "landscape"},
        ],
    }


@pytest.mark.unit
def test_mobile_4mix_expands_to_four_singles_in_order() -> None:
    from travelogue.render.mobile_screens import expand_editorial_4mix_screen

    expanded = expand_editorial_4mix_screen(_4mix_mobile_screen())
    assert len(expanded) == 4
    assert [sc["patternId"] for sc in expanded] == [
        "screen-landscape-1",
        "screen-portrait-1",
        "screen-portrait-1",
        "screen-landscape-1",
    ]
    assert [sc["slots"][0]["assetId"] for sc in expanded] == ["l1", "p1", "p2", "l2"]
    assert all(len(sc["slots"]) == 1 for sc in expanded)
    assert all("layoutHint" not in sc for sc in expanded)
    assert all("copy" not in sc for sc in expanded)


@pytest.mark.unit
def test_mobile_4mix_plate_on_first_slot_only() -> None:
    from travelogue.render.mobile_screens import expand_screens_for_mobile

    plate_flags: list[bool] = []
    chapter_screen_seq = 0
    for sc in expand_screens_for_mobile([_4mix_mobile_screen()]):
        chapter_screen_seq += 1
        plate_flags.append(chapter_screen_seq == 1)
    assert plate_flags == [True, False, False, False]


@pytest.mark.unit
def test_mobile_longshot_skips_4mix_expand() -> None:
    from travelogue.render.mobile_screens import should_expand_screens_for_mobile

    assert not should_expand_screens_for_mobile("mobile", is_longshot=True)
    assert should_expand_screens_for_mobile("mobile", is_longshot=False)
    assert not should_expand_screens_for_mobile("web", is_longshot=False)


@pytest.mark.unit
def test_ac_4m_11_mobile_html_expands_4mix_without_grid() -> None:
    """AC-4M-11 · mobile 无 editorial-4mix grid；TL→TR→BL→BR 四单槽。"""
    from travelogue.render.engine import render_html

    trip = _4mix_render_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="mobile",
        reading_profile_override="legacy",
    )
    assert PATTERN_EDITORIAL_4MIX not in html
    assert "layout-screen__grid--editorial-4mix" not in html
    assert html.count('data-pattern="screen-portrait-1"') >= 2
    assert html.count('data-pattern="screen-landscape-1"') >= 2
    idx_l1 = html.find('data-asset-ids="l1"')
    idx_p1 = html.find('data-asset-ids="p1"')
    idx_p2 = html.find('data-asset-ids="p2"')
    idx_l2 = html.find('data-asset-ids="l2"')
    assert -1 not in (idx_l1, idx_p1, idx_p2, idx_l2)
    assert idx_l1 < idx_p1 < idx_p2 < idx_l2


@pytest.mark.unit
def test_ac_4m_12_longshot_html_skips_4mix_mobile_expand() -> None:
    """AC-4M-12 · longshot 面不出现 4mix mobile 四连展开。"""
    from travelogue.render.engine import render_html

    trip = _4mix_render_trip()
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="longshot",
        reading_profile_override="legacy",
    )
    assert "layout-screen__grid--editorial-4mix" not in html
    patterns = re.findall(r'data-pattern="([^"]+)"', html)
    assert patterns.count("screen-portrait-1") < 4
    assert patterns.count("screen-landscape-1") < 2


@pytest.mark.unit
def test_scenery_portrait_fit_mode_is_deterministic() -> None:
    from travelogue.layout_engine.editorial.four_mix import editorial_4mix_scenery_portrait_fit_mode

    args = dict(
        trip_id="trip-a",
        screen_id="ch-01-sc-01",
        asset_id="p1",
        slot_index=1,
    )
    first = editorial_4mix_scenery_portrait_fit_mode(**args)
    for _ in range(20):
        assert editorial_4mix_scenery_portrait_fit_mode(**args) == first
    assert first in ("cover", "contain")


@pytest.mark.unit
def test_apply_editorial_4mix_slot_fits_person_contain_scenery_may_cover() -> None:
    from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_slot_fits

    screen = {
        "screenId": "ch01-s4mix",
        "patternId": PATTERN_EDITORIAL_4MIX,
        "slots": [
            {"assetId": "l1", "slot": 0, "fit": "cover", "role": "landscape"},
            {"assetId": "p1", "slot": 1, "fit": "contain", "role": "portrait"},
            {"assetId": "p2", "slot": 2, "fit": "contain", "role": "portrait"},
            {"assetId": "l2", "slot": 3, "fit": "cover", "role": "landscape"},
        ],
    }
    assets_map = {
        "l1": {"id": "l1", "tags": ["scenery"]},
        "p1": {"id": "p1", "tags": ["person"]},
        "p2": {"id": "p2", "tags": ["scenery"]},
        "l2": {"id": "l2", "tags": ["scenery"]},
    }
    trip = {"tripId": "fit-trip"}
    out = apply_editorial_4mix_slot_fits(screen, assets_map, trip=trip, cfg=_cfg_with_4mix())
    fits = [s["fit"] for s in out["slots"]]
    assert fits[0] == "cover"
    assert fits[1] == "contain"
    assert fits[3] == "cover"
    assert fits[2] in ("cover", "contain")


@pytest.mark.unit
def test_scenery_portrait_cover_random_disabled_keeps_contain() -> None:
    from dataclasses import replace

    from travelogue.layout_engine.editorial.four_mix import apply_editorial_4mix_slot_fits

    cfg = _cfg_with_4mix()
    e4 = replace(cfg.layout.editorial_4mix, scenery_portrait_cover_random=False)
    cfg = replace(cfg, layout=replace(cfg.layout, editorial_4mix=e4))
    screen = {
        "screenId": "ch01-s4mix",
        "patternId": PATTERN_EDITORIAL_4MIX,
        "slots": [
            {"assetId": "l1", "slot": 0, "role": "landscape"},
            {"assetId": "p1", "slot": 1, "role": "portrait"},
            {"assetId": "p2", "slot": 2, "role": "portrait"},
            {"assetId": "l2", "slot": 3, "role": "landscape"},
        ],
    }
    assets_map = {
        "l1": {"id": "l1", "tags": ["scenery"]},
        "p1": {"id": "p1", "tags": ["scenery"]},
        "p2": {"id": "p2", "tags": ["scenery"]},
        "l2": {"id": "l2", "tags": ["scenery"]},
    }
    out = apply_editorial_4mix_slot_fits(
        screen,
        assets_map,
        trip={"tripId": "t"},
        cfg=cfg,
    )
    assert [s["fit"] for s in out["slots"]] == ["cover", "contain", "contain", "cover"]
