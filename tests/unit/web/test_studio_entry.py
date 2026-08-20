"""Phase 4 M16 · F-P4-PRV-06: preview entry deep-link resolver tests."""

from __future__ import annotations

from travelogue.web.studio_entry import (
    build_chapter_summaries,
    build_entry,
    build_intent_summary,
    edition_chrome,
    resolve_peak_screen_id,
)


def _screen(screen_id: str, asset_ids: list[str], *, arc_segment: str | None = None) -> dict:
    screen = {
        "screenId": screen_id,
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": a} for a in asset_ids],
    }
    if arc_segment:
        screen["arcSegment"] = arc_segment
    return screen


def _trip_with_screens(*chapters_screens: list[dict]) -> dict:
    return {
        "chapters": [{"screens": screens} for screens in chapters_screens],
    }


def test_peak_prefers_best_scored_peak_screen():
    trip = _trip_with_screens(
        [
            _screen("s1", ["a1"], arc_segment="peak"),
            _screen("grid-peak", ["a2", "a3"], arc_segment="peak"),
            _screen("hero-peak", ["a4"], arc_segment="peak"),
        ],
    )
    assert resolve_peak_screen_id(trip) == "hero-peak"


def test_peak_prefers_arc_segment_over_scene_cluster():
    trip = _trip_with_screens(
        [_screen("s1", ["a1"]), _screen("peak", ["a2"], arc_segment="peak")],
        [_screen("s3", ["a9"])],
    )
    trip["curation"] = {
        "clustering": {
            "clusters": [
                {"assetIds": ["a9", "a10", "a11"]},
            ]
        }
    }
    assert resolve_peak_screen_id(trip) == "peak"


def test_peak_prefers_largest_scene_cluster_screen():
    trip = _trip_with_screens(
        [_screen("s1", ["a1", "a2"]), _screen("s2", ["a3"])],
        [_screen("s3", ["a9"])],
    )
    trip["curation"] = {
        "clustering": {
            "clusters": [
                {"assetIds": ["a3"]},
                {"assetIds": ["a9", "a10", "a11"]},  # largest
            ]
        }
    }
    # Largest cluster contains a9 -> screen s3.
    assert resolve_peak_screen_id(trip) == "s3"


def test_peak_falls_back_to_first_content_screen():
    trip = _trip_with_screens(
        [_screen("cover", []), _screen("s2", ["a1"])],
    )
    assert resolve_peak_screen_id(trip) == "s2"


def test_peak_falls_back_to_first_screen_when_no_assets():
    trip = _trip_with_screens([_screen("cover", []), _screen("s2", [])])
    assert resolve_peak_screen_id(trip) == "cover"


def test_peak_none_for_no_screens():
    assert resolve_peak_screen_id({"chapters": []}) is None
    assert resolve_peak_screen_id({}) is None


def test_build_entry_appends_fragment_when_peak_exists():
    trip = _trip_with_screens([_screen("s1", ["a1"])])
    entry = build_entry(trip, "demo-trip")
    assert entry["peakScreenId"] == "s1"
    assert entry["previewUrl"] == "/demo-trip/index.html#screen-s1"
    assert entry["scrollShareUrl"] == "/demo-trip/index.html?share=1#screen-s1"


def test_build_entry_exposes_portfolio_edition() -> None:
    journal = build_entry({"chapters": []}, "demo-trip")
    assert journal["edition"] == "journal"
    assert journal["portfolioPipelineEnabled"] is False
    assert journal["layoutVibeVisible"] is True
    assert journal.get("portfolio") is None

    trip = {
        "studio": {
            "edition": "portfolio",
            "portfolio": {"photosPlaced": 96, "photosKept": 180, "overflow": {"count": 84}},
        },
        "chapters": [],
    }
    entry = build_entry(trip, "demo-trip")
    assert entry["edition"] == "portfolio"
    assert entry["portfolioPipelineEnabled"] is False
    assert entry["layoutVibeVisible"] is False
    assert entry["portfolio"]["photosPlaced"] == 96
    assert entry["portfolio"]["photosKept"] == 180
    assert entry["portfolio"]["pageCountChips"] == [8, 12, 16, 20, 24, 28, 32]
    assert entry["previewUrl"] == "/demo-trip/index.html"
    assert entry["dockCta"]["aria"] == "导出作品集"
    assert entry["overflowLine"] == "本册收录 96 / 180 张"
    assert entry["overflowCta"] == "改用游记（全收）"
    assert journal["dockCta"]["aria"] == "导出长图"
    assert journal["overflowLine"] is None
    assert journal["overflowCta"] is None
    chrome = edition_chrome(trip)
    assert chrome["dockCta"] == entry["dockCta"]
    assert chrome["overflowLine"] == entry["overflowLine"]
    assert chrome["layoutVibeVisible"] is False


