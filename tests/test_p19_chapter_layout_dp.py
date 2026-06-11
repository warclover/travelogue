"""P19 S5-03 · chapter_layout_dp."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from travelogue.config import MosaicConfig
from travelogue.curation.chapter_layout_dp import (
    chapter_dp_enabled,
    plan_mosaic_partition_dp,
    try_plan_chapter_with_dp,
)
from travelogue.curation.screen_planner_stages import build_chapter_plan_context


@pytest.mark.unit
def test_chapter_dp_disabled_by_default() -> None:
    cfg = MosaicConfig()
    assert not chapter_dp_enabled(cfg)


@pytest.mark.unit
def test_plan_mosaic_partition_dp_covers_all_assets() -> None:
    ids = [f"a{i}" for i in range(10)]
    aspects = {aid: "landscape" for aid in ids}
    assets_map = {
        aid: {"id": aid, "width": 1600, "height": 900, "aspectRatio": 1.78}
        for aid in ids
    }
    cfg = MosaicConfig(chapter_dp_enabled=True)
    with patch(
        "travelogue.curation.mosaic.hook.window_has_candidates",
        return_value=True,
    ), patch(
        "travelogue.curation.mosaic.compose.pick_best_window",
    ) as mock_pick:
        from travelogue.curation.mosaic.compose import MosaicWindowLog, WindowPickResult

        def _fake_pick(window, *_args, **_kwargs):
            size = len(window)
            screen = {
                "patternId": "screen-landscape-3",
                "slots": [{"assetId": aid, "slot": i} for i, aid in enumerate(window)],
            }
            log = MosaicWindowLog(
                segment_id="ch",
                window_size=size,
                window_start=0,
                scorer_version=cfg.scorer_version,
                weights_hash="test",
            )
            log.winner_score = 0.8
            log.winner_pattern_id = screen["patternId"]
            return WindowPickResult(screen=screen, log=log, used_legacy=False)

        mock_pick.side_effect = _fake_pick
        planned = plan_mosaic_partition_dp(
            ids,
            aspects,
            assets_map,
            cfg=cfg,
            trip_total=len(ids),
        )
    assert planned is not None
    steps, score = planned
    assert score > 0
    assert sum(size for _, size, _ in steps) == len(ids)


@pytest.mark.unit
def test_try_plan_chapter_with_dp_sets_cursor_to_end() -> None:
    ids = [f"b{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    assets_map = {
        aid: {"id": aid, "width": 1600, "height": 900, "aspectRatio": 1.78}
        for aid in ids
    }
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        chapter_id="ch-dp",
        assets=assets_map,
        enable_mosaic=True,
    )
    cfg = MosaicConfig(chapter_dp_enabled=True)
    with patch("travelogue.curation.mosaic.hook._mosaic_cfg", return_value=cfg):
        with patch(
            "travelogue.curation.mosaic.hook.window_has_candidates",
            return_value=True,
        ), patch(
            "travelogue.curation.mosaic.compose.pick_best_window",
        ) as mock_pick:
            from travelogue.curation.mosaic.compose import MosaicWindowLog, WindowPickResult

            def _fake_pick(window, *_args, **_kwargs):
                size = len(window)
                screen = {
                    "patternId": "screen-landscape-3",
                    "slots": [{"assetId": aid, "slot": i} for i, aid in enumerate(window)],
                }
                log = MosaicWindowLog(
                    segment_id="ch",
                    window_size=size,
                    window_start=0,
                    scorer_version=cfg.scorer_version,
                    weights_hash="test",
                )
                log.winner_score = 0.75
                return WindowPickResult(screen=screen, log=log, used_legacy=False)

            mock_pick.side_effect = _fake_pick
            ok = try_plan_chapter_with_dp(ctx)
    assert ok
    assert ctx.i == len(ids)
    assert len(ctx.screens) >= 1
