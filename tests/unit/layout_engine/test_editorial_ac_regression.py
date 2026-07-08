"""PRD portrait-row-editorial · AC / G-ED integration regression (v0.3)."""



from __future__ import annotations
from tests._repo_root import repo_root

import copy
import json
import re
import shutil
from pathlib import Path

import pytest

from tests._golden.helpers import (
    build_portrait_heavy_trip,
    layout_snapshot,
    load_golden,
    plan_legacy_screens,
)
from .test_editorial_portrait_row import _cfg_with_editorial
from travelogue.curation.breath_pauses import BREATH_PATTERN, insert_breath_screens_in_chapters
from travelogue.curation.editorial_portrait_row import (
    LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
    PATTERN_PORTRAIT_3_EDITORIAL,
)
from travelogue.paths import FIXTURES_DIR
from travelogue.render.compare_editorial_portrait_row import compare_editorial_portrait_row
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html
from travelogue.render.golden_regression import load_golden_trip
from travelogue.render.mobile_screens import expand_portrait_triples_for_mobile

_GOLDEN_FIXTURE = FIXTURES_DIR / "trip.render_golden.json"
_DEMO_ASSETS = repo_root(__file__) / "templates" / "visual-journal" / "assets"


def _copy_demo_assets(ws: Path) -> None:
    if not _DEMO_ASSETS.is_dir():
        pytest.skip("demo assets not present")
    shutil.copytree(_DEMO_ASSETS, ws / "assets", dirs_exist_ok=True)
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")


def _inject_editorial_triple(trip: dict) -> dict:
    """Insert editorial triple after the first screen (avoid folio plate → screen-plate)."""
    out = copy.deepcopy(trip)
    editorial_screen = {
        "screenId": "ch-ed-sc-01",
        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
        "layoutHint": LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
        "slots": [
            {"assetId": "asset-001", "slot": 0, "fit": "contain"},
            {"assetId": "asset-002", "slot": 1, "fit": "contain"},
            {"assetId": "scroll-1", "slot": 2, "fit": "contain"},
        ],
    }
    for ch in out.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        screens = list(ch.get("screens") or [])
        if not screens:
            continue
        ch["screens"] = [screens[0], editorial_screen, *screens[1:]]
        break
    else:
        out.setdefault("chapters", []).append(
            {"id": "ch-ed", "patternId": "open", "title": "Ed", "items": [], "screens": [editorial_screen]}
        )
    export = out.setdefault("export", {})
    export["editorialPortraitRow"] = True
    return out


def _editorial_render_workspace(tmp_path: Path) -> Path:
    if not _GOLDEN_FIXTURE.is_file():
        pytest.skip("trip.render_golden.json missing")
    ws = tmp_path / "editorial-ac"
    ws.mkdir()
    trip = _inject_editorial_triple(prepare_trip_web_screens(load_golden_trip()))
    trip["layoutEngine"] = "screens"
    trip["exportLayout"] = "auto"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    _copy_demo_assets(ws)
    return ws


def _screen_pattern_blocks(html: str) -> list[tuple[str, str]]:
    """(patternId, data-asset-ids) for each layout-screen block."""
    blocks = re.findall(
        r'<(?:article|div)[^>]*class="[^"]*layout-screen[^"]*"[^>]*data-pattern="([^"]+)"[^>]*data-asset-ids="([^"]*)"',
        html,
    )
    if blocks:
        return blocks
    return [
        (pat, aids)
        for pat, aids in re.findall(
            r'data-pattern="(screen-[^"]+)"[^>]*data-asset-ids="([^"]*)"',
            html,
        )
    ]


def test_ac_ed_08a_mobile_html_has_no_editorial_3col_block(tmp_path: Path) -> None:
    """AC-ED-08a · mobile 面不出现 editorial 三列 layout-screen。"""
    ws = _editorial_render_workspace(tmp_path)
    trip = json.loads((ws / "trip.json").read_text(encoding="utf-8"))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="mobile",
    )
    assert PATTERN_PORTRAIT_3_EDITORIAL not in html
    assert "layout-screen__grid--3col" not in html or PATTERN_PORTRAIT_3_EDITORIAL not in html


