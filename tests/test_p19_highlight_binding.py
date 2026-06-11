"""P19 S6-03 · highlight opener hero binding."""

from __future__ import annotations

from travelogue.curation.highlight_binding import bind_highlight_opener_heroes


def _asset(aid: str, sharp: float) -> dict:
    return {
        "id": aid,
        "quality": {"sharpness": sharp},
        "subjectClass": "landscape",
    }


def test_bind_highlight_opener_heroes_overrides_when_opener_in_window() -> None:
    bucket = [f"a{i}" for i in range(8)]
    assets = {aid: _asset(aid, 10 + idx) for idx, aid in enumerate(bucket)}
    heroes = bind_highlight_opener_heroes(
        {"ch-01": "a0"},
        [bucket],
        assets,
        enabled=True,
        window_sizes=(5,),
        max_windows=1,
    )
    assert heroes["ch-01"] in bucket
    assert heroes["ch-01"] != "a0" or assets["a0"]["quality"]["sharpness"] >= 10


def test_bind_highlight_opener_heroes_disabled_is_noop() -> None:
    bucket = ["a0", "a1", "a2"]
    assets = {aid: _asset(aid, 10) for aid in bucket}
    heroes = bind_highlight_opener_heroes(
        {"ch-01": "a0"},
        [bucket],
        assets,
        enabled=False,
    )
    assert heroes == {"ch-01": "a0"}
