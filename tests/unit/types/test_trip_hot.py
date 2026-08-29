"""RCL W2 · hot-path TypedDicts (AC-RCL-20)."""

from __future__ import annotations

import json

import pytest

from scripts.lint_rcl_orchestrators import ROOT
from travelogue.config.edition import is_portfolio_trip, read_trip_edition, resolve_edition
from travelogue.render.assemble_cover import _resolve_title_art_src
from travelogue.types.trip_hot import read_studio_block, read_title_art_meta

pytestmark = [pytest.mark.unit]

SCHEMA = ROOT / "schemas" / "trip.schema.json"


def test_missing_fields_do_not_explode() -> None:
    assert read_studio_block(None) == {}
    assert read_studio_block({}) == {}
    assert read_studio_block({"studio": "nope"}) == {}
    assert read_title_art_meta(None) is None
    assert read_title_art_meta({}) is None
    assert read_title_art_meta({"meta": {}}) is None
    assert read_trip_edition({}) is None
    assert resolve_edition({}) == "journal"
    assert is_portfolio_trip({}) is False
    assert is_portfolio_trip(None) is False


def test_edition_defaults_to_journal() -> None:
    assert resolve_edition({"studio": {}}) == "journal"
    assert resolve_edition({"studio": {"edition": ""}}) == "journal"
    assert is_portfolio_trip({"studio": {"edition": "portfolio"}}) is True
    studio = read_studio_block({"studio": {"edition": "portfolio"}})
    assert studio.get("edition") == "portfolio"


def test_title_art_guards_match_resolve() -> None:
    empty = _resolve_title_art_src({}, "veil-footer")
    assert empty[0] is None
    assert empty[1] is False

    stale = {
        "coverAssetId": "asset-001",
        "meta": {
            "titleArt": {
                "enabled": True,
                "stale": True,
                "assetPath": "title-art.png",
                "openingStyleId": "veil-footer",
                "coverAssetId": "asset-001",
                "position": {"x": 0.5, "y": 0.25},
            }
        },
    }
    assert read_title_art_meta(stale) is not None
    assert _resolve_title_art_src(stale, "veil-footer")[1] is False

    live = {
        "coverAssetId": "asset-001",
        "meta": {
            "titleArt": {
                "enabled": True,
                "stale": False,
                "assetPath": "title-art.png",
                "openingStyleId": "veil-footer",
                "coverAssetId": "asset-001",
                "position": {"x": 0.4, "y": 0.2},
            }
        },
    }
    src, show, x_pct, y_pct, _attr = _resolve_title_art_src(live, "veil-footer")
    assert src == "title-art.png"
    assert show is True
    assert x_pct == "40.00%"
    assert y_pct == "20.00%"


def test_schema_subset_and_title_art_is_runtime() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    text = SCHEMA.read_text(encoding="utf-8")
    studio = schema["$defs"]["tripStudio"]["properties"]
    meta = schema["$defs"]["meta"]["properties"]
    chapter = schema["$defs"]["chapter"]
    assert "edition" in studio
    assert "id" in chapter["properties"]
    assert "id" in chapter["required"]
    assert "coverSecondaryAssetId" in meta
    assert "titleArt" not in meta
    assert "titleArt" not in text
    assert "runtime" in (ROOT / "travelogue/types/trip_hot.py").read_text(encoding="utf-8")
