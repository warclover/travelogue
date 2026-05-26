"""Mobile render uses full layout planner when items[] is a screens stub."""

from __future__ import annotations

import copy

from travelogue.curation.chapter_items import resolve_chapter_items_for_render
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.screen_planner import LAYOUT_ENGINE_LEGACY
from travelogue.render.context import build_render_context
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.golden_regression import load_golden_trip


def test_mobile_render_replans_stub_items():
    trip = prepare_trip_web_screens(load_golden_trip())
    ch = trip["chapters"][0]
    stub_len = len(ch.get("items") or [])
    assert ch.get("curation", {}).get("layoutStub")

    assets_map = {a["id"]: a for a in trip["assets"]}
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip["assets"]}
    resolved = resolve_chapter_items_for_render(
        ch,
        export_layout="mobile",
        layout_engine=LAYOUT_ENGINE_LEGACY,
        is_longshot=False,
        aspects=aspects,
        assets_map=assets_map,
        trip_photo_total=len(trip["assets"]),
    )
    assert len(resolved) >= stub_len

    ctx = build_render_context(
        trip,
        export_mode="draft",
        layout_engine_override=LAYOUT_ENGINE_LEGACY,
        export_layout_override="mobile",
    )
    ch_ctx = ctx["chapters"][0]
    assert len(ch_ctx["items"]) == len(resolved)


def test_mobile_render_keeps_legacy_items_without_stub():
    trip = copy.deepcopy(load_golden_trip())
    trip["layoutEngine"] = "legacy"
    for ch in trip.get("chapters", []):
        ch.get("curation", {}).pop("layoutStub", None)
    before = len(trip["chapters"][0]["items"])
    ctx = build_render_context(
        trip,
        export_mode="draft",
        layout_engine_override=LAYOUT_ENGINE_LEGACY,
        export_layout_override="mobile",
    )
    assert len(ctx["chapters"][0]["items"]) == before


def test_mobile_gallery_screens_stub_flattens_not_scroll():
    """Gallery + screens engine: mobile should stack screen slots, not one horizontal scroll."""
    trip = prepare_trip_web_screens(load_golden_trip())
    gallery = next(ch for ch in trip["chapters"] if ch.get("patternId") == "gallery")
    if not gallery.get("screens"):
        gallery["patternId"] = "gallery"
        gallery.setdefault("screens", [{"patternId": "screen-landscape-1", "slots": [{"assetId": "a1"}]}])
    assets_map = {a["id"]: a for a in trip["assets"]}
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in trip["assets"]}
    resolved = resolve_chapter_items_for_render(
        gallery,
        export_layout="mobile",
        layout_engine=LAYOUT_ENGINE_LEGACY,
        is_longshot=False,
        aspects=aspects,
        assets_map=assets_map,
        trip_photo_total=len(trip["assets"]),
    )
    assert all(it.get("type") == "media-card" for it in resolved)
    assert len(resolved) >= len(gallery.get("screens") or [])
    assert not any(it.get("type") == "media-scroll" for it in resolved)
