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


def test_disabled_meta_dict_with_reason_adds_field_without_changing_base_shape() -> None:
    d = disabled_meta_dict(reason="focal_conflict:veil-footer")
    assert d["version"] == 1
    assert d["enabled"] is False
    assert d["stale"] is False
    assert d["reason"] == "focal_conflict:veil-footer"


def test_route_b_result_serialization_omits_route_c_fields() -> None:
    result = TitleArtResult(
        enabled=True,
        engine=ENGINE_ROUTE_B,
        main_rendered="拾光",
        asset_path="trip-derived/title-art/abc.png",
        opening_style_id="veil-footer",
        cover_asset_id="asset-1",
    )
    d = result.to_meta_dict()
    assert d["engine"] == ENGINE_ROUTE_B
    assert d["enabled"] is True
    assert d["assetPath"] == "trip-derived/title-art/abc.png"
    assert d["coverAssetId"] == "asset-1"
    assert "styleId" not in d
    assert "ocrVerified" not in d
    assert "fallbackFrom" not in d


def test_title_art_result_from_meta_roundtrip() -> None:
    from travelogue.cover_engine.title_art.models import title_art_result_from_meta

    original = TitleArtResult(
        enabled=True,
        engine=ENGINE_ROUTE_B,
        main_rendered="拾光",
        opening_style_id="veil-footer",
        cover_asset_id="a1",
        asset_path="x.png",
    )
    restored = title_art_result_from_meta(original.to_meta_dict())
    assert restored.enabled is True
    assert restored.cover_asset_id == "a1"
    assert restored.asset_path == "x.png"
    assert restored.opening_style_id == "veil-footer"


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
