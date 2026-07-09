"""Tests for scripts/studio_lcp_measure.py (M20-i · LCP P95)."""



from __future__ import annotations

import importlib.util
import sys

import pytest

from tests._repo_root import repo_root

_SCRIPT = repo_root(__file__) / "scripts" / "studio_lcp_measure.py"
_spec = importlib.util.spec_from_file_location("studio_lcp_measure", _SCRIPT)
lcp_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_lcp_measure"] = lcp_mod
_spec.loader.exec_module(lcp_mod)


def test_percentile_interpolation() -> None:
    vals = [10, 20, 30, 40, 50]
    assert lcp_mod.percentile(vals, 50) == 30.0
    assert lcp_mod.percentile(vals, 0) == 10.0
    assert lcp_mod.percentile(vals, 100) == 50.0
    # 线性插值：p75 落在 40 与 50 之间
    assert lcp_mod.percentile(vals, 75) == pytest.approx(40.0)
    assert lcp_mod.percentile([], 95) == 0.0
    assert lcp_mod.percentile([42], 95) == 42.0


def test_summarize_filters_nonpositive() -> None:
    s = lcp_mod.summarize([100, 200, 0, None, 300])
    assert s["n"] == 3
    assert s["p50"] == 200.0
    assert s["max"] == 300.0
    assert s["mean"] == pytest.approx(200.0)


def test_summarize_empty() -> None:
    s = lcp_mod.summarize([])
    assert s["n"] == 0
    assert s["p95"] == 0.0


def test_rollback_flag_triggers_when_v2_slower() -> None:
    summary = {
        "v2": {"n": 10, "p95": 2000.0},
        "classic": {"n": 10, "p95": 1000.0},  # v2 比 classic 慢 100% > 30%
    }
    flags = lcp_mod.lcp_rollback_flags(summary)
    assert any(f.startswith("ROLLBACK") for f in flags)


def test_rollback_flag_ok_within_threshold() -> None:
    summary = {
        "v2": {"n": 10, "p95": 1100.0},  # +10% < 30%
        "classic": {"n": 10, "p95": 1000.0},
    }
    flags = lcp_mod.lcp_rollback_flags(summary)
    assert flags and flags[0].startswith("OK")


def test_rollback_flag_insufficient_without_holdback() -> None:
    flags = lcp_mod.lcp_rollback_flags({"v2": {"n": 10, "p95": 1000.0}})
    assert any("INSUFFICIENT_DATA" in f for f in flags)


def test_rollback_flag_metric_mismatch() -> None:
    summary = {
        "v2": {"n": 5, "p95": 1000.0, "metric": "fcp"},
        "v3": {"n": 5, "p95": 1000.0, "metric": "lcp"},
    }
    flags = lcp_mod.lcp_rollback_flags(summary)
    assert any("指标不一致" in f for f in flags)


def test_variant_paths() -> None:
    assert lcp_mod.VARIANT_PATHS["v2"] == "/"
    assert lcp_mod.VARIANT_PATHS["classic"] == "/classic"
    assert lcp_mod.LEGACY_VARIANT_ALIASES["v3"] == "classic"


def test_lcp_baseline_fixture_valid() -> None:
    """docs/studio-homepage-v2/lcp-baseline.json 结构合法。"""
    import json

    path = (
        repo_root(__file__)
        / "docs"
        / "studio-homepage-v2"
        / "lcp-baseline.json"
    )
    body = json.loads(path.read_text(encoding="utf-8"))
    assert body["schema"] == "studio-homepage-lcp-baseline/v1"
    assert body["min_runs_required"] >= 10
    ref = body["reference"]
    for variant in ("v2", "classic"):
        assert ref[variant]["p95"] > 0
        assert ref[variant]["n"] >= 10
    ratio = body["rollback_ratio"]
    assert ref["v2"]["p95"] <= ref["classic"]["p95"] * ratio
