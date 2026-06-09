"""Studio replan → layout-feedback sidecar."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from travelogue.config import get_config
from travelogue.layout_engine.feedback import read_layout_feedback_events
from travelogue.layout_engine.studio_feedback import persist_studio_layout_feedback


def test_persist_studio_layout_feedback_writes_sidecar(tmp_path: Path) -> None:
    cfg = get_config(reload=True)
    se = replace(
        cfg.layout.strategy_engine,
        enabled=True,
        feedback=replace(cfg.layout.strategy_engine.feedback, enabled=True),
    )
    cfg_on = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))

    before = {
        "chapters": [
            {
                "id": "ch-1",
                "screens": [{"patternId": "screen-portrait-1", "slots": [{"assetId": "a1"}]}],
            }
        ]
    }
    after = {
        "chapters": [
            {
                "id": "ch-1",
                "screens": [{"patternId": "screen-landscape-3", "slots": [{"assetId": "a1"}]}],
            }
        ]
    }
    summary = persist_studio_layout_feedback(
        "trip-1",
        tmp_path,
        before,
        after,
        cfg=cfg_on,
    )
    assert summary is not None
    events = read_layout_feedback_events(tmp_path)
    assert len(events) == 1
    assert events[0]["editType"] == "pattern_change"
