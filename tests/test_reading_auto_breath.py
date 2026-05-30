"""P5-S1 · auto breath profile by photo count."""

from __future__ import annotations

from travelogue.render.reading_profile import (
    auto_breath_for_trip,
    count_trip_photos,
    resolve_reading_payload,
)


def _trip(n: int) -> dict:
    return {"assets": [{"id": f"a{i}", "kind": "photo"} for i in range(n)], "chapters": []}


def test_count_trip_photos_uses_image_type() -> None:
    trip = {
        "assets": [
            {"id": "a1", "type": "image"},
            {"id": "a2", "type": "video"},
            {"id": "a3", "kind": "photo"},
        ]
    }
    assert count_trip_photos(trip) == 2


def test_count_trip_photos() -> None:
    assert count_trip_photos(_trip(0)) == 0
    assert count_trip_photos(_trip(19)) == 19


def test_auto_breath_thresholds() -> None:
    assert auto_breath_for_trip(_trip(10)) == "soft"
    assert auto_breath_for_trip(_trip(19)) == "soft"
    assert auto_breath_for_trip(_trip(20)) == "flow"
    assert auto_breath_for_trip(_trip(50)) == "flow"
    assert auto_breath_for_trip(_trip(51)) == "cinematic"


def test_resolve_applies_auto_breath_web_draft() -> None:
    payload = resolve_reading_payload(_trip(25), export_mode="draft", export_layout_override="web")
    assert payload["scroll"]["breath"] == "flow"
    assert payload["scroll"]["breathEngine"] == "native"


def test_resolve_cinematic_uses_gsap() -> None:
    payload = resolve_reading_payload(_trip(80), export_mode="draft", export_layout_override="web")
    assert payload["scroll"]["breath"] == "cinematic"
    assert payload["scroll"]["breathEngine"] == "gsap"


def test_explicit_scroll_breath_not_overridden() -> None:
    trip = _trip(80)
    trip["export"] = {"reading": {"scroll": {"breath": "soft"}}}
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["scroll"]["breath"] == "soft"
