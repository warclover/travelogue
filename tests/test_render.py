"""Renderer integration tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.context import pick_image_sizes
from travelogue.render.engine import RenderError, render_html, render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    """trip.json + assets/demo copied for render."""
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    # voice / video placeholders (optional files)
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_render_screens_engine_outputs_layout_screen(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=trip_workspace,
        layout_engine_override="screens",
    )
    assert 'data-layout-engine="screens"' in html
    assert 'data-block="layout-screen"' in html
    assert "layout-screen--16x9" in html
    assert 'layout-slot__img--cover' in html


def test_render_screens_includes_screenplay_bundle(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (trip_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(
        trip_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        export_mode="share",
    )
    assert (trip_workspace / "screenplay-hash.js").is_file()
    assert (trip_workspace / "screenplay-bookmarks.js").is_file()
    assert (trip_workspace / "screenplay.js").is_file()
    assert (trip_workspace / "screenplay.css").is_file()
    assert (trip_workspace / "copy-toggle.js").is_file()
    assert (trip_workspace / "copy-display.css").is_file()
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-screenplay="on"' in html
    assert 'data-copy-toggle="on"' in html
    assert "copy-display-toggle" in html
    assert "screenplay-start" in html
    assert "screenplay-hash.js" in html
    assert "screenplay-bookmarks.js" in html
    assert "screenplay.js" in html
    assert "longshot.js" not in html


def test_render_hides_cover_title_in_frame_mode(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("curation", {})["narrativeScope"] = "frame"
    trip["meta"]["title"] = "京都"
    trip["meta"]["places"] = ["京都"]
    html = render_html(trip, export_mode="draft", trip_root=trip_workspace)
    assert "cover-hero--photo-only" in html
    assert 'class="cover-hero__text"' not in html
    assert "cover-opening__title" in html
    assert "京都" in html


def test_render_hides_cover_title_for_custom_title_in_frame_mode(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("curation", {})["narrativeScope"] = "frame"
    trip["meta"]["title"] = "雨后京都"
    trip["meta"]["places"] = ["京都"]
    html = render_html(trip, export_mode="draft", trip_root=trip_workspace)
    assert "cover-hero--photo-only" in html


def test_render_html_has_core_blocks(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    html = render_html(trip, export_mode="draft", trip_root=trip_workspace)
    assert 'data-block="cover-hero"' in html
    assert 'data-pattern="open"' in html
    assert 'data-pattern="moment"' in html
    assert 'data-pattern="gallery"' in html
    assert 'data-block="media-scroll"' in html
    assert 'data-block="voice-bar"' in html
    assert 'class="media-card__visual"' in html


def test_render_trip_writes_index(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False)
    index = trip_workspace / "index.html"
    css = trip_workspace / "journal.css"
    assert index.is_file()
    assert css.is_file()
    assert (trip_workspace / "journal-screens.css").is_file()
    text = index.read_text(encoding="utf-8")
    assert "雨后京都" in text
    assert "assets/demo/cover-w1600.webp" in text


def test_render_missing_asset_raises(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["assets"][0]["displayFile"] = "assets/missing.webp"
    bad = trip_workspace / "bad.json"
    bad.write_text(json.dumps(trip), encoding="utf-8")
    with pytest.raises(RenderError) as exc:
        render_trip(bad, validate=False)
    assert exc.value.code == "E_RENDER_ASSET_MISSING"


def test_render_share_mode_no_editable(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    html = render_html(trip, export_mode="share", trip_root=trip_workspace)
    assert 'data-export="share"' in html
    assert "data-editable" not in html


def test_render_draft_includes_longshot_bundle(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False, export_mode="draft")
    assert (trip_workspace / "longshot.js").is_file()
    assert (trip_workspace / "share.js").is_file()
    assert (trip_workspace / "longshot.css").is_file()
    assert (trip_workspace / "vendor" / "html2canvas.min.js").is_file()
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-longshot="on"' in html
    assert 'data-block="share-toolbar"' in html
    assert "share.js" in html


def test_render_share_includes_longshot_by_default(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False, export_mode="share")
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert "longshot.js" in html
    assert 'data-longshot="on"' in html


def test_render_web_export_includes_responsive_sizes(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["exportLayout"] = "web"
    html = render_html(trip, export_mode="draft", trip_root=trip_workspace)
    assert "2200px" in html
    assert pick_image_sizes("web", "cover") in html
    assert pick_image_sizes("mobile", "cover") == "100vw"
    assert 'sizes="100vw"' in html or "sizes=" in html


def test_render_longshot_opt_out(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["export"] = {"longShot": False}
    (trip_workspace / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    render_trip(trip_workspace / "trip.json", validate=False, export_mode="share")
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert "longshot.js" not in html


def test_render_media_row_uses_source_and_aspect_kind(trip_workspace: Path) -> None:
    from travelogue.render.context import build_media_row

    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in trip["assets"]}
    row = {
        "type": "media-row",
        "assetIds": [trip["assets"][0]["id"], trip["assets"][1]["id"]],
        "rowLayout": "landscape-pair",
    }
    ctx = build_media_row(
        row,
        assets,
        meta_title="测试",
        export_layout="mobile",
        is_draft=True,
        chapter_id="ch-01",
        item_index=0,
    )
    assert ctx["cells"][0]["src"].startswith("assets/")
    assert ctx["cells"][0]["aspectKind"] in ("portrait", "landscape", "square", "panorama", "tall")
