"""Window-level golden capability probes."""

from __future__ import annotations

from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from scripts.phase17_golden_metrics import _cfg_lse_enabled, _cfg_with_capabilities
from travelogue.layout_engine.golden_probe import (
    merge_gates,
    probe_ac_p17_16,
    probe_ac_p17_17,
    probe_ac_p17_18,
    probe_ac_p17_19,
    probe_ac_p17_20,
    run_ac_probe,
)


def _pair_cfg(**caps):
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    return (
        _cfg_with_capabilities(base, **{k: False for k in caps}),
        _cfg_with_capabilities(base, **caps),
    )


def test_probe_ac16_measurable_on_p17_fixture() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    b = _cfg_with_capabilities(base, saliency_scoring=False)
    c = _cfg_with_capabilities(base, saliency_scoring=True)
    out = probe_ac_p17_16(trip, baseline_cfg=b, candidate_cfg=c)
    assert out.get("measurable") is True
    assert out.get("passed") is True
    assert (out.get("rankingLiftPp") or 0) >= 3.0


def test_probe_ac17_measurable() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    out = probe_ac_p17_17(trip, baseline_cfg=base, candidate_cfg=base)
    assert out.get("measurable") is True
    assert out.get("passed") is True
    assert (out.get("deltaPp") or 0) >= 8.0


def test_probe_ac19_measurable() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    b = _cfg_with_capabilities(base, hungarian_assignment=False, quality_unified=False)
    c = _cfg_with_capabilities(base, hungarian_assignment=True, quality_unified=True)
    out = probe_ac_p17_19(trip, baseline_cfg=b, candidate_cfg=c)
    assert out.get("measurable") is True


def test_merge_gates_probe_rescue() -> None:
    merged = merge_gates(
        {"passed": False, "measurable": True},
        {"passed": True, "measurable": True},
    )
    assert merged["passed"] is True
    assert merged["probePassed"] is True


def test_probe_ac16_measurable_on_mixed_scenes() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    b = _cfg_with_capabilities(base, saliency_scoring=False)
    c = _cfg_with_capabilities(base, saliency_scoring=True)
    out = probe_ac_p17_16(trip, baseline_cfg=b, candidate_cfg=c)
    assert out.get("measurable") is True
    assert out.get("passed") is True


def test_probe_ac18_tone_penalty_on_mixed_scenes() -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    b = _cfg_with_capabilities(base, tone_harmony=False)
    c = _cfg_with_capabilities(base, tone_harmony=True)
    out = probe_ac_p17_18(trip, baseline_cfg=b, candidate_cfg=c)
    assert out.get("measurable") is True
    assert out.get("passed") is True


def test_probe_ac18_tone_penalty_on_fixture() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    b = _cfg_with_capabilities(base, tone_harmony=False)
    c = _cfg_with_capabilities(base, tone_harmony=True)
    out = probe_ac_p17_18(trip, baseline_cfg=b, candidate_cfg=c)
    assert out.get("measurable") is True
    assert out.get("passed") is True


def test_probe_ac20_segment_order_on_fixture() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    out = probe_ac_p17_20(trip, baseline_cfg=base, candidate_cfg=base)
    assert out.get("measurable") is True
    assert out.get("passed") is True


def test_run_ac_probe_dispatch() -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_lse_enabled(_cfg_for_mode("p3_full"))
    out = run_ac_probe(trip, "AC-P17-20", baseline_cfg=base, candidate_cfg=base)
    assert "measurable" in out
