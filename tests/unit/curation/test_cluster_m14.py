"""M14 · vision downgrade notice（SFC W0 · D-SFC-05 人话）。"""

from __future__ import annotations

from travelogue.curation.cluster_decision_log import ClusterDecisionLog
from travelogue.curation.clustering import _vision_downgrade_notice
from travelogue.domain.stage_hints import VISION_DOWNGRADE_NOTICE


def test_vision_timeout_notice() -> None:
    log = ClusterDecisionLog()
    log.add("fallback", "E_CLUSTER_VISION_TIMEOUT: scene analysis skipped")
    msg = _vision_downgrade_notice(log, want_vision=True, scene_count=0)
    assert msg == VISION_DOWNGRADE_NOTICE


def test_vision_missing_notice_sfc() -> None:
    """AC-SFC-05 · 离线/缺栈也要有一次人话降级说明。"""
    log = ClusterDecisionLog()
    log.add("fallback", "E_CLUSTER_VISION_MISSING: numpy/sklearn not installed")
    assert _vision_downgrade_notice(log, want_vision=True, scene_count=0) == VISION_DOWNGRADE_NOTICE


def test_vision_scene_error_notice() -> None:
    log = ClusterDecisionLog()
    log.add("fallback", "scene cluster error: boom")
    assert _vision_downgrade_notice(log, want_vision=True, scene_count=0) == VISION_DOWNGRADE_NOTICE
