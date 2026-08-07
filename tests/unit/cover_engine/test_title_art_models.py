"""Unit tests · trip.meta.titleArt serialization (PRD §8)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.models import (
    ENGINE_ROUTE_B,
    ENGINE_ROUTE_C,
    TitleArtResult,
    disabled_meta_dict,
)

pytestmark = pytest.mark.unit


def test_disabled_meta_dict_shape() -> None:
    d = disabled_meta_dict()
    assert d == {"version": 1, "enabled": False, "stale": False}


def test_route_b_result_serialization_omits_route_c_fields() -> None:
    result = TitleArtResult(
        enabled=True,
        engine=ENGINE_ROUTE_B,
        main_rendered="拾光",
        asset_path="trip-derived/title-art/abc.png",
        opening_style_id="veil-footer",
    )
    d = result.to_meta_dict()
    assert d["engine"] == ENGINE_ROUTE_B
    assert d["enabled"] is True
    assert d["assetPath"] == "trip-derived/title-art/abc.png"
    assert "styleId" not in d
    assert "ocrVerified" not in d
    assert "fallbackFrom" not in d


def test_route_b_result_with_fallback_from_still_records_it() -> None:
    result = TitleArtResult(
        enabled=True,
        engine=ENGINE_ROUTE_B,
        fallback_from=ENGINE_ROUTE_C,
    )
    d = result.to_meta_dict()
    assert d["fallbackFrom"] == ENGINE_ROUTE_C


def test_route_c_result_serialization_includes_route_c_fields() -> None:
    result = TitleArtResult(
        enabled=True,
        engine=ENGINE_ROUTE_C,
        style_id="cascade-seal",
        prompt_version="v1",
        model_provider="wanxiang",
        ocr_verified=True,
        fallback_from=None,
    )
    d = result.to_meta_dict()
    assert d["styleId"] == "cascade-seal"
    assert d["promptVersion"] == "v1"
    assert d["modelProvider"] == "wanxiang"
    assert d["ocrVerified"] is True
    assert d["fallbackFrom"] is None


def test_default_position_is_mutable_copy_not_shared_reference() -> None:
    a = TitleArtResult()
    b = TitleArtResult()
    a.position["x"] = 0.9
    assert b.position["x"] == 0.5
