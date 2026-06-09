"""Folio full · trip-index · featured-grid dedupe (PRD-EXPERIENCE E7)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from travelogue.curation.curate import run_curate
from travelogue.curation.folio_plan import (
    build_folio_plan,
    collect_screen_asset_ids,
    pick_featured_grid_asset_ids,
    strip_assets_from_screens,
)
from travelogue.media.ingest import ingest_into_trip
from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html, render_trip
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
SCREENS_CSS = TEMPLATE_VISUAL_JOURNAL / "journal-screens.css"
TRIP_INDEX = TEMPLATE_VISUAL_JOURNAL / "partials" / "trip-index.hbs"
FEATURED_GRID = TEMPLATE_VISUAL_JOURNAL / "partials" / "featured-grid.hbs"
FOREWORD_SPREAD = TEMPLATE_VISUAL_JOURNAL / "partials" / "foreword-spread.hbs"
SCREEN_SPREAD = TEMPLATE_VISUAL_JOURNAL / "partials" / "screen-spread.hbs"
EPILOGUE_SCREEN = TEMPLATE_VISUAL_JOURNAL / "partials" / "epilogue-screen.hbs"
MANIFEST = TEMPLATE_VISUAL_JOURNAL / "manifest.json"


def _write_photo(path: Path, size: tuple[int, int] = (1200, 1600), color=(100, 80, 120)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG")


def _dual_album(tmp_path: Path, featured_n: int = 5, material_n: int = 8) -> Path:
    root = tmp_path / "album"
    feat = root / "精选"
    mat = root / "素材"
    for i in range(featured_n):
        _write_photo(feat / f"feat-{i:02d}.jpg", color=(180 + i * 5, 90, 60))
    for i in range(material_n):
        _write_photo(mat / f"mat-{i:02d}.jpg", size=(1600, 900), color=(60, 100 + i, 140))
    return root


@pytest.fixture
def screens_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "folio-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_folio_partials_exist() -> None:
    assert TRIP_INDEX.is_file()
    assert FEATURED_GRID.is_file()
    assert FOREWORD_SPREAD.is_file()
    assert SCREEN_SPREAD.is_file()
    assert EPILOGUE_SCREEN.is_file()
    assert 'data-block="trip-index"' in TRIP_INDEX.read_text(encoding="utf-8")
    assert 'data-block="featured-grid"' in FEATURED_GRID.read_text(encoding="utf-8")
    assert 'data-block="foreword-spread"' in FOREWORD_SPREAD.read_text(encoding="utf-8")
    assert 'data-block="screen-spread"' in SCREEN_SPREAD.read_text(encoding="utf-8")
    assert 'data-block="epilogue-screen"' in EPILOGUE_SCREEN.read_text(encoding="utf-8")


def test_manifest_folio_screen_patterns_whitelist() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    patterns = manifest.get("layoutEngine", {}).get("screenPatterns") or []
    blocks = manifest.get("blocks") or []
    assert "screen-plate" in patterns
    assert "screen-spread" in patterns
    for block in ("foreword-spread", "trip-index", "featured-grid", "screen-spread", "epilogue-screen"):
        assert block in blocks


def test_folio_full_css_rules() -> None:
    css = SCREENS_CSS.read_text(encoding="utf-8")
    assert ".trip-index" in css
    assert ".featured-grid__cards" in css
    assert ".foreword-spread" in css
    assert ".screen-spread" in css
    assert ".plate-caption" in css
    assert ".epilogue-screen" in css


def test_pick_featured_grid_requires_min_four() -> None:
    assets = [
        {"id": f"a{i}", "userTier": "featured", "layoutEligible": True, "width": 900, "height": 1200}
        for i in range(3)
    ]
    assert pick_featured_grid_asset_ids(assets) == []
    assets.append(
        {"id": "a4", "userTier": "featured", "layoutEligible": True, "width": 900, "height": 1200}
    )
    ids = pick_featured_grid_asset_ids(assets)
    assert len(ids) == 4


def test_strip_assets_from_screens_dedupes_grid() -> None:
    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {
                    "screenId": "ch-01-sc-01",
                    "patternId": "screen-portrait-2",
                    "slots": [{"assetId": "g1"}, {"assetId": "g2"}],
                },
                {
                    "screenId": "ch-01-sc-02",
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": "keep"}],
                },
            ],
        }
    ]
    removed = strip_assets_from_screens(chapters, {"g1", "g2"})
    assert removed == 2
    assert len(chapters[0]["screens"]) == 1
    assert chapters[0]["screens"][0]["slots"][0]["assetId"] == "keep"


def test_build_folio_plan_default_does_not_mutate_screens() -> None:
    chapters = [
        {
            "id": "ch-01",
            "screens": [{"slots": [{"assetId": "g1"}, {"assetId": "x1"}]}],
        }
    ]
    assets = [
        {"id": f"g{i}", "userTier": "featured", "layoutEligible": True, "width": 900, "height": 1200}
        for i in range(1, 6)
    ]
    trip = {"chapters": chapters, "assets": assets}
    before = json.dumps(chapters)
    plan = build_folio_plan(trip, chapters, assets)
    assert plan["featuredGrid"] is True
    assert before == json.dumps(chapters)


def test_build_folio_plan_mutates_screens() -> None:
    chapters = [
        {
            "id": "ch-01",
            "lead": "导语",
            "screens": [
                {"slots": [{"assetId": "g1"}, {"assetId": "x1"}]},
                {"slots": [{"assetId": "x2"}]},
            ],
        }
    ]
    assets = [
        {"id": f"g{i}", "userTier": "featured", "layoutEligible": True, "width": 900, "height": 1200}
        for i in range(1, 6)
    ] + [{"id": "x1", "layoutEligible": True, "width": 1600, "height": 900}]
    trip = {"chapters": chapters, "assets": assets}
    plan = build_folio_plan(trip, chapters, assets, mutate_screens=True)
    assert plan["featuredGrid"] is True
    assert len(plan["featuredGridAssetIds"]) >= 4
    screen_ids = collect_screen_asset_ids(chapters)
    overlap = screen_ids.intersection(plan["featuredGridAssetIds"])
    assert not overlap


def test_curate_writes_folio_plan(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("folio-curate", trips, title="folio")
    trip_dir = trips / "folio-curate"
    trip = TripService().load(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_dual_album(tmp_path, 5, 10),
        dedupe=False,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    run_curate(trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    plan = (trip.get("curation") or {}).get("folioPlan") or {}
    if plan.get("featuredGrid"):
        grid_ids = set(plan.get("featuredGridAssetIds") or [])
        screen_ids = collect_screen_asset_ids(trip.get("chapters") or [])
        assert not grid_ids.intersection(screen_ids)


def test_magazine_profile_renders_folio_full_blocks(screens_workspace: Path) -> None:
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    for i, asset in enumerate(trip.get("assets", [])[:5]):
        asset["userTier"] = "featured"
        asset["id"] = asset.get("id") or f"asset-{i}"
    trip.setdefault("curation", {})["folioPlan"] = {
        "index": True,
        "foreword": False,
        "featuredGrid": True,
        "featuredGridAssetIds": [a["id"] for a in trip["assets"][:5]],
        "plateAssetIds": [],
    }
    (screens_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="magazine",
    )
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-folio="full"' in html
    assert 'data-block="trip-index"' in html
    assert 'data-block="featured-grid"' in html


def test_legacy_profile_no_folio_full_blocks(screens_workspace: Path) -> None:
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
    )
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert "trip-index" not in html
    assert "featured-grid" not in html
    assert "foreword-spread" not in html
    assert "screen-spread" not in html
    assert 'data-block="epilogue-screen"' not in html


def _magazine_trip(*, foreword: bool = True) -> dict:
    trip = prepare_trip_web_screens(json.loads(FIXTURE.read_text(encoding="utf-8")))
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    chapters = trip.get("chapters") or []
    if foreword and chapters:
        chapters[0]["lead"] = "抵达京都的第一阵雨，把霓虹拉得很长。"
    for i, asset in enumerate(trip.get("assets", [])[:5]):
        asset["userTier"] = "featured"
        asset["id"] = asset.get("id") or f"asset-{i}"
    if len(chapters) >= 3:
        chapters[2]["lead"] = "人太多，高光在站台边。"
    trip.setdefault("curation", {})["folioPlan"] = {
        "index": True,
        "foreword": foreword and bool((chapters[0].get("lead") or "").strip()) if chapters else False,
        "featuredGrid": True,
        "featuredGridAssetIds": [a["id"] for a in trip["assets"][:5]],
        "plateAssetIds": [],
    }
    return trip


def test_magazine_renders_folio_full_blocks() -> None:
    trip = _magazine_trip(foreword=True)
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="magazine",
    )
    assert 'data-folio="full"' in html
    assert 'data-block="trip-index"' in html
    assert 'data-block="featured-grid"' in html
    assert 'data-block="foreword-spread"' in html
    assert 'data-block="screen-spread"' in html
    assert 'data-block="cover-closing"' in html
    assert 'data-block="epilogue-screen"' not in html
    assert 'data-pattern="screen-plate"' in html
    foreword_idx = html.index('data-block="foreword-spread"')
    ch03_idx = html.index('id="ch-03"')
    assert foreword_idx < ch03_idx
    ch01 = html[html.index('id="ch-01"'): html.index('id="ch-02"')]
    assert 'data-block="chapter-lead"' not in ch01
    assert html.count('data-block="screen-spread"') >= 1
    assert "人太多" in html


def test_folio_lite_renders_screen_plate_and_epilogue_screen() -> None:
    trip = prepare_trip_web_screens(json.loads(FIXTURE.read_text(encoding="utf-8")))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-folio="lite"' in html
    assert 'data-pattern="screen-plate"' in html
    assert 'data-block="cover-closing"' in html
    assert 'data-block="closing-hero"' in html
    assert 'data-block="epilogue-screen"' not in html
    assert 'data-block="foreword-spread"' not in html


def test_build_foreword_spread_context() -> None:
    from travelogue.render.context import build_foreword_spread

    out = build_foreword_spread({"title": "抵达", "lead": "第一句。第二句。"}, trip_hook="hook")
    assert out is not None
    assert out["lead"] == "第一句。第二句。"
    assert out["hasPullQuote"] is True
    assert out["pullQuote"] == "第一句"


def test_build_screen_spread_uses_chapter_lead() -> None:
    from travelogue.render.context import build_screen_spread

    assets = {
        "a1": {
            "id": "a1",
            "displayFile": "assets/demo/cover-w1600.webp",
            "width": 1600,
            "height": 900,
        }
    }
    spread = build_screen_spread(
        {"lead": "站台边的光。", "curation": {}},
        {"slots": [{"assetId": "a1"}]},
        assets,
        meta_title="test",
        export_layout="web",
        trip_hook="",
    )
    assert spread is not None
    assert spread["body"] == "站台边的光。"
    assert spread["hasPullQuote"] is True
