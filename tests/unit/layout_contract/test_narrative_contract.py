"""LTN B1 / ADR-020 · Narrative Contract defaults."""

from __future__ import annotations

from travelogue.layout_contract.narrative_contract import (
    derive_narrative_role,
    derive_preserve_group,
    ensure_narrative_contract,
    ensure_narrative_contract_on_chapters,
)


def test_mosaic_hero_defaults_preserve_group():
    screen = {
        "screenId": "ch-sc-01",
        "patternId": "screen-mosaic-4-hero-70-sidebar",
        "slots": [
            {"assetId": "a0", "slot": 0, "role": "main"},
            {"assetId": "a1", "slot": 1},
        ],
    }
    ensure_narrative_contract(screen)
    assert screen["preserveGroup"] is True
    assert screen["narrativeRole"] == "mosaic_hero"
    assert screen["groupId"] == "ch-sc-01"
    assert screen["representativeAssetId"] == "a0"
    assert screen["exportHints"] == {}


def test_mosaic_flat_role():
    assert derive_narrative_role("screen-mosaic-4-2l2p-weighted", slot_count=4) == "mosaic_flat"
    assert derive_preserve_group("screen-mosaic-4-2l2p-weighted", slot_count=4) is True


def test_single_and_breath_do_not_preserve():
    assert derive_preserve_group("screen-landscape-1", slot_count=1) is False
    assert derive_narrative_role("screen-breath-pause") == "breath"
    breath = {
        "screenId": "ch-sc-02",
        "patternId": "screen-breath-pause",
        "slots": [],
    }
    ensure_narrative_contract(breath)
    assert breath["preserveGroup"] is False
    assert breath["narrativeRole"] == "breath"


def test_explicit_values_not_overwritten():
    screen = {
        "screenId": "ch-sc-03",
        "patternId": "screen-mosaic-5-main-hero-plus-4",
        "preserveGroup": False,
        "narrativeRole": "plate",
        "groupId": "custom-g",
        "representativeAssetId": "picked",
        "exportHints": {"longshotMode": "flatten"},
        "slots": [{"assetId": "a0", "role": "main"}],
    }
    ensure_narrative_contract(screen)
    assert screen["preserveGroup"] is False
    assert screen["narrativeRole"] == "plate"
    assert screen["groupId"] == "custom-g"
    assert screen["representativeAssetId"] == "picked"
    # Conflict: preserveGroup false allows flatten hint to remain.
    assert screen["exportHints"].get("longshotMode") == "flatten"


def test_flatten_hint_dropped_when_preserve_true():
    screen = {
        "screenId": "ch-sc-04",
        "patternId": "screen-mosaic-4-hero-70-sidebar",
        "preserveGroup": True,
        "exportHints": {"longshotMode": "flatten"},
        "slots": [{"assetId": "a0", "role": "main"}, {"assetId": "a1"}],
    }
    ensure_narrative_contract(screen)
    assert "longshotMode" not in screen["exportHints"]
    assert screen["exportHints"].get("conflictDropped") == "longshotMode=flatten"


def test_ensure_on_chapters_migration():
    chapters = [
        {
            "screens": [
                {
                    "screenId": "x-1",
                    "patternId": "screen-mosaic-5-main-portrait-3land",
                    "slots": [
                        {"assetId": "m", "role": "main"},
                        {"assetId": "t1"},
                    ],
                }
            ]
        }
    ]
    ensure_narrative_contract_on_chapters(chapters)
    sc = chapters[0]["screens"][0]
    assert sc["preserveGroup"] is True
    assert sc["narrativeRole"] == "mosaic_hero"
