"""Studio title-art Route B/C 一次性生成 HTTP 入口
(PRD-COVER-CALLIGRAPHY-TITLE-V1 §8 · D-CAL-14/16/21)。
"""

from __future__ import annotations

from travelogue.web.studio_dispatch import _CAPTURE_MATCHERS, ROUTE_SPECS, _compile_route
from travelogue.web.studio_handlers.common import match_trip_title_art_resolve


def test_title_art_route_matcher() -> None:
    tid = "demo-trip"
    assert (
        match_trip_title_art_resolve(f"/__travelogue/trips/{tid}/title-art/resolve") == tid
    )
    assert match_trip_title_art_resolve(f"/__travelogue/trips/{tid}/title-art/extra") is None


def test_title_art_route_registered() -> None:
    path = "/__travelogue/trips/{tripId}/title-art/resolve"
    specs = [s for s in ROUTE_SPECS if s.path == path]
    assert specs
    spec = specs[0]
    assert spec.method == "POST"
    assert spec.handler == "trip_handlers.handle_post_resolve_title_art"
    assert spec.auth is True
    assert path in _CAPTURE_MATCHERS
    compiled = _compile_route(spec)
    assert compiled.match("/__travelogue/trips/x/title-art/resolve") == "x"


def test_title_art_route_snapshot() -> None:
    from travelogue.web.studio_dispatch import studio_route_snapshot

    rows = studio_route_snapshot()
    hit = [
        r
        for r in rows
        if r["path"] == "/__travelogue/trips/{tripId}/title-art/resolve" and r["method"] == "POST"
    ]
    assert hit
    assert hit[0]["handler"] == "trip_handlers.handle_post_resolve_title_art"
