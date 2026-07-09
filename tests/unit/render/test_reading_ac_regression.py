"""PRD-EXPERIENCE AC regression · Post-Epic follow-ups."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from travelogue.paths import FIXTURES_DIR, ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html, render_trip
from travelogue.render.reading_profile import resolve_reading_payload

FIXTURE = FIXTURES_DIR / "trip.render_golden.json"
LINZHI_CI = FIXTURES_DIR / "trip.linzhi_screens.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
LINZHI = ROOT / "trips" / "linzhi"
AUX_SELECTOR_FRAGMENTS = (
    'data-block="cover-hero"',
    'data-block="trip-index"',
    'data-block="featured-grid"',
    'data-block="epilogue-screen"',
)


def _extract_reading_json(html: str) -> dict:
    match = re.search(
        r"window\.__TRAVELOGUE_READING__\s*=\s*(\{.*?\});",
        html,
        re.DOTALL,
    )
    assert match, "missing __TRAVELOGUE_READING__ script"
    return json.loads(match.group(1))


@pytest.fixture
def screens_workspace(tmp_path: Path) -> Path:
    trip = prepare_trip_web_screens(json.loads(FIXTURE.read_text(encoding="utf-8")))
    ws = tmp_path / "trips" / "ac-regression"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_ac_exp_02_default_hybrid_bundle(screens_workspace: Path) -> None:
    """AC-EXP-02: default_hybrid enables snap + soft breath + folio lite."""
    html = render_html(
        json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8")),
        export_mode="draft",
        trip_root=screens_workspace,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-snap="proximity"' in html
    assert 'data-breath="soft"' in html
    assert 'data-folio="lite"' in html
    assert "breath.js" in html


def _ensure_single_slot_chapter_opener(trip: dict, *, asset_id: str | None = None) -> None:
    """Force chapter-1 opener to 1 slot so folio plate rewrite remains testable."""
    chapters = trip.get("chapters") or []
    if not chapters:
        return
    screens = list(chapters[0].get("screens") or [])
    if not screens:
        return
    sc = dict(screens[0])
    slots = [s for s in (sc.get("slots") or []) if s.get("assetId")]
    if len(slots) == 1 and not asset_id:
        return
    assets = trip.get("assets") or []
    aid = asset_id
    if not aid:
        featured = next((a for a in assets if a.get("userTier") == "featured"), None)
        aid = str((featured or (assets[0] if assets else {}) or {}).get("id") or slots[0]["assetId"])
    sc["patternId"] = "screen-portrait-1"
    sc["slots"] = [{"assetId": aid, "slot": 0, "fit": "contain"}]
    screens[0] = sc
    chapters[0] = dict(chapters[0])
    chapters[0]["screens"] = screens


def test_ac_exp_05_featured_plate_pattern(screens_workspace: Path) -> None:
    """AC-EXP-05 / AC-FO-02: featured asset on folio lite plate pattern."""
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["assets"][1]["userTier"] = "featured"
    _ensure_single_slot_chapter_opener(trip, asset_id=str(trip["assets"][1]["id"]))
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=screens_workspace,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-pattern="screen-plate"' in html
    assert 'data-featured="true"' in html


def test_skip_aux_blocks_in_reading_payload(screens_workspace: Path) -> None:
    """P0-4 render: skipAuxBlocks flows into __TRAVELOGUE_READING__."""
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {
        "profile": "performance",
        "present": {"skipAuxBlocks": True},
    }
    html = render_html(
        trip,
        export_mode="share",
        trip_root=screens_workspace,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    payload = _extract_reading_json(html)
    assert payload["present"]["skipAuxBlocks"] is True
    assert 'data-screenplay="on"' in html


def test_skip_aux_blocks_selector_contract() -> None:
    """P0-4: when skipAuxBlocks, present collects layout-screen only (JS contract)."""
    js = (TEMPLATE_VISUAL_JOURNAL / "screenplay.js").read_text(encoding="utf-8")
    assert 'if (skipAuxBlocksEnabled())' in js
    assert "return SELECTOR" in js
    assert "AUX_SELECTOR" in js


def test_present_bookmarks_render_asset_ids(screens_workspace: Path) -> None:
    """P3-2: layout-screen carries data-asset-ids for featured-grid bookmarks."""
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    featured_ids = [a["id"] for a in trip["assets"][:5]]
    for i, asset in enumerate(trip["assets"][:5]):
        asset["userTier"] = "featured"
        asset["id"] = asset.get("id") or f"asset-{i}"
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    trip.setdefault("curation", {})["folioPlan"] = {
        "index": True,
        "foreword": False,
        "featuredGrid": True,
        "featuredGridAssetIds": featured_ids,
        "plateAssetIds": [],
    }
    html = render_html(
        trip,
        export_mode="share",
        trip_root=screens_workspace,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-asset-ids="' in html
    assert 'data-asset-id="' in html
    assert "wire" in (TEMPLATE_VISUAL_JOURNAL / "screenplay-bookmarks.js").read_text(
        encoding="utf-8"
    )


def test_ac_fo_03_trip_index_chapter_anchors(screens_workspace: Path) -> None:
    """AC-FO-03: folio full trip-index links anchor to chapter ids."""
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    trip.setdefault("curation", {})["folioPlan"] = {
        "index": True,
        "foreword": False,
        "featuredGrid": False,
        "featuredGridAssetIds": [],
        "plateAssetIds": [],
    }
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=screens_workspace,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'href="#ch-01"' in html
    assert 'id="ch-01"' in html


def test_ac_fo_05_legacy_profile_no_folio_blocks(screens_workspace: Path) -> None:
    """AC-FO-05: legacy profile omits folio full blocks."""
    render_trip(
        screens_workspace / "trip.json",
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
    )
    html = (screens_workspace / "index.html").read_text(encoding="utf-8")
    assert "trip-index" not in html
    assert "folio-plate-meta" not in html


def test_ac_fo_04_featured_grid_not_on_mobile(screens_workspace: Path) -> None:
    """AC-FO-04: mobile surface forces folio off even with magazine trip."""
    trip = json.loads((screens_workspace / "trip.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    payload = resolve_reading_payload(
        trip,
        export_mode="draft",
        export_layout_override="mobile",
        index_name="index-mobile.html",
    )
    assert payload["scroll"]["folio"] == "off"


def test_linzhi_ci_fixture_validates() -> None:
    from travelogue.services.validate import validate_trip

    trip = json.loads(LINZHI_CI.read_text(encoding="utf-8"))
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert errs == []
    assert sum(len(ch.get("screens") or []) for ch in trip["chapters"]) >= 15


@pytest.mark.skipif(not (LINZHI / "trip.json").is_file(), reason="local trips/linzhi missing")
def test_linzhi_real_trip_optional() -> None:
    """Optional: full linzhi album when present locally."""
    trip = json.loads((LINZHI / "trip.json").read_text(encoding="utf-8"))
    assert trip.get("layoutEngine") == "screens"
