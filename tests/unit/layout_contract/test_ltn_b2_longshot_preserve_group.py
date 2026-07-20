"""LTN B2 / ADR-020 · longshot preserveGroup three-tier degradation."""

from __future__ import annotations

import logging

from travelogue.layout_contract.chapter_items import (
    resolve_longshot_mode,
    screens_to_longshot_items,
)


def _mosaic_screen(*, preserve: bool | None = None, mode: str | None = None) -> dict:
    sc: dict = {
        "screenId": "ch-sc-01",
        "patternId": "screen-mosaic-4-hero-70-sidebar",
        "slots": [
            {"assetId": "a0", "slot": 0, "role": "main"},
            {"assetId": "a1", "slot": 1},
            {"assetId": "a2", "slot": 2},
            {"assetId": "a3", "slot": 3},
        ],
    }
    if preserve is not None:
        sc["preserveGroup"] = preserve
    if mode is not None:
        sc["exportHints"] = {"longshotMode": mode}
    return sc


def test_default_mosaic_preserves_as_media_row():
    items = screens_to_longshot_items({"screens": [_mosaic_screen()]})
    assert len(items) == 1
    assert items[0]["type"] == "media-row"
    assert items[0]["rowLayout"] == "preserve-stack"
    assert items[0]["assetIds"] == ["a0", "a1", "a2", "a3"]
    assert items[0]["preserveGroup"] is True
    assert items[0]["groupId"] == "ch-sc-01"
    assert "一组" in (items[0].get("groupMark") or "")


def test_explicit_false_flattens_and_logs(caplog):
    sc = _mosaic_screen(preserve=False)
    with caplog.at_level(logging.INFO, logger="travelogue.layout.narrative"):
        items = screens_to_longshot_items({"screens": [sc]})
    assert len(items) == 4
    assert all(it["type"] == "media-card" for it in items)
    assert any("preserve_group_false" in r.message for r in caplog.records)


def test_representative_badge_mode():
    sc = _mosaic_screen(mode="representative_badge")
    assert resolve_longshot_mode(sc) == "representative_badge"
    items = screens_to_longshot_items({"screens": [sc]})
    assert len(items) == 1
    assert items[0]["type"] == "media-card"
    assert items[0]["assetId"] == "a0"
    assert items[0]["groupBadge"] == "+3"


def test_mixed_chapter_preserves_only_mosaic():
    chapter = {
        "screens": [
            {
                "screenId": "s1",
                "patternId": "screen-landscape-1",
                "slots": [{"assetId": "solo"}],
            },
            _mosaic_screen(),
            {
                "screenId": "s3",
                "patternId": "screen-portrait-2",
                "slots": [{"assetId": "p1"}, {"assetId": "p2"}],
                "preserveGroup": False,
            },
        ]
    }
    items = screens_to_longshot_items(chapter)
    # solo card + mosaic row + 2 flattened pair cards
    assert items[0]["type"] == "media-card" and items[0]["assetId"] == "solo"
    assert items[1]["type"] == "media-row" and len(items[1]["assetIds"]) == 4
    assert items[2]["type"] == "media-card" and items[2]["assetId"] == "p1"
    assert items[3]["type"] == "media-card" and items[3]["assetId"] == "p2"
