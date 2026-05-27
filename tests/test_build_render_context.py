"""Characterization tests for build_render_context (P1a tech-debt safety net)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from travelogue.render.context import build_render_context
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.golden_regression import load_golden_trip

_FIXTURE = Path(__file__).resolve().parents[1] / "schemas" / "fixtures" / "trip.render_golden.json"

# Stable top-level keys for regression — excludes volatile assetVersion / paths.
_SNAPSHOT_KEYS = (
    "exportMode",
    "exportLayout",
    "layoutEngine",
    "copyDisplay",
    "isPhotosOnly",
    "isDraft",
    "isShare",
    "includeLongShot",
    "includeLongshotBridge",
    "includeScreenplay",
    "includeBreath",
    "includeBreathFlow",
    "includeBreathScrub",
    "includeBreathGsapRuntime",
    "includeScrollKeyboardNav",
    "folioLite",
    "folioFull",
    "hasTripIndex",
    "hasFeaturedGrid",
    "hasForewordSpread",
    "hasHook",
    "hasEpilogue",
    "coverShowTitle",
    "presentPreviewUrl",
    "lang",
)


def _chapter_summary(chapters: list[dict]) -> list[dict]:
    return [
        {
            "id": ch.get("id"),
            "patternId": ch.get("patternId"),
            "useScreensEngine": ch.get("useScreensEngine"),
            "screenCount": len(ch.get("screens") or []),
            "itemCount": len(ch.get("items") or []),
            "hasLead": ch.get("hasLead"),
            "hasScreenSpread": ch.get("hasScreenSpread"),
        }
        for ch in chapters
    ]


def context_snapshot(ctx: dict) -> dict:
    """Extract stable subset for characterization comparisons."""
    snap = {k: ctx[k] for k in _SNAPSHOT_KEYS if k in ctx}
    snap["chapterSummary"] = _chapter_summary(ctx.get("chapters") or [])
    snap["htmlAttrTokens"] = sorted((ctx.get("htmlExtraAttrs") or "").split())
    if ctx.get("readingJson"):
        snap["readingJson"] = json.loads(ctx["readingJson"])
    return snap


@pytest.fixture
def golden_trip() -> dict:
    if not _FIXTURE.is_file():
        pytest.skip("fixture missing")
    return copy.deepcopy(load_golden_trip())


@pytest.fixture
def screens_trip(golden_trip: dict) -> dict:
    return prepare_trip_web_screens(copy.deepcopy(golden_trip))


def test_build_render_context_draft_web_legacy_profile(golden_trip: dict) -> None:
    ctx = build_render_context(
        golden_trip,
        export_mode="draft",
        reading_profile_override="legacy",
    )
    snap = context_snapshot(ctx)
    assert snap["exportMode"] == "draft"
    assert snap["isDraft"] is True
    assert snap["folioLite"] is False
    assert snap["folioFull"] is False
    assert len(snap["chapterSummary"]) == 4
    assert snap["chapterSummary"][0]["itemCount"] >= 1


def test_build_render_context_mobile_surface(golden_trip: dict) -> None:
    ctx = build_render_context(
        golden_trip,
        export_mode="draft",
        export_layout_override="mobile",
        reading_profile_override="legacy",
    )
    snap = context_snapshot(ctx)
    assert snap["exportLayout"] == "mobile"
    assert 'data-layout="mobile"' in (ctx.get("htmlExtraAttrs") or "")


def test_build_render_context_present_preview(screens_trip: dict) -> None:
    ctx = build_render_context(
        screens_trip,
        export_mode="present-preview",
        index_name="index-present.html",
        reading_profile_override="default_hybrid",
    )
    snap = context_snapshot(ctx)
    assert snap["exportMode"] == "present-preview"
    assert snap["includeScreenplay"] is True
    assert snap["isDraft"] is False


def test_build_render_context_folio_full(screens_trip: dict) -> None:
    ctx = build_render_context(
        screens_trip,
        export_mode="draft",
        reading_profile_override="magazine",
    )
    snap = context_snapshot(ctx)
    assert snap["folioFull"] is True
    assert snap["hasTripIndex"] is True
