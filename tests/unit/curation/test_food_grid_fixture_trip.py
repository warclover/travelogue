"""Phase 10 fixture trip verification for manual acceptance support."""



from __future__ import annotations

import json

from tests._repo_root import repo_root
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.layout_engine.planner.screen_planner import (
    FOOD_GRID_LAYOUT_HINT,
    attach_screens_to_chapters,
)


def test_phase10_fixture_trip_produces_food_grid_screen() -> None:
    fixture = (
        repo_root(__file__)
        / "schemas"
        / "fixtures"
        / "trip.phase10_food_grid.json"
    )
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    assets = trip.get("assets") or []
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in assets}
    chapters = attach_screens_to_chapters(
        trip.get("chapters") or [],
        aspects,
        assets=assets,
        plan_scope="chapter",
        trip_photo_total=len(assets),
        enable_food_grid=True,
    )
    screens = [sc for ch in (chapters or []) for sc in (ch.get("screens") or [])]
    assert any(sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT for sc in screens)
    assert any(sc.get("patternId") == "screen-square-4" for sc in screens)
    used_ids = {slot.get("assetId") for sc in screens for slot in (sc.get("slots") or [])}
    assert "l1" in used_ids
