"""VR-P05 moment chapter: visual units (card/row/scroll + screens)."""

from __future__ import annotations

from travelogue.services.validate import chapter_visual_units, validate_trip


def test_chapter_visual_units_card_plus_screens():
    ch = {
        "patternId": "moment",
        "items": [{"type": "media-card", "assetId": "a1"}],
        "screens": [
            {"screenId": "sc-01", "patternId": "screen-landscape-3", "slots": [{"assetId": "a2"}]},
            {"screenId": "sc-02", "patternId": "screen-landscape-1", "slots": [{"assetId": "a3"}]},
        ],
    }
    assert chapter_visual_units(ch) == 3


def test_moment_one_card_plus_one_screen_passes_manifest():
    trip = {
        "version": "0.2",
        "tripId": "demo-test",
        "templateId": "visual-journal",
        "exportLayout": "web",
        "meta": {"title": "测", "dateStart": "2026-05-20", "dateEnd": "2026-05-20", "places": ["京都"]},
        "coverAssetId": "a1",
        "assets": [
            {"id": f"a{i}", "type": "image", "sourceFile": f"s/a{i}.jpg", "displayFile": f"assets/a{i}.webp"}
            for i in range(1, 10)
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "开",
                "items": [{"type": "media-card", "assetId": "a2"}, {"type": "media-card", "assetId": "a3"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "patternId": "moment",
                "title": "中",
                "items": [{"type": "media-card", "assetId": "a4"}],
                "screens": [
                    {
                        "screenId": "ch-02-sc-01",
                        "patternId": "screen-landscape-3",
                        "slots": [
                            {"assetId": "a5", "slot": 0, "fit": "cover"},
                            {"assetId": "a6", "slot": 1, "fit": "cover"},
                            {"assetId": "a7", "slot": 2, "fit": "cover"},
                        ],
                    },
                ],
            },
            {
                "id": "ch-03",
                "index": 3,
                "patternId": "close",
                "title": "终",
                "items": [{"type": "media-card", "assetId": "a8"}, {"type": "media-card", "assetId": "a9"}],
            },
        ],
        "privacy": {"level": "private", "stripExifOnExport": True, "confirmedAt": None},
        "pipeline": {"status": "layout_ready", "locks": {"structure": False, "copy": False}},
    }
    errs = [e for e in validate_trip(trip, level="manifest") if "VR-P05" in e]
    assert not errs, errs


def test_moment_single_card_no_screens_fails_vr_p05():
    trip = {
        "version": "0.2",
        "tripId": "demo-single",
        "templateId": "visual-journal",
        "exportLayout": "web",
        "meta": {"title": "测", "dateStart": "2026-05-20", "dateEnd": "2026-05-20", "places": ["京都"]},
        "coverAssetId": "a1",
        "assets": [
            {"id": f"a{i}", "type": "image", "sourceFile": f"s/a{i}.jpg", "displayFile": f"assets/a{i}.webp"}
            for i in range(1, 8)
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "开",
                "items": [{"type": "media-card", "assetId": "a2"}, {"type": "media-card", "assetId": "a3"}],
            },
            {
                "id": "ch-02",
                "index": 2,
                "patternId": "moment",
                "title": "中",
                "items": [{"type": "media-card", "assetId": "a4"}],
            },
            {
                "id": "ch-03",
                "index": 3,
                "patternId": "close",
                "title": "终",
                "items": [{"type": "media-card", "assetId": "a5"}, {"type": "media-card", "assetId": "a6"}],
            },
        ],
        "privacy": {"level": "private", "stripExifOnExport": True, "confirmedAt": None},
        "pipeline": {"status": "layout_ready", "locks": {"structure": False, "copy": False}},
    }
    errs = [e for e in validate_trip(trip, level="manifest") if "VR-P05" in e]
    assert len(errs) == 1
