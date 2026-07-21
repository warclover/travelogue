"""SFI D-SFI-11 · compact folds preserve_stack → representative_badge."""

from travelogue.layout_contract.chapter_items import screens_to_longshot_items


def test_compact_folds_multi_slot_group() -> None:
    chapter = {
        "screens": [
            {
                "screenId": "s1",
                "patternId": "screen-landscape-2",
                "preserveGroup": True,
                "slots": [
                    {"assetId": "a"},
                    {"assetId": "b"},
                ],
            }
        ]
    }
    default_items = screens_to_longshot_items(chapter, compact=False)
    assert default_items and default_items[0].get("type") == "media-row"
    compact_items = screens_to_longshot_items(chapter, compact=True)
    assert compact_items and compact_items[0].get("type") == "media-card"
    assert compact_items[0].get("groupBadge") == "+1"
