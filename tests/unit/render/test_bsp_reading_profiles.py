"""BSP-3 · studio_preview / reader_immersive reading profiles."""

from __future__ import annotations

import pytest

from travelogue.render.reading_profile import (
    VALID_PROFILES,
    load_experience_matrix,
    resolve_reading_payload,
)


@pytest.mark.unit
def test_valid_profiles_include_bsp3() -> None:
    assert "studio_preview" in VALID_PROFILES
    assert "reader_immersive" in VALID_PROFILES


@pytest.mark.unit
def test_experience_matrix_defines_bsp3_profiles() -> None:
    profiles = load_experience_matrix().get("profiles") or {}
    assert "studio_preview" in profiles
    assert "reader_immersive" in profiles
    assert str(profiles["studio_preview"]["scroll"]["folio"]).lower() in ("lite",)
    folio_off = profiles["reader_immersive"]["scroll"]["folio"]
    assert folio_off in ("off", False, "false", None)


@pytest.mark.unit
def test_resolve_reader_immersive_folio_off() -> None:
    trip = {"export": {"reading": {"profile": "reader_immersive"}}}
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["profile"] == "reader_immersive"
    assert payload["scroll"]["folio"] == "off"


@pytest.mark.unit
def test_resolve_studio_preview_folio_lite() -> None:
    trip = {"export": {"reading": {"profile": "studio_preview"}}}
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["profile"] == "studio_preview"
    assert payload["scroll"]["folio"] == "lite"
