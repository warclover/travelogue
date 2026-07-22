"""CSC W2a · layout_engine public facade exports."""

from __future__ import annotations

import travelogue.layout_engine as le
from travelogue.layout_engine import api


def test_package_reexports_match_api_all() -> None:
    assert set(le.__all__) == set(api.__all__)
    for name in api.__all__:
        assert getattr(le, name) is getattr(api, name)


def test_facade_exports_core_happy_path_symbols() -> None:
    assert callable(api.plan_chapter_screens)
    assert callable(api.attach_screens_to_chapters)
    assert callable(api.compose_trip)
    assert callable(api.resolve_layout_engine)
    assert callable(api.drain_mosaic_capture)
    assert callable(api.annotate_winner_plan_logs)
    assert callable(api.replan_screen)
    assert api.LAYOUT_ENGINE_SCREENS == "screens"
    assert api.ChapterPlanRequest.__name__ == "ChapterPlanRequest"
    assert api.ReplanError.__name__ == "ReplanError"
