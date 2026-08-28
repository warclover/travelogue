"""PFM · page-* may persist on portfolio trips; journal MCS whitelist unchanged."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from travelogue.layout_contract.active_set import schema_all_pattern_ids
from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip
from travelogue.layout_templates.page_promote import P0_PAGE_IDS
from travelogue.paths import ROOT, SCHEMA_PATH
from travelogue.services.validate import validate_page_pattern_ids, validate_schema

pytestmark = pytest.mark.unit

_LINZHI = ROOT / "schemas" / "fixtures" / "trip.linzhi_screens.json"


def _layout_screen_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        {
            "$schema": schema.get("$schema"),
            "$defs": schema["$defs"],
            "$ref": "#/$defs/layoutScreen",
        }
    )


def _assets_for_p0() -> list[dict]:
    bands = [1, 1, 2, 6, 4, 3, 5, 1, 4, 3, 6, 3, 5, 2, 6, 1]
    assets: list[dict] = []
    n = 0
    for i, band in enumerate(bands, 1):
        for _ in range(band):
            n += 1
            assets.append(
                {
                    "id": f"a{n:03d}",
                    "shotGroupId": f"g{i}",
                    "shotGroupKind": "scene",
                }
            )
    return assets


def test_schema_all_pattern_ids_excludes_page_star() -> None:
    ids = schema_all_pattern_ids()
    assert "screen-landscape-1" in ids
    assert "screen-breath-pause" in ids
    assert not any(str(i).startswith("page-") for i in ids)


def test_p0_composed_screens_are_layout_screen_legal() -> None:
    assets = _assets_for_p0()
    chapters = [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": a["id"]} for a in assets],
            "screens": [],
        }
    ]
    trip = {"studio": {"edition": "portfolio"}}
    out, _meta = compose_portfolio_trip(chapters, assets=assets, trip=trip)
    validator = _layout_screen_validator()
    screens = [sc for ch in out for sc in (ch.get("screens") or [])]
    assert len(screens) == 16
    for sc in screens:
        validator.validate(sc)
        assert sc["patternId"] in P0_PAGE_IDS
        assert sc["screenId"].startswith("ch-01-sc-")
        for i, slot in enumerate(sc["slots"]):
            assert slot["slot"] == i
            assert slot["fit"] == "cover"
    assert not validate_page_pattern_ids({"studio": trip["studio"], "chapters": out})


def test_folio_alias_allows_promoted_page_face() -> None:
    trip = {
        "studio": {"edition": "folio"},
        "chapters": [
            {
                "screens": [
                    {
                        "screenId": "ch-01-sc-01",
                        "patternId": "page-1-hero-land-wide",
                        "slots": [{"assetId": "a1", "slot": 0, "fit": "cover"}],
                    }
                ]
            }
        ],
    }
    errs = validate_page_pattern_ids(trip)
    assert not any("portfolio-only" in e for e in errs)


def test_journal_trip_rejects_promoted_page_face() -> None:
    trip = json.loads(_LINZHI.read_text(encoding="utf-8"))
    screen = trip["chapters"][0]["screens"][0]
    screen["patternId"] = "page-1-hero-land-wide"
    errs = validate_page_pattern_ids(trip)
    assert any("portfolio-only" in e for e in errs)


def test_unknown_promoted_page_face_rejected() -> None:
    trip = {
        "studio": {"edition": "portfolio"},
        "chapters": [
            {
                "screens": [
                    {
                        "screenId": "ch-01-sc-01",
                        "patternId": "page-99-not-a-face",
                        "slots": [{"assetId": "a1", "slot": 0, "fit": "cover"}],
                    }
                ]
            }
        ],
    }
    errs = validate_page_pattern_ids(trip)
    assert any("unknown page face" in e for e in errs)


def test_bogus_screen_sku_still_fails_schema_enum() -> None:
    trip = json.loads(_LINZHI.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(trip)
    mutated["chapters"][0]["screens"][0]["patternId"] = "screen-not-a-real-sku"
    errs = [e for e in validate_schema(mutated) if "patternId" in e]
    assert errs
