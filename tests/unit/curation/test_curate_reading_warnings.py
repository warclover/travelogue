"""Curate warnings for heavy reading-mode combos (PRD-EXPERIENCE P3-4)."""

from __future__ import annotations

from travelogue.curation.curate import reading_experience_warnings


def test_reading_experience_warns_cinematic_folio_full() -> None:
    trip = {
        "export": {
            "reading": {
                "profile": "magazine",
                "scroll": {"breath": "cinematic", "folio": "full"},
            }
        }
    }
    chapters = [{"screens": [{}] * 40}]
    assets = [{"id": f"a{i}"} for i in range(120)]
    warnings = reading_experience_warnings(trip, chapters, assets)
    assert any("cinematic + folio full" in w for w in warnings)
    assert any("40 屏" in w for w in warnings)
    assert any("120 张图" in w for w in warnings)


def test_reading_experience_silent_for_default_hybrid() -> None:
    trip = {"export": {"reading": {"profile": "default_hybrid"}}}
    chapters = [{"screens": [{}] * 50}]
    assets = [{"id": f"a{i}"} for i in range(150)]
    assert reading_experience_warnings(trip, chapters, assets) == []
