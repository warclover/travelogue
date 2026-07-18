"""R2.1 · cover subtitle from userNotes / meta.subtitle + date range."""

from __future__ import annotations

from travelogue.render.cover_opening import resolve_cover_subtitle


def test_cover_subtitle_uses_user_notes_and_date() -> None:
    trip = {
        "userNotes": "带娃慢走",
        "meta": {
            "title": "雨后京都",
            "places": ["京都"],
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-03",
        },
    }
    shown = resolve_cover_subtitle(trip)
    assert shown.startswith("带娃慢走")
    assert "2026.07.01" in shown
    assert "雨后京都" not in shown


def test_meta_subtitle_wins_over_user_notes() -> None:
    trip = {
        "userNotes": "带娃慢走",
        "meta": {
            "subtitle": "京都漫游手记",
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-01",
        },
    }
    shown = resolve_cover_subtitle(trip)
    assert shown.startswith("京都漫游手记")
    assert "带娃慢走" not in shown


def test_empty_when_no_subtitle_or_notes() -> None:
    assert resolve_cover_subtitle({"meta": {"title": "雨后京都"}}) == ""
