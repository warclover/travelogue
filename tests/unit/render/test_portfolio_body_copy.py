"""AC-PFM-32 · 作品集正文页无图注 / 章导语节点；封面封底书名地点仍在。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_html

pytestmark = pytest.mark.unit

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def screens_trip(tmp_path: Path) -> tuple[Path, dict]:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "portfolio-body-copy"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.layout_engine.planner.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    for ch in trip.get("chapters") or []:
        ch["lead"] = "这是章导语，作品集正文不应出现"
        for item in ch.get("items") or []:
            if isinstance(item, dict):
                item["caption"] = "这是图注，作品集正文不应出现"
    trip.setdefault("meta", {})
    trip["meta"]["title"] = "奈良"
    trip["meta"]["places"] = ["奈良公园"]
    trip["intent"] = {**(trip.get("intent") or {}), "placesUserSet": True}
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


def test_ac_pfm_32_portfolio_body_omits_caption_and_lead(
    screens_trip: tuple[Path, dict],
) -> None:
    ws, trip = screens_trip
    trip["studio"] = {"edition": "portfolio"}
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert "奈良" in html
    assert "奈良公园" in html
    assert 'data-block="trip-meta"' in html
    assert "cover-opening__title" in html
    assert "cover-closing__title" in html or "cover-opening__title" in html
    assert 'data-block="chapter-lead"' not in html
    assert 'data-block="chapter-header"' not in html
    assert 'data-block="chapter-separator"' not in html
    assert 'data-block="divider-place"' not in html
    assert "media-card__caption" not in html
    assert "media-row__caption" not in html
    assert "plate-caption" not in html
    assert "layout-copy--kicker" not in html
    assert "layout-copy--body" not in html
    assert "page-6-grid-land" not in html
    assert "page-1-hero" not in html
