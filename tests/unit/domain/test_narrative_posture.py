"""SNR · narrativePosture 纯函数（AC-SNR-01 / D-SNR-01）。"""

from travelogue.domain.narrative_posture import (
    has_reader_narrative,
    photo_year_is_outlier,
    resolve_narrative_posture,
    trip_primary_year,
)


def test_photo_led_when_no_narrative_and_no_ai() -> None:
    trip = {"meta": {}, "chapters": [{"lead": ""}, {"intro": ""}]}
    assert resolve_narrative_posture(trip) == "photo_led"
    assert has_reader_narrative(trip) is False


def test_upgrade_ready_when_ai_and_llm_ready() -> None:
    trip = {"meta": {}, "chapters": [{"lead": ""}]}
    assert (
        resolve_narrative_posture(
            trip, ai_surface_enabled=True, llm_ready=True
        )
        == "upgrade_ready"
    )


def test_narrative_ready_from_hook() -> None:
    trip = {"meta": {"hook": "湖风里的一天", "title": "周末"}, "chapters": []}
    assert resolve_narrative_posture(trip, ai_surface_enabled=True, llm_ready=True) == (
        "narrative_ready"
    )
    assert has_reader_narrative(trip) is True


def test_narrative_ready_from_chapter_lead() -> None:
    trip = {
        "meta": {"title": "周末"},
        "chapters": [{"lead": "清晨的第一杯茶"}],
    }
    assert resolve_narrative_posture(trip) == "narrative_ready"


def test_banned_hook_does_not_count() -> None:
    trip = {"meta": {"hook": "慢慢翻这一页", "title": "游记"}, "chapters": []}
    assert has_reader_narrative(trip) is False
    assert resolve_narrative_posture(trip, ai_surface_enabled=True, llm_ready=True) == (
        "upgrade_ready"
    )


def test_appendix_lead_ignored() -> None:
    trip = {
        "meta": {},
        "chapters": [
            {"lead": "附录说明", "curation": {"isAppendix": True}},
        ],
    }
    assert has_reader_narrative(trip) is False


def test_trip_primary_year_from_meta() -> None:
    trip = {"meta": {"dateStart": "2024-07-01", "dateEnd": "2024-07-05"}}
    assert trip_primary_year(trip) == 2024


def test_trip_primary_year_from_assets_mode() -> None:
    trip = {
        "meta": {},
        "assets": [
            {"takenAt": "2024-07-01T10:00:00"},
            {"takenAt": "2024-07-02T11:00:00"},
            {"takenAt": "2015-03-12T09:00:00"},
        ],
    }
    assert trip_primary_year(trip) == 2024


def test_photo_year_outlier_delta_ge_2() -> None:
    assert photo_year_is_outlier("2015-03-12T09:00:00", 2024) is True
    assert photo_year_is_outlier("2023-03-12T09:00:00", 2024) is False
    assert photo_year_is_outlier("2022-03-12T09:00:00", 2024) is True
    assert photo_year_is_outlier(None, 2024) is False
