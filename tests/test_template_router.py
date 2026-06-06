"""Phase 13 template router tests."""

from __future__ import annotations

from travelogue.config import AppConfig, TemplateRouterConfig
from travelogue.templating.resolver import is_template_locked
from travelogue.templating.router import (
    REASON_MANUAL,
    apply_template_selection,
    compute_decision_hash,
    replay_template_decision,
    route_template,
    template_user_feedback,
)


def _cfg(*, enabled: bool = True) -> AppConfig:
    return AppConfig(template_router=TemplateRouterConfig(enabled=enabled))


def test_manual_override_priority() -> None:
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["A"]}}
    sel = route_template(trip, mode="manual", requested_template_id="visual-journal", cfg=_cfg())
    assert sel["resolvedTemplateId"] == "visual-journal"
    assert REASON_MANUAL in sel["reasonCodes"]
    assert sel["decisionHash"].startswith("sha256:")


def test_smart_fallback_low_confidence() -> None:
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-03", "places": ["A", "B"]}, "assets": []}
    sel = route_template(trip, mode="smart", cfg=_cfg())
    assert sel["resolvedTemplateId"] == "visual-journal"
    assert "decisionHash" in sel


def test_freeze_manual_no_recompute() -> None:
    trip = {
        "templateSelection": {
            "mode": "manual",
            "resolvedTemplateId": "visual-journal",
            "decisionHash": "sha256:abc",
        },
        "pipeline": {"locks": {"copy": False}},
    }
    out = apply_template_selection(trip, mode="smart", cfg=_cfg(), recompute=False)
    assert out["decisionHash"] == "sha256:abc"


def test_copy_locked_blocks_recompute() -> None:
    trip = {
        "templateSelection": {
            "mode": "smart",
            "resolvedTemplateId": "visual-journal",
            "decisionHash": "sha256:locked",
        },
        "pipeline": {"locks": {"copy": True}},
    }
    assert is_template_locked(trip)
    out = apply_template_selection(trip, mode="smart", cfg=_cfg(), recompute=True)
    assert out["decisionHash"] == "sha256:locked"


def test_replay_decision_hash_stable() -> None:
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["X"]}}
    apply_template_selection(trip, mode="smart", cfg=_cfg())
    replay = replay_template_decision(trip, cfg=_cfg())
    assert replay["match"] is True
    assert "features" in replay
    assert replay.get("featureSummary")


def test_template_user_feedback_kinds() -> None:
    assert template_user_feedback({"mode": "smart", "resolvedTemplateId": "visual-journal"})["kind"] == "smart"
    assert template_user_feedback({"mode": "manual", "resolvedTemplateId": "visual-journal"})["kind"] == "manual"
    assert template_user_feedback({"fallbackUsed": True, "resolvedTemplateId": "visual-journal"})["kind"] == "fallback"


def test_compute_decision_hash_deterministic() -> None:
    a = {"mode": "smart", "resolvedTemplateId": "visual-journal", "reasonCodes": ["R"], "fallbackUsed": False,
         "routerVersion": "p13-r1", "routerConfigVersion": "c", "featureSnapshotVersion": "f", "registryVersion": "r",
         "requestedTemplateId": None}
    h1 = compute_decision_hash(a)
    h2 = compute_decision_hash(dict(a))
    assert h1 == h2
