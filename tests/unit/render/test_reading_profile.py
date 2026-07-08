"""Reading profile resolution and HTML injection (PRD-EXPERIENCE E1)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import (
    LONGSHOT_INDEX_NAME,
    render_html,
    render_trip_surfaces,
    write_longshot_sidecar,
)
from travelogue.render.reading_profile import resolve_reading_payload

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def screens_trip(tmp_path: Path) -> tuple[Path, dict]:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "reading-profile-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip["exportLayout"] = "web"
    trip["layoutEngine"] = "screens"
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.screen_planner import attach_screens_to_chapters

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip.get("assets", [])}
    trip["chapters"] = attach_screens_to_chapters(trip.get("chapters", []), aspects)
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


def _extract_reading_json(html: str) -> dict:
    match = re.search(
        r"window\.__TRAVELOGUE_READING__\s*=\s*(\{.*?\});",
        html,
        re.DOTALL,
    )
    assert match, "missing __TRAVELOGUE_READING__ script"
    return json.loads(match.group(1))


def test_resolve_reading_payload_web_draft_default_hybrid(screens_trip: tuple[Path, dict]) -> None:
    _, trip = screens_trip
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["profile"] == "default_hybrid"
    assert payload["scroll"]["snap"] == "proximity"
    assert payload["scroll"]["breath"] == "soft"
    assert payload["scroll"]["folio"] == "lite"
    assert payload["present"]["dwellMs"] == 2000


def test_resolve_reading_payload_share_performance(screens_trip: tuple[Path, dict]) -> None:
    _, trip = screens_trip
    payload = resolve_reading_payload(trip, export_mode="share", export_layout_override="web")
    assert payload["profile"] == "performance"
    assert payload["scroll"]["breath"] == "off"


def test_resolve_reading_payload_mobile_legacy(screens_trip: tuple[Path, dict]) -> None:
    _, trip = screens_trip
    payload = resolve_reading_payload(
        trip,
        export_mode="draft",
        export_layout_override="mobile",
        index_name="index-mobile.html",
    )
    assert payload["profile"] == "legacy"
    assert payload["scroll"]["folio"] == "off"


def test_resolve_reading_payload_longshot_surface(screens_trip: tuple[Path, dict]) -> None:
    _, trip = screens_trip
    payload = resolve_reading_payload(
        trip,
        export_mode="draft",
        export_layout_override="longshot",
        index_name=LONGSHOT_INDEX_NAME,
    )
    assert payload["profile"] == "performance"
    assert payload["scroll"]["snap"] == "off"
    assert payload["longshot"]["breath"] == "off"


def test_render_html_injects_reading_script(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-reading-profile="default_hybrid"' in html
    assert 'data-snap="proximity"' in html
    assert 'data-breath="soft"' in html
    assert 'data-folio="lite"' in html
    payload = _extract_reading_json(html)
    assert payload["profile"] == "default_hybrid"


def test_render_html_reading_profile_override_legacy(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
    )
    assert 'data-reading-profile="legacy"' in html
    assert "data-snap=" not in html
    payload = _extract_reading_json(html)
    assert payload["scroll"]["breath"] == "off"


def test_render_trip_surfaces_mobile_legacy_profile(screens_trip: tuple[Path, dict]) -> None:
    ws, _ = screens_trip
    web_path, mobile_path, _present = render_trip_surfaces(ws / "trip.json", validate=False)
    web_html = web_path.read_text(encoding="utf-8")
    mobile_html = mobile_path.read_text(encoding="utf-8")
    assert _extract_reading_json(web_html)["profile"] == "default_hybrid"
    assert _extract_reading_json(mobile_html)["profile"] == "legacy"
    assert 'data-reading-profile="legacy"' in mobile_html


def test_longshot_sidecar_performance_profile(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    write_longshot_sidecar(trip, ws, trip_root=ws)
    html = (ws / LONGSHOT_INDEX_NAME).read_text(encoding="utf-8")
    payload = _extract_reading_json(html)
    assert payload["profile"] == "performance"
    assert payload["scroll"]["breath"] == "off"


def test_trip_export_reading_profile_in_schema(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    trip.setdefault("export", {})["reading"] = {"profile": "magazine"}
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    payload = _extract_reading_json(html)
    assert payload["profile"] == "magazine"
    assert payload["scroll"]["breath"] == "flow"


def test_featured_asset_ids_in_payload(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    trip["assets"][0]["userTier"] = "featured"
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    payload = _extract_reading_json(html)
    assert trip["assets"][0]["id"] in payload["featuredAssetIds"]


def test_draft_inline_edit_disables_present(screens_trip: tuple[Path, dict]) -> None:
    """AC-EXP-09: draft preview keeps hybrid scroll but omits present bundle."""
    ws, trip = screens_trip
    html = render_html(
        trip,
        export_mode="draft",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-inline-edit="on"' in html
    assert 'data-screenplay="on"' not in html
    assert "screenplay.js" not in html
    assert "screenplay-start" not in html
    assert 'data-reading-profile="default_hybrid"' in html


def test_share_surface_includes_present(screens_trip: tuple[Path, dict]) -> None:
    ws, trip = screens_trip
    html = render_html(
        trip,
        export_mode="share",
        trip_root=ws,
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-screenplay="on"' in html
    assert "screenplay.js" in html
