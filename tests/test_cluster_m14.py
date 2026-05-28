"""M14 · vision downgrade notice."""

from __future__ import annotations

from travelogue.curation.cluster_decision_log import ClusterDecisionLog
from travelogue.curation.clustering import _vision_downgrade_notice


def test_vision_timeout_notice() -> None:
    log = ClusterDecisionLog()
    log.add("fallback", "E_CLUSTER_VISION_TIMEOUT: scene analysis skipped")
    msg = _vision_downgrade_notice(log, want_vision=True, scene_count=0)
    assert "场景分析" in msg


def test_vision_missing_no_notice() -> None:
    log = ClusterDecisionLog()
    log.add("fallback", "E_CLUSTER_VISION_MISSING: numpy/sklearn not installed")
    assert _vision_downgrade_notice(log, want_vision=True, scene_count=0) == ""
