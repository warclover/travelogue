"""Render must not crash when chapter items reference missing asset ids."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.context import build_media_row, build_media_scroll

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


def test_build_media_row_skips_missing_asset_ids(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in trip["assets"]}
    row = {
        "type": "media-row",
        "assetIds": [trip["assets"][0]["id"], "missing-asset-id", ""],
        "rowLayout": "landscape-pair",
    }
    ctx = build_media_row(
        row,
        assets,
        meta_title="测试",
        export_layout="mobile",
        is_draft=False,
        chapter_id="ch-01",
        item_index=0,
    )
    assert len(ctx["cells"]) == 1


def test_build_media_scroll_skips_missing_asset_ids(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in trip["assets"]}
    item = {
        "type": "media-scroll",
        "assetIds": ["orphan", trip["assets"][0]["id"]],
    }
    ctx = build_media_scroll(
        item,
        assets,
        meta_title="测试",
        export_layout="mobile",
        is_draft=False,
        chapter_id="ch-01",
        item_index=0,
    )
    assert len(ctx["slides"]) == 1
