"""AC-ARC-13 · Studio route table snapshot (method+path+handler)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.web.studio_dispatch import studio_route_snapshot

_BASELINE = Path(__file__).resolve().parent / "fixtures" / "studio_route_snapshot.json"


def test_studio_route_snapshot_matches_baseline() -> None:
    expected = json.loads(_BASELINE.read_text(encoding="utf-8"))
    actual = studio_route_snapshot()
    assert actual == expected, (
        "Route table changed — update tests/unit/web/fixtures/studio_route_snapshot.json "
        "intentionally when adding/removing Studio routes."
    )


def test_studio_route_snapshot_has_serve_trip_post_entries() -> None:
    rows = {(r["method"], r["path"], r["handler"]) for r in studio_route_snapshot()}
    assert ("POST", "{tripId}/__travelogue/save-copy", "serve._handle_save_copy") in rows
    assert ("POST", "{tripId}/__travelogue/promote-tier", "serve._handle_promote_tier") in rows
    assert ("POST", "{tripId}/__travelogue/rerender", "trip_handlers.handle_rerender") in rows
