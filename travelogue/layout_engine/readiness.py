"""P17 W3b-12 readiness gates (R-P17-20 · do not flip global enabled by default)."""

from __future__ import annotations

from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.layout_engine.rollout import lse_rollout_snapshot


def w3b12_rollout_ready(cfg: AppConfig | None = None) -> dict[str, Any]:
    """Checklist for flipping global enabled=true (manual approval still required)."""
    app = cfg or get_config()
    se = app.layout.strategy_engine
    return {
        "globalEnabled": se.enabled,
        "defaultShouldStayFalse": not se.enabled,
        "rollout": lse_rollout_snapshot(app),
        "capabilitiesDefaultOff": {
            "saliencyScoring": se.capabilities.saliency_scoring,
            "beatProfile": se.capabilities.beat_profile,
            "toneHarmony": se.capabilities.tone_harmony,
            "hungarianAssignment": se.capabilities.hungarian_assignment,
        },
        "notes": "W3b-12 requires product sign-off; use rollout allowlist until global flip.",
    }


def evaluate_readiness_checks(
    *,
    golden_strict_passed: bool,
    dogfood_strict_passed: bool,
    perf_within_budget: bool,
    parity_ok: bool = True,
    quick_share_ok: bool = True,
    zero_step_ok: bool = True,
) -> dict[str, Any]:
    triple = parity_ok and quick_share_ok and zero_step_ok
    ready = golden_strict_passed and dogfood_strict_passed and perf_within_budget and triple
    return {
        "readyForW3b12Review": ready,
        "checks": {
            "controlledParity": parity_ok,
            "quickShareZeroDiff": quick_share_ok,
            "zeroStepE2E": zero_step_ok,
            "goldenMetricsStrict": golden_strict_passed,
            "dogfoodAdmissionStrict": dogfood_strict_passed,
            "curatePerfBudget": perf_within_budget,
        },
        "tripleGate": triple,
    }