def test_build_entry_pipeline_enabled_when_flag_on() -> None:
    from dataclasses import replace

    from travelogue.config import AppConfig, PortfolioPipelineConfig
    from travelogue.config.runtime import config_override

    trip = {"studio": {"edition": "portfolio"}, "chapters": []}
    cfg = replace(
        AppConfig(),
        studio=replace(
            AppConfig().studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=True),
        ),
    )
    with config_override(cfg):
        entry = build_entry(trip, "demo-trip")
    assert entry["portfolioPipelineEnabled"] is True
    assert entry["edition"] == "portfolio"


def test_intent_summary_reads_intent_then_meta():
    trip = {
        "intent": {"title": "京都之秋", "userNotes": "想表达静谧"},
        "meta": {"title": "fallback"},
        "assets": [
            {"userTier": "featured"},
            {"userTier": "featured"},
            {"userTier": "normal"},
        ],
        "curation": {"clustering": {"segments": [{}, {}, {}]}},
    }
    summary = build_intent_summary(trip)
    assert summary["title"] == "京都之秋"
    assert summary["featuredCount"] == 2
    assert summary["segmentCount"] == 3
    assert summary["hasUserNotes"] is True


def test_build_entry_includes_cover_opening_style() -> None:
    trip = {"meta": {"coverOpeningStyle": "magazine-head"}}
    entry = build_entry(trip, "demo-trip")
    # V6 legacy_map: magazine-head → folio-overlap (resolved for Studio consumers)
    assert entry["coverOpeningStyle"] == "folio-overlap"
    assert entry["coverOpeningStyleRaw"] == "magazine-head"
    assert entry["coverLegacyMapped"] is True


def test_build_entry_cover_opening_style_defaults_veil_footer() -> None:
    entry = build_entry({"meta": {}}, "demo-trip")
    assert entry["coverOpeningStyle"] == "veil-footer"


def test_build_entry_title_art_ui_from_meta() -> None:
    from travelogue.web.studio_entry import build_title_art_ui

    assert build_title_art_ui({})["statusLabel"] == "尚未生成"
    assert build_title_art_ui({"meta": {}})["ready"] is False

    ready = build_title_art_ui(
        {
            "meta": {
                "titleArt": {
                    "enabled": True,
                    "engine": "clean-pipeline-v1",
                    "stale": False,
                }
            }
        }
    )
    assert ready["ready"] is True
    assert ready["statusLabel"] == "已生成 · 字库合成"

    route_c = build_title_art_ui(
        {
            "meta": {
                "titleArt": {
                    "enabled": True,
                    "engine": "diffusion-fixed-prompt-v1",
                    "stale": False,
                }
            }
        }
    )
    assert "AI 手写体" in route_c["statusLabel"]

    entry = build_entry(
        {
            "meta": {
                "titleArt": {"enabled": True, "engine": "clean-pipeline-v1"}
            }
        },
        "demo-trip",
    )
    assert entry["titleArtUi"]["ready"] is True


def test_build_entry_includes_pipeline_and_chapters():
    trip = {
        "pipeline": {"status": "structure_draft"},
        "chapters": [{
            "id": "ch-01",
            "title": "京都",
            "screens": [_screen("s1", ["a1"])],
            "curation": {"memoryAnchors": ["寺", "雨"]},
        }],
    }
    entry = build_entry(trip, "demo-trip")
    assert entry["pipelineStatus"] == "structure_draft"
    assert entry["g1Pending"] is True
    assert entry["chapters"][0]["memoryAnchors"] == ["寺", "雨"]
    assert entry["chapters"][0]["copyIntent"] == {}
    assert entry["aesthetic"]["enabled"] is True


def test_chapter_summaries_includes_copy_intent() -> None:
    trip = {
        "chapters": [{
            "id": "ch-01",
            "title": "京都",
            "curation": {
                "memoryAnchors": ["寺"],
                "copyIntent": {"mood": "平静", "focus": "地方", "note": "雨后"},
            },
        }],
    }
    rows = build_chapter_summaries(trip)
    assert rows[0]["copyIntent"] == {"mood": "平静", "focus": "地方", "note": "雨后"}


def test_chapter_summaries_has_voice_flag() -> None:
    trip = {
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "voice": {"transcriptPreview": "雨太大了"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "雨后",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "id": "ch-02",
                "title": "空白",
                "items": [{"type": "media-card", "assetId": "missing"}],
            },
        ],
    }
    rows = build_chapter_summaries(trip)
    assert rows[0]["hasVoice"] is True
    assert rows[1]["hasVoice"] is False


def test_chapter_summaries_empty_without_chapters():
    assert build_chapter_summaries({}) == []
    summary = build_intent_summary({})
    assert summary["title"] == "我的旅途"
    assert summary["featuredCount"] == 0
    assert summary["segmentCount"] == 0
    assert summary["hasUserNotes"] is False
    assert summary["userNotes"] == ""