def test_ac_ed_08b_mobile_html_expands_triple_to_three_portrait_1(tmp_path: Path) -> None:
    """AC-ED-08b · 原三竖 assets 以 3 个连续 screen-portrait-1 出现。"""
    ws = _editorial_render_workspace(tmp_path)
    trip = json.loads((ws / "trip.json").read_text(encoding="utf-8"))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="mobile",
    )
    blocks = _screen_pattern_blocks(html)
    patterns = [b[0] for b in blocks]
    asset_rows = [b[1] for b in blocks]
    expected_assets = ["asset-001", "asset-002", "scroll-1"]
    found = False
    for i in range(len(patterns) - 2):
        if (
            patterns[i : i + 3] == ["screen-portrait-1"] * 3
            and asset_rows[i : i + 3] == expected_assets
        ):
            found = True
            break
    assert found, f"expected 3 consecutive portrait-1 with {expected_assets}, got {list(zip(patterns, asset_rows, strict=False))[:12]}"


def test_breath_anchor_unchanged_after_mobile_expand() -> None:
    """§12.4 · breath 在 raw screens[] 序中的锚点；mobile 拆屏仅扩展 render 序列。"""
    triple = {
        "screenId": "ch-sc-01",
        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
        "slots": [{"assetId": f"p{i}", "slot": i} for i in range(3)],
    }
    single = {
        "screenId": "ch-sc-02",
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": "p9", "slot": 0}],
    }
    chapters = [{"id": "ch-01", "screens": [triple, single]}]
    raw_before = copy.deepcopy(chapters[0]["screens"])
    insert_breath_screens_in_chapters(chapters, interval=2)
    raw_screens = chapters[0]["screens"]
    breath_raw_idx = next(
        i for i, sc in enumerate(raw_screens) if sc.get("patternId") == BREATH_PATTERN
    )
    assert raw_screens[:breath_raw_idx] == raw_before[:breath_raw_idx]

    render_screens = expand_portrait_triples_for_mobile(raw_screens)
    expected_breath_idx = sum(
        len(expand_portrait_triples_for_mobile([sc]))
        for sc in raw_screens[:breath_raw_idx]
    )
    assert render_screens[expected_breath_idx]["patternId"] == BREATH_PATTERN


def test_ac_ed_02_web_html_includes_editorial_pattern(tmp_path: Path) -> None:
    """AC-ED-02 · 开启 editorial 时 web HTML 含 screen-portrait-3-editorial。"""
    ws = _editorial_render_workspace(tmp_path)
    trip = json.loads((ws / "trip.json").read_text(encoding="utf-8"))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert f'data-pattern="{PATTERN_PORTRAIT_3_EDITORIAL}"' in html


def test_compare_editorial_portrait_row_renders_panels(tmp_path: Path) -> None:
    """PR-5 · dogfood 并排对比页可渲染 legacy / editorial 面板。"""
    ws = _editorial_render_workspace(tmp_path)
    result = compare_editorial_portrait_row(ws / "trip.json", out_dir=ws / "editorial-compare")
    assert result.wrapper_html.is_file()
    assert result.legacy_panel.is_file()
    assert result.editorial_panel.is_file()
    legacy_html = result.legacy_panel.read_text(encoding="utf-8")
    editorial_html = result.editorial_panel.read_text(encoding="utf-8")
    assert 'data-pattern="screen-portrait-3"' in legacy_html
    assert f'data-pattern="{PATTERN_PORTRAIT_3_EDITORIAL}"' in editorial_html
    wrapper = result.wrapper_html.read_text(encoding="utf-8")
    assert "panel-legacy.html" in wrapper
    assert "panel-editorial.html" in wrapper


def test_g_ed_03_portrait_heavy_proxy_deep_equal_with_editorial_disabled() -> None:
    """G-ED-03 · demo-2025-2 代理样本 · enabled:false 时 layout golden deep equal。"""
    buckets, aspects, assets = build_portrait_heavy_trip()
    cfg = _cfg_with_editorial(enabled=False)
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        chapters = plan_legacy_screens(buckets, aspects, assets, layout_density="balanced")
    finally:
        config_mod.get_config = orig
    assert layout_snapshot(chapters) == load_golden("portrait-heavy")
