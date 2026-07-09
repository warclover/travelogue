"""Discovery sort modes latest/popular/team (REL-10)."""

from __future__ import annotations

from travelogue.templating.discovery import sort_consumer_templates


def test_sort_team_puts_recommended_first() -> None:
    items = [
        {"templateId": "event-recap", "category": "event"},
        {"templateId": "visual-journal", "category": "travel"},
    ]
    out = sort_consumer_templates(
        items,
        display_order=("visual-journal", "event-recap"),
        recommended=("visual-journal",),
        sort_mode="team",
        team_templates=("visual-journal",),
    )
    assert out[0]["templateId"] == "visual-journal"


def test_sort_alphabetical() -> None:
    items = [{"templateId": "event-recap"}, {"templateId": "visual-journal"}]
    out = sort_consumer_templates(
        items,
        display_order=(),
        recommended=(),
        sort_mode="alphabetical",
    )
    assert out[0]["templateId"] == "event-recap"
