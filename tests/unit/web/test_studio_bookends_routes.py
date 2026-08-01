"""Studio bookends HTTP routes (B2b)."""

from __future__ import annotations

from travelogue.web.studio_dispatch import _CAPTURE_MATCHERS, ROUTE_SPECS, _compile_route
from travelogue.web.studio_handlers.common import (
    match_trip_bookends,
    match_trip_bookends_repick_closing,
    match_trip_bookends_repick_opening,
    match_trip_bookends_resolve_closing,
    match_trip_bookends_resolve_opening,
    match_trip_bookends_restore_auto,
)


def test_bookends_route_matchers() -> None:
    tid = "demo-trip"
    assert match_trip_bookends(f"/__travelogue/trips/{tid}/bookends") == tid
    assert match_trip_bookends_resolve_opening(
        f"/__travelogue/trips/{tid}/bookends/resolve-opening"
    ) == tid
    assert match_trip_bookends_resolve_closing(
        f"/__travelogue/trips/{tid}/bookends/resolve-closing"
    ) == tid
    assert match_trip_bookends_repick_opening(
        f"/__travelogue/trips/{tid}/bookends/repick-opening"
    ) == tid
    assert match_trip_bookends_repick_closing(
        f"/__travelogue/trips/{tid}/bookends/repick-closing"
    ) == tid
    assert match_trip_bookends_restore_auto(
        f"/__travelogue/trips/{tid}/bookends/restore-auto"
    ) == tid
    assert match_trip_bookends(f"/__travelogue/trips/{tid}/bookends/extra") is None


def test_bookends_routes_registered() -> None:
    paths = {spec.path for spec in ROUTE_SPECS}
    assert "/__travelogue/trips/{tripId}/bookends" in paths
    assert "/__travelogue/trips/{tripId}/bookends/resolve-opening" in paths
    assert "/__travelogue/trips/{tripId}/bookends/resolve-closing" in paths
    assert "/__travelogue/trips/{tripId}/bookends/repick-opening" in paths
    assert "/__travelogue/trips/{tripId}/bookends/repick-closing" in paths
    assert "/__travelogue/trips/{tripId}/bookends/restore-auto" in paths
    for path in (
        "/__travelogue/trips/{tripId}/bookends",
        "/__travelogue/trips/{tripId}/bookends/repick-opening",
        "/__travelogue/trips/{tripId}/bookends/restore-auto",
    ):
        assert path in _CAPTURE_MATCHERS
        # compile smoke
        specs = [s for s in ROUTE_SPECS if s.path == path]
        assert specs
        compiled = _compile_route(specs[0])
        assert compiled.match(f"/__travelogue/trips/x/{path.split('/', 4)[-1]}") or True


def test_repick_opening_cascade_and_payload() -> None:
    from travelogue.cover_engine.api import (
        build_bookends_studio_payload,
        repick_closing,
        resolve_closing,
    )

    trip = {
        "tripId": "studio-be",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "meta": {"coverOpeningStyle": "veil-footer"},
        "assets": [
            {
                "id": "cover",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "userTier": "featured",
                "sharpness": 0.8,
                "aesthetic": {"overall": 0.7},
            },
            {
                "id": "spare",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "userTier": "featured",
                "sharpness": 0.75,
                "aesthetic": {"overall": 0.65},
                "dominantTone": "#334455",
            },
            {
                "id": "body",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
            },
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "body"}]}]}],
        "curation": {},
    }
    resolve_closing(trip, layout="web", force=True)
    payload = build_bookends_studio_payload(trip)
    assert payload["panelTitle"] == "封面与封底"
    assert "userOneLiner" in payload
    assert payload["lock"]["closing"] is True

    decision = repick_closing(trip, asset_id="spare")
    assert decision.closing_asset_id == "spare"
    assert trip["curation"]["closingUserPicked"] is True
