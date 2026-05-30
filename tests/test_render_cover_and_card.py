"""Render resilience: missing media-card asset and invalid cover."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.assemble import build_render_context
from travelogue.render.chapters import build_chapters_render_context
from travelogue.render.engine import RenderError, render_html
from travelogue.render.surface import resolve_surface_context

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_build_chapters_skips_missing_media_card_asset(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    ch = trip["chapters"][0]
    ch["items"] = [
        {"type": "media-card", "assetId": "missing-asset-id"},
        {
            "type": "media-card",
            "assetId": trip["assets"][0]["id"],
        },
    ]
    surface = resolve_surface_context(trip, export_mode="draft")
    bundle = build_chapters_render_context(
        trip,
        surface,
        trip_root=trip_workspace,
        meta_title="测试",
        hook="",
    )
    items = bundle.chapters_out[0]["items"]
    media_cards = [it for it in items if it.get("isMediaCard")]
    assert len(media_cards) == 1


def test_build_render_context_invalid_cover_raises(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["assets"] = []
    trip["coverAssetId"] = "orphan-cover"
    with pytest.raises(RenderError) as exc:
        build_render_context(trip, export_mode="draft", trip_root=trip_workspace)
    assert exc.value.code == "E_RENDER_COVER_MISSING"


def test_render_html_with_orphan_media_card_does_not_crash(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    ch = trip["chapters"][0]
    items = copy.deepcopy(ch.get("items") or [])
    items.insert(0, {"type": "media-card", "assetId": "ghost"})
    ch["items"] = items
    html = render_html(trip, export_mode="draft", trip_root=trip_workspace)
    assert "<html" in html.lower()
