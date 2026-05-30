"""Copy subject resolution (title vs place vs EXIF)."""



from __future__ import annotations



from travelogue.curation.time_segments import cluster_time_segments

from travelogue.render.context import build_epilogue_stats, chapter_divider
from travelogue.services.copy_subject import (
    filter_chapter_places_for_copy,
    narrative_copy_subject,
    place_conflicts_with_title,
    suppress_chapter_geo_places,
    user_place_explicit,
)
from travelogue.services.narrative_brief import build_chapter_brief

from travelogue.services.narrate import run_narrate

from travelogue.services.narrative_scope import SCOPE_FRAME





def test_narrative_copy_subject_prefers_title_when_place_generic() -> None:

    meta = {"title": "小学毕业", "places": ["旅途"]}

    assert narrative_copy_subject(meta) == "小学毕业"





def test_narrative_copy_subject_prefers_title_when_not_user_set() -> None:

    meta = {"title": "小学毕业", "places": ["云南大理"]}

    intent = {"placesUserSet": False}

    assets = [{"place": {"city": "大理"}}]

    assert narrative_copy_subject(meta, intent=intent, assets=assets) == "小学毕业"





def test_narrative_copy_subject_keeps_explicit_user_place() -> None:

    meta = {"title": "小学毕业", "places": ["丽江"]}

    intent = {"placesUserSet": True}

    assets = [{"place": {"city": "大理"}}]

    assert narrative_copy_subject(meta, intent=intent, assets=assets) == "丽江"





def test_place_conflicts_with_title_detects_geo_mismatch() -> None:

    assets = [{"place": {"city": "大理"}}]

    assert place_conflicts_with_title("小学毕业", "大理", assets)

    assert place_conflicts_with_title("小学毕业", "云南大理", assets)

    assert not place_conflicts_with_title("大理五日", "大理", assets)





def test_user_place_explicit_requires_flag() -> None:

    meta = {"places": ["大理"]}

    assert not user_place_explicit(meta, intent={"placesUserSet": False})

    assert user_place_explicit(meta, intent={"placesUserSet": True})





def test_stub_hook_uses_title_not_exif_city_when_place_generic() -> None:

    trip = {

        "meta": {

            "title": "小学毕业",

            "dateStart": "2025-06-01",

            "dateEnd": "2025-06-03",

            "places": ["旅途"],

            "tone": "relaxed",

        },

        "intent": {"placesUserSet": False},

        "assets": [

            {

                "id": "a1",

                "type": "image",

                "place": {"city": "大理"},

                "takenAt": "2025-06-01T10:00:00Z",

            },

            {

                "id": "a2",

                "type": "image",

                "place": {"city": "大理"},

                "takenAt": "2025-06-02T10:00:00Z",

            },

            {

                "id": "a3",

                "type": "image",

                "place": {"city": "大理"},

                "takenAt": "2025-06-03T10:00:00Z",

            },

        ],

        "chapters": [

            {

                "id": "ch-01",

                "index": 1,

                "title": "6月1日",

                "items": [{"type": "media-card", "assetId": "a1"}],

            },

            {

                "id": "ch-02",

                "index": 2,

                "title": "6月2日",

                "items": [{"type": "media-card", "assetId": "a2"}],

            },

        ],

        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},

    }

    run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)

    hook = trip["meta"]["hook"]

    assert "小学毕业" in hook

    assert "大理" not in hook

    assert "云南" not in hook





def test_segment_label_uses_title_when_place_not_user_set() -> None:

    assets = [

        {

            "id": "a1",

            "takenAt": "2025-06-04T10:00:00Z",

            "place": {"city": "大理"},

        },

        {

            "id": "a2",

            "takenAt": "2025-06-04T15:00:00Z",

            "place": {"city": "大理"},

        },

    ]

    segs = cluster_time_segments(

        assets,

        gap_days=14,

        place="小学毕业",

        explicit_place=None,

    )

    assert segs

    assert "大理" not in segs[0].label

    assert "云南" not in segs[0].label

    assert "小学毕业" in segs[0].label


def test_suppress_chapter_geo_when_title_not_user_set() -> None:
    meta = {"title": "小学毕业", "places": ["云南大理"]}
    intent = {"placesUserSet": False}
    assets = [{"place": {"city": "大理"}}]
    assert suppress_chapter_geo_places(meta, intent=intent, assets=assets)


def test_suppress_chapter_geo_false_when_user_set_place() -> None:
    meta = {"title": "小学毕业", "places": ["丽江"]}
    intent = {"placesUserSet": True}
    assert not suppress_chapter_geo_places(meta, intent=intent)


def test_chapter_divider_omits_exif_place_for_thematic_title() -> None:
    meta = {"title": "小学毕业", "places": ["旅途"]}
    intent = {"placesUserSet": False}
    ch = {
        "curation": {
            "daySpan": ["2025-06-02"],
            "places": ["大理"],
        }
    }
    out = chapter_divider(ch, 2, meta=meta, intent=intent, assets=[{"place": {"city": "大理"}}])
    assert out.get("showDivider") is True
    assert out.get("dividerDate") == "06.02"
    assert "dividerPlace" not in out


def test_build_epilogue_stats_counts_theme_not_exif_cities() -> None:
    trip = {
        "meta": {"title": "小学毕业", "places": ["旅途"]},
        "intent": {"placesUserSet": False},
        "assets": [
            {"id": "a1", "layoutEligible": True, "place": {"city": "大理"}},
            {"id": "a2", "layoutEligible": True, "place": {"city": "大理"}},
        ],
        "chapters": [
            {"curation": {"daySpan": ["2025-06-01"], "places": ["大理"]}},
            {"curation": {"daySpan": ["2025-06-02"], "places": ["大理"]}},
        ],
    }
    stats = build_epilogue_stats(trip)
    assert stats["placeCount"] == 1
    assert "大理" not in stats["summaryLine"]
    assert "小学毕业" not in stats["summaryLine"]
    assert "1 个地方" in stats["summaryLine"]


def test_build_chapter_brief_strips_exif_places_when_suppressed() -> None:
    trip = {
        "meta": {"title": "小学毕业", "places": ["旅途"]},
        "intent": {"placesUserSet": False},
        "assets": [{"id": "a1", "place": {"city": "大理"}}],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "curation": {"places": ["大理"], "daySpan": ["2025-06-01"]},
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    brief = build_chapter_brief(trip, trip["chapters"][0], tone="relaxed", scope="full")
    assert brief["chapter"]["places"] == []
    assert brief["trip"]["editorialSubject"] == "小学毕业"


