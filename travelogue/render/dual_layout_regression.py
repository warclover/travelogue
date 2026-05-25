"""Dual layoutEngine regression: legacy vs screens on the same trip."""

from __future__ import annotations

import copy
import re
from collections import Counter

from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.screen_planner import (
    LAYOUT_ENGINE_LEGACY,
    LAYOUT_ENGINE_SCREENS,
    _collect_asset_ids_from_chapter,
    attach_screens_to_chapters,
)
from travelogue.config import default_mixed_proximity_seconds
from travelogue.render.engine import render_html
from travelogue.services.layout import apply_layout_to_trip


def screen_pattern_sequence(html: str) -> list[str]:
    return re.findall(r'data-pattern="(screen-[^"]+)"', html)


def prepare_trip_web_screens(trip: dict) -> dict:
    """Web export + screens[] from current chapter item order."""
    t = copy.deepcopy(trip)
    t["exportLayout"] = "web"
    t["layoutEngine"] = LAYOUT_ENGINE_SCREENS
    t["layoutEngineVersion"] = "screens-2"
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in t.get("assets", []) if a.get("id")}
    summary = (t.get("curation") or {}).get("orientationSummary")
    chapters = t.get("chapters", [])
    seen: set[str] = set()
    bucket: list[str] = []
    for ch in chapters:
        for aid in _collect_asset_ids_from_chapter(ch):
            if aid not in seen:
                seen.add(aid)
                bucket.append(aid)
    t["chapters"] = attach_screens_to_chapters(
        chapters,
        aspects,
        assets=t.get("assets"),
        orientation_summary=summary,
        day_buckets=[bucket] if bucket else None,
        mixed_proximity_seconds=default_mixed_proximity_seconds(),
    )
    from travelogue.curation.chapter_items import compact_chapter_items_for_screens

    compact_chapter_items_for_screens(t["chapters"])
    return t


def prepare_trip_web_legacy(trip: dict) -> dict:
    """Web export + legacy items via layout planner."""
    t = copy.deepcopy(trip)
    apply_layout_to_trip(
        t,
        export_layout="web",
        layout_engine=LAYOUT_ENGINE_LEGACY,
        preserve_titles=True,
    )
    return t


def check_legacy_render_contract(html: str) -> list[str]:
    """Legacy web/mobile render must not use layout-screen blocks."""
    errors: list[str] = []
    if 'data-layout-engine="screens"' in html:
        errors.append("legacy render must not set data-layout-engine=screens")
    if 'data-block="layout-screen"' in html:
        errors.append("legacy render must not contain layout-screen")
    if "layout-screen--16x9" in html:
        errors.append("legacy render must not contain layout-screen--16x9")
    return errors


def check_screens_render_contract(html: str) -> list[str]:
    """Screens engine minimal DOM contract."""
    errors: list[str] = []
    if 'data-layout-engine="screens"' not in html:
        errors.append('missing data-layout-engine="screens"')
    if 'data-block="layout-screen"' not in html:
        errors.append("missing layout-screen block")
    if "layout-screen--16x9" not in html:
        errors.append("missing layout-screen--16x9 class")
    patterns = screen_pattern_sequence(html)
    if not patterns:
        errors.append("no screen-* data-pattern on layout-screen")
    if 'data-block="media-scroll"' in html and "useScreensEngine" not in html:
        # rendered HTML has no handlebars vars; if scroll appears, screens branch failed
        errors.append("screens render should not output media-scroll blocks")
    return errors


def check_legacy_unchanged_vs_baseline(baseline_html: str, legacy_html: str) -> list[str]:
    """Legacy path output should match prior baseline (e.g. golden mobile render)."""
    errors: list[str] = []
    if baseline_html != legacy_html:
        # Allow only longshot attr drift; compare without data-longshot line
        def norm(h: str) -> str:
            h = re.sub(r'\s*data-longshot="[^"]*"', "", h)
            return h

        if norm(baseline_html) != norm(legacy_html):
            errors.append("legacy HTML changed vs baseline (unexpected regression)")
    return errors


def run_dual_engine_checks(trip: dict, *, trip_root=None) -> list[str]:
    """Run legacy + screens contracts on one trip dict."""
    errors: list[str] = []
    baseline = render_html(trip, export_mode="draft", trip_root=trip_root)

    legacy_trip = prepare_trip_web_legacy(trip)
    legacy_html = render_html(legacy_trip, export_mode="draft", trip_root=trip_root)
    errors.extend(check_legacy_render_contract(legacy_html))

    screens_trip = prepare_trip_web_screens(trip)
    if not any(ch.get("screens") for ch in screens_trip.get("chapters", [])):
        errors.append("screens trip has no chapters[].screens")
    screens_html = render_html(
        screens_trip,
        export_mode="draft",
        trip_root=trip_root,
        layout_engine_override=LAYOUT_ENGINE_SCREENS,
    )
    errors.extend(check_screens_render_contract(screens_html))

    return errors


def screen_layout_stats(chapters: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for ch in chapters:
        for sc in ch.get("screens") or []:
            pid = sc.get("patternId")
            if pid:
                counts[pid] += 1
    return counts
