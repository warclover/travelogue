"""ALG-V3 · AC-20 / AC-21 gate tests against frozen baselines."""

from __future__ import annotations

import json

import pytest

from tests.unit.layout_engine._alg3_corpus import (
    AC21_LAYOUT_BASELINE,
    BUILD_SCREEN_BASELINE,
    ac20_total_build_screen_calls,
    run_alg3_corpus,
)


def _load(path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_ac20_build_screen_calls_strictly_below_w0_baseline() -> None:
    """AC-20: B2a-on absolute buildScreenCalls must strictly drop vs W0 baseline.

    Main MCS windows alone may not drop (signature collapses to matched SKUs);
    the frozen total includes the mismatch probe where static_precheck skips builds.
    """
    baseline = _load(BUILD_SCREEN_BASELINE)
    assert baseline.get("status") == "frozen", "AC-20 baseline still pending_freeze"
    expected = baseline.get("totalBuildScreenCalls")
    assert isinstance(expected, int) and expected > 0
    prior_b2a = baseline.get("b2aOnBuildScreenCalls")
    assert isinstance(prior_b2a, int) and prior_b2a < expected, (
        "frozen baseline must record a real B2a drop (probe required)"
    )

    live = ac20_total_build_screen_calls(precheck_enabled=True)
    assert live["buildScreenCalls"] < expected, (
        f"AC-20 expects a strict drop; live={live['buildScreenCalls']} "
        f"baseline={expected} probe={live.get('probe')}"
    )
    assert live["buildScreenCalls"] == prior_b2a


def test_ac21_layout_projection_matches_frozen_baseline() -> None:
    """AC-21: patternId+slotAssetIds(+slotRoles) vs frozen file (not self-dual-run)."""
    baseline = _load(AC21_LAYOUT_BASELINE)
    assert baseline.get("status") == "frozen", "AC-21 baseline still pending_freeze"
    expected_chapters = baseline.get("chapters")
    assert isinstance(expected_chapters, list) and expected_chapters

    live = run_alg3_corpus(precheck_enabled=True)
    assert live["chapters"] == expected_chapters


def test_ac20_w0_path_matches_frozen_total() -> None:
    """Sanity: regenerating W0-equivalent path still hits the frozen total."""
    baseline = _load(BUILD_SCREEN_BASELINE)
    if baseline.get("status") != "frozen":
        pytest.skip("baseline not frozen")
    w0 = ac20_total_build_screen_calls(precheck_enabled=False)
    assert w0["buildScreenCalls"] == baseline["totalBuildScreenCalls"]
