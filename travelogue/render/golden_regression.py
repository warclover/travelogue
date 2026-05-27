"""Golden HTML ↔ render_golden fixture regression (shared by verify + pytest)."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from travelogue.paths import FIXTURES_DIR, GOLDEN_HTML
from travelogue.render.dom_compare import dom_signature
from travelogue.render.engine import render_html

GOLDEN_TRIP_FIXTURE = FIXTURES_DIR / "trip.render_golden.json"
EXPECTED_CHAPTER_PATTERNS = ("open", "moment", "gallery", "close")

REQUIRED_BLOCK_KEYS = [
    "header:block=cover-hero",
    "div:block=trip-meta",
    "p:block=hook-line",
    "section:ch-01:open",
    "section:ch-02:moment",
    "section:ch-03:gallery",
    "section:ch-04:close",
    "div:block=media-scroll",
    "p:block=epilogue",
    "footer:block=footer-cta",
]


def load_golden_trip() -> dict:
    return json.loads(GOLDEN_TRIP_FIXTURE.read_text(encoding="utf-8"))


def pattern_sequence(html: str) -> list[str]:
    return re.findall(r'data-pattern="([^"]+)"', html)


def check_golden_structure(trip: dict) -> list[str]:
    """Chapter count and patternIds vs golden contract."""
    errors: list[str] = []
    chapters = trip.get("chapters") or []
    if len(chapters) != len(EXPECTED_CHAPTER_PATTERNS):
        errors.append(
            f"chapters: expected {len(EXPECTED_CHAPTER_PATTERNS)}, got {len(chapters)}"
        )
    for i, (ch, pid) in enumerate(zip(chapters, EXPECTED_CHAPTER_PATTERNS)):
        got = ch.get("patternId")
        if got != pid:
            errors.append(f"chapters[{i}].patternId: expected {pid!r}, got {got!r}")
    row_count = sum(1 for ch in chapters for it in ch.get("items") or [] if it.get("type") == "media-row")
    if row_count:
        errors.append(f"unexpected media-row in golden fixture ({row_count})")
    scroll_count = sum(
        1 for ch in chapters for it in ch.get("items") or [] if it.get("type") == "media-scroll"
    )
    if scroll_count != 1:
        errors.append(f"media-scroll: expected 1, got {scroll_count}")
    return errors


def check_golden_dom(*, trip: dict | None = None, golden_html: str | None = None) -> list[str]:
    """Compare rendered fixture HTML to hand-maintained golden.html."""
    errors: list[str] = []
    trip = trip if trip is not None else load_golden_trip()
    golden_html = golden_html if golden_html is not None else GOLDEN_HTML.read_text(encoding="utf-8")
    rendered = render_html(
        trip, export_mode="draft", reading_profile_override="legacy"
    )

    if pattern_sequence(rendered) != pattern_sequence(golden_html):
        errors.append("data-pattern sequence mismatch vs golden.html")

    g = Counter(dom_signature(golden_html))
    r = Counter(dom_signature(rendered))
    for key in REQUIRED_BLOCK_KEYS:
        if r[key] < 1:
            errors.append(f"rendered missing {key}")
        if g[key] < 1:
            errors.append(f"golden.html missing {key}")

    if r["figure:block=media-card"] < 6:
        errors.append(f"media-card count low: {r['figure:block=media-card']}")
    if r["div:block=voice-bar"] < 2:
        errors.append(f"voice-bar count low: {r['div:block=voice-bar']}")

    if r["div:block=share-toolbar"] < 1:
        errors.append("missing share-toolbar (P0 save-longshot / share)")

    return errors


def run_golden_regression() -> list[str]:
    """Full golden gate: structure + DOM."""
    if not GOLDEN_TRIP_FIXTURE.is_file():
        return [f"missing fixture {GOLDEN_TRIP_FIXTURE}"]
    if not GOLDEN_HTML.is_file():
        return [f"missing golden.html: {GOLDEN_HTML}"]
    trip = load_golden_trip()
    errors = check_golden_structure(trip)
    errors.extend(check_golden_dom(trip=trip))
    return errors
