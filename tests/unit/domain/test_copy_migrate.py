"""BE-PFM-25 · 切身份文案回填 / copyOrphans。"""

from __future__ import annotations

from travelogue.config.edition import make_studio_edition_mutator
from travelogue.domain.copy_migrate import (
    KIND_CAPTION,
    KIND_LEAD,
    KIND_TITLE,
    collect_user_copy,
    migrate_copy_after_recompose,
)
from travelogue.domain.copy_origin import mark_origin


def _journal_trip() -> dict:
    ch = {
        "id": "ch-01",
        "title": "手改章名",
        "lead": "手改导语",
        "items": [
            {"type": "media-card", "assetId": "a1", "caption": "手改图注"},
        ],
        "screens": [
            {
                "screenId": "ch-01-sc-01",
                "edited": True,
                "copy": {"kicker": "手改眉题", "body": "手改正文"},
                "slots": [{"assetId": "a1"}],
            }
        ],
    }
    mark_origin(ch, "titleOrigin")
    mark_origin(ch, "leadOrigin")
    mark_origin(ch["items"][0], "captionOrigin")
    return {"chapters": [ch], "studio": {}}


def test_collect_user_copy_skips_stub() -> None:
    trip = _journal_trip()
    trip["chapters"][0]["leadOrigin"] = "stub"
    kinds = {f["kind"] for f in collect_user_copy(trip)}
    assert KIND_TITLE in kinds
    assert KIND_CAPTION in kinds
    assert KIND_LEAD not in kinds


def test_journal_to_portfolio_orphans_body_keeps_title() -> None:
    trip = _journal_trip()
    frags = collect_user_copy(trip)
    trip["chapters"][0]["items"] = [{"type": "media-card", "assetId": "a1"}]
    trip["chapters"][0]["screens"] = [
        {"screenId": "ch-01-sc-01", "slots": [{"assetId": "a1"}]}
    ]
    leftovers = migrate_copy_after_recompose(trip, frags, edition="portfolio")
    assert trip["chapters"][0]["title"] == "手改章名"
    assert trip["chapters"][0]["titleOrigin"] == "user"
    kinds = {row["kind"] for row in leftovers}
    assert kinds == {KIND_LEAD, KIND_CAPTION, "kicker", "body"}
    assert all(row.get("reason") == "portfolio_body" for row in leftovers)
    assert not trip["chapters"][0]["items"][0].get("caption")
    assert trip["studio"]["copyOrphans"]


def test_portfolio_to_journal_replays_orphans_by_asset() -> None:
    trip = {
        "studio": {
            "edition": "portfolio",
            "copyOrphans": [
                {
                    "kind": KIND_CAPTION,
                    "text": "手改图注",
                    "assetIds": ["a1"],
                    "reason": "portfolio_body",
                }
            ],
        },
        "chapters": [
            {
                "id": "ch-01",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "screens": [{"screenId": "ch-01-sc-01", "slots": [{"assetId": "a1"}]}],
            }
        ],
    }
    leftovers = migrate_copy_after_recompose(trip, [], edition="journal")
    assert leftovers == []
    item = trip["chapters"][0]["items"][0]
    assert item["caption"] == "手改图注"
    assert item["captionOrigin"] == "user"
    assert "copyOrphans" not in trip["studio"]


def test_screen_copy_remaps_by_overlapping_asset() -> None:
    trip = {
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    {
                        "screenId": "ch-01-sc-09",
                        "slots": [{"assetId": "a1"}, {"assetId": "a2"}],
                    }
                ],
            }
        ]
    }
    leftovers = migrate_copy_after_recompose(
        trip,
        [
            {
                "kind": "kicker",
                "text": "手改眉题",
                "chapterId": "ch-01",
                "assetIds": ["a2"],
                "screenId": "old-sc",
            }
        ],
        edition="journal",
    )
    assert leftovers == []
    screen = trip["chapters"][0]["screens"][0]
    assert screen["copy"]["kicker"] == "手改眉题"
    assert screen["copyMeta"]["kickerSource"] == "user"


def test_missing_asset_stays_orphan() -> None:
    trip = {"chapters": [{"id": "ch-01", "items": [], "screens": []}]}
    leftovers = migrate_copy_after_recompose(
        trip,
        [{"kind": KIND_CAPTION, "text": "无处可去", "assetIds": ["gone"]}],
        edition="journal",
    )
    assert leftovers[0]["reason"] == "no_slot"
    assert leftovers[0]["text"] == "无处可去"


def test_collect_skips_asset_level_caption() -> None:
    trip = _journal_trip()
    trip["assets"] = [
        {"id": "a1", "caption": "资产级图注", "captionOrigin": "user", "edited": True}
    ]
    texts = {frag["text"] for frag in collect_user_copy(trip)}
    assert "资产级图注" not in texts
    assert "手改图注" in texts


def test_mutator_persists_copy_orphans() -> None:
    memory = {
        "studio": {
            "edition": "portfolio",
            "portfolio": {"pageCountSource": "auto"},
            "copyOrphans": [{"kind": KIND_LEAD, "text": "旧导语"}],
            "layoutVibe": "magazine_default",
        }
    }
    disk = {"studio": {"layoutVibe": "magazine_default"}}
    make_studio_edition_mutator(memory)(disk)
    assert disk["studio"]["copyOrphans"][0]["text"] == "旧导语"
    assert disk["studio"]["layoutVibe"] == "magazine_default"


def test_mutator_pops_empty_copy_orphans() -> None:
    memory = {"studio": {"edition": "portfolio"}}
    disk = {
        "studio": {
            "edition": "portfolio",
            "copyOrphans": [{"kind": KIND_LEAD, "text": "过期"}],
        }
    }
    make_studio_edition_mutator(memory)(disk)
    assert "copyOrphans" not in disk["studio"]
