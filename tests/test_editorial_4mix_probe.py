"""PR-6 · editorial-4mix probe baselines + dogfood compare."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.curation.editorial_4mix import PATTERN_EDITORIAL_4MIX
from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2
from travelogue.layout_templates.probe_editorial_4mix import (
    EDITORIAL_4MIX_PROBE_IDS,
    build_editorial_4mix_probe_html,
    editorial_4mix_baseline_path,
    editorial_4mix_probe_id,
    run_editorial_4mix_screenshot_probe,
)
from travelogue.render.compare_editorial_4mix import (
    transform_trip_for_4mix_compare,
)


def test_editorial_4mix_probe_ids() -> None:
    assert editorial_4mix_probe_id("person") in EDITORIAL_4MIX_PROBE_IDS
    assert editorial_4mix_probe_id("scenery") in EDITORIAL_4MIX_PROBE_IDS


def test_build_editorial_4mix_probe_html_variants() -> None:
    person = build_editorial_4mix_probe_html(variant="person")
    scenery = build_editorial_4mix_probe_html(variant="scenery")
    assert f'data-pattern="{PATTERN_EDITORIAL_4MIX}"' in person
    assert "layout-copy--kicker" in person
    assert "layout-copy--kicker" not in scenery
    assert "layout-screen__grid--editorial-4mix" in scenery


def test_transform_trip_for_4mix_compare() -> None:
    trip = {
        "tripId": "compare-trip",
        "layoutEngine": "screens",
        "assets": [
            {"id": "l1", "nativeWidth": 1600, "nativeHeight": 900, "layoutEligible": True},
            {"id": "p1", "nativeWidth": 900, "nativeHeight": 1600, "layoutEligible": True},
            {"id": "p2", "nativeWidth": 800, "nativeHeight": 1400, "layoutEligible": True},
            {"id": "l2", "nativeWidth": 1400, "nativeHeight": 800, "layoutEligible": True},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    {
                        "screenId": "ch-01-sc-01",
                        "patternId": PATTERN_EDITORIAL_4MIX,
                        "slots": [
                            {"assetId": "l1", "slot": 0, "role": "landscape"},
                            {"assetId": "p1", "slot": 1, "role": "portrait"},
                            {"assetId": "p2", "slot": 2, "role": "portrait"},
                            {"assetId": "l2", "slot": 3, "role": "landscape"},
                        ],
                        "copy": {"kicker": "地点", "body": "一句旁白"},
                    }
                ],
            }
        ],
    }
    legacy = transform_trip_for_4mix_compare(trip, mode="legacy")
    editorial = transform_trip_for_4mix_compare(trip, mode="editorial")
    sc_l = legacy["chapters"][0]["screens"][0]
    sc_e = editorial["chapters"][0]["screens"][0]
    assert sc_l["patternId"] == PATTERN_PORTRAIT_2_LANDSCAPE_2
    assert sc_e["patternId"] == PATTERN_EDITORIAL_4MIX
    assert editorial["export"]["editorial4Mix"] is True
    assert sc_e.get("copy") == {"kicker": "地点", "body": "一句旁白"}


@pytest.mark.unit
def test_run_editorial_4mix_screenshot_probe_missing_baseline() -> None:
    pytest.importorskip("playwright")
    for probe_id in EDITORIAL_4MIX_PROBE_IDS:
        path = editorial_4mix_baseline_path(probe_id)
        backup = path.read_bytes() if path.is_file() else None
        if path.is_file():
            path.unlink()
        try:
            out = run_editorial_4mix_screenshot_probe(update_baselines=False)
            if out.get("skipped"):
                pytest.skip(out.get("reason", "playwright unavailable"))
            assert out["ok"] is False
            assert any(probe_id in w for w in out.get("warnings") or [])
            break
        finally:
            if backup is not None:
                path.write_bytes(backup)


@pytest.mark.unit
def test_run_editorial_4mix_screenshot_probe_matches_baselines() -> None:
    pytest.importorskip("playwright")
    missing = [
        pid for pid in EDITORIAL_4MIX_PROBE_IDS if not editorial_4mix_baseline_path(pid).is_file()
    ]
    if missing:
        pytest.skip(
            f"missing baselines: {', '.join(missing)} (run lte_probe_regress --update-baselines)"
        )
    out = run_editorial_4mix_screenshot_probe(update_baselines=False)
    if out.get("skipped"):
        pytest.skip(out.get("reason", "playwright unavailable"))
    assert out["ok"] is True
    assert out["compared"] == len(EDITORIAL_4MIX_PROBE_IDS)


def test_compare_editorial_4mix_renders_panels(tmp_path: Path) -> None:
    """PR-6 · dogfood 并排对比页可渲染 legacy / 4mix 面板。"""
    from travelogue.render.compare_editorial_4mix import compare_editorial_4mix

    trip = {
        "tripId": "4mix-compare",
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "meta": {"title": "4mix 对比", "hook": ""},
        "coverAssetId": "l1",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "l1",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "nativeWidth": 1600,
                "nativeHeight": 900,
                "paths": {"w800": "assets/l1-w800.webp"},
            },
            {
                "id": "p1",
                "type": "image",
                "layoutEligible": True,
                "width": 900,
                "height": 1600,
                "nativeWidth": 900,
                "nativeHeight": 1600,
                "paths": {"w800": "assets/p1-w800.webp"},
            },
            {
                "id": "p2",
                "type": "image",
                "layoutEligible": True,
                "width": 800,
                "height": 1400,
                "nativeWidth": 800,
                "nativeHeight": 1400,
                "paths": {"w800": "assets/p2-w800.webp"},
            },
            {
                "id": "l2",
                "type": "image",
                "layoutEligible": True,
                "width": 1400,
                "height": 800,
                "nativeWidth": 1400,
                "nativeHeight": 800,
                "paths": {"w800": "assets/l2-w800.webp"},
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "章",
                "screens": [
                    {
                        "screenId": "ch01-s4mix",
                        "patternId": PATTERN_EDITORIAL_4MIX,
                        "slots": [
                            {"assetId": "l1", "slot": 0, "role": "landscape"},
                            {"assetId": "p1", "slot": 1, "role": "portrait"},
                            {"assetId": "p2", "slot": 2, "role": "portrait"},
                            {"assetId": "l2", "slot": 3, "role": "landscape"},
                        ],
                    }
                ],
            }
        ],
    }
    trip_file = tmp_path / "trip.json"
    trip_file.write_text(__import__("json").dumps(trip), encoding="utf-8")
    from PIL import Image

    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    for name in ("l1-w800.webp", "p1-w800.webp", "p2-w800.webp", "l2-w800.webp"):
        Image.new("RGB", (800, 533), (196, 214, 232)).save(assets_dir / name, "WEBP")
    result = compare_editorial_4mix(trip_file, out_dir=tmp_path / "compare")
    assert result.wrapper_html.is_file()
    assert result.legacy_panel.is_file()
    assert result.editorial_panel.is_file()
    assert (tmp_path / "compare" / "assets").is_dir()
    legacy_html = result.legacy_panel.read_text(encoding="utf-8")
    editorial_html = result.editorial_panel.read_text(encoding="utf-8")
    assert f'data-pattern="{PATTERN_PORTRAIT_2_LANDSCAPE_2}"' in legacy_html
    assert f'data-pattern="{PATTERN_EDITORIAL_4MIX}"' in editorial_html
    wrapper = result.wrapper_html.read_text(encoding="utf-8")
    assert "panel-legacy.html" in wrapper
    assert "panel-editorial.html" in wrapper
