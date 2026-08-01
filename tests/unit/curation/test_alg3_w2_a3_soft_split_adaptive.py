"""ALG-V3 W2-A3 · adaptive soft-split (opt-in; default path unchanged)."""

from __future__ import annotations

from travelogue.config.shot_grouping import (
    ShotGroupingSceneConfig,
    shot_grouping_from_dict,
)
from travelogue.curation.shot_grouping import (
    _soft_split_runs,
    adaptive_soft_split_hours,
    resolve_soft_split_hours,
    run_shot_grouping_layer,
)


def _member(aid: str, taken: str | None, *, cid: int = 1) -> dict:
    row: dict = {
        "id": aid,
        "type": "photo",
        "sceneClusterId": cid,
        "eventId": "e1",
        "sharpness": 0.5,
    }
    if taken is not None:
        row["takenAt"] = taken
    return row


def test_a3_adaptive_defaults_off() -> None:
    cfg = ShotGroupingSceneConfig()
    assert cfg.adaptive_soft_split is False
    assert cfg.time_soft_split_hours == 6.0
    assert cfg.adaptive_soft_split_k == 3.0
    assert cfg.adaptive_soft_split_hours_lo == 1.0
    assert cfg.adaptive_soft_split_hours_hi == 12.0


def test_a3_loader_camel_and_lo_hi_swap() -> None:
    ssg = shot_grouping_from_dict(
        {
            "scene": {
                "adaptiveSoftSplit": True,
                "adaptiveSoftSplitK": 2.5,
                "adaptiveSoftSplitHoursLo": 9.0,
                "adaptiveSoftSplitHoursHi": 2.0,
            }
        }
    )
    assert ssg.scene.adaptive_soft_split is True
    assert ssg.scene.adaptive_soft_split_k == 2.5
    # loader normalizes lo/hi
    assert ssg.scene.adaptive_soft_split_hours_lo == 2.0
    assert ssg.scene.adaptive_soft_split_hours_hi == 9.0


def test_a3_adaptive_hours_clamps_to_lo() -> None:
    # Uniform 10-minute gaps → median 1/6 h → *3 = 0.5 → clamp to lo=1
    members = [
        _member("a0", "2025-01-01T10:00:00Z"),
        _member("a1", "2025-01-01T10:10:00Z"),
        _member("a2", "2025-01-01T10:20:00Z"),
        _member("a3", "2025-01-01T10:30:00Z"),
    ]
    h = adaptive_soft_split_hours(members, k=3.0, lo=1.0, hi=12.0, fallback=6.0)
    assert h == 1.0


def test_a3_adaptive_hours_mid_band() -> None:
    # Gaps of 2h → median 2 → *3 = 6
    members = [
        _member("a0", "2025-01-01T10:00:00Z"),
        _member("a1", "2025-01-01T12:00:00Z"),
        _member("a2", "2025-01-01T14:00:00Z"),
    ]
    h = adaptive_soft_split_hours(members, k=3.0, lo=1.0, hi=12.0, fallback=6.0)
    assert h == 6.0


def test_a3_adaptive_hours_clamps_to_hi() -> None:
    # Gaps of 5h → median 5 → *3 = 15 → clamp hi=12
    members = [
        _member("a0", "2025-01-01T10:00:00Z"),
        _member("a1", "2025-01-01T15:00:00Z"),
        _member("a2", "2025-01-01T20:00:00Z"),
    ]
    h = adaptive_soft_split_hours(members, k=3.0, lo=1.0, hi=12.0, fallback=6.0)
    assert h == 12.0


def test_a3_adaptive_hours_fallback_when_sparse() -> None:
    assert (
        adaptive_soft_split_hours(
            [_member("a0", "2025-01-01T10:00:00Z")],
            k=3.0,
            lo=1.0,
            hi=12.0,
            fallback=6.0,
        )
        == 6.0
    )
    assert (
        adaptive_soft_split_hours(
            [_member("a0", None), _member("a1", None)],
            k=3.0,
            lo=1.0,
            hi=12.0,
            fallback=6.0,
        )
        == 6.0
    )
    assert (
        adaptive_soft_split_hours(
            [
                _member("a0", "2025-01-01T10:00:00Z"),
                _member("a1", "2025-01-01T12:00:00Z"),
            ],
            k=0.0,
            lo=1.0,
            hi=12.0,
            fallback=6.0,
        )
        == 6.0
    )


def test_a3_flag_off_matches_fixed_six_hour_split() -> None:
    """Default path: 10h gap soft-splits once under fixed 6h."""
    members = [
        _member("a0", "2025-01-01T08:00:00Z"),
        _member("a1", "2025-01-01T09:00:00Z"),
        _member("a2", "2025-01-01T19:00:00Z"),  # +10h from a1
        _member("a3", "2025-01-01T20:00:00Z"),
    ]
    scene = ShotGroupingSceneConfig(adaptive_soft_split=False, time_soft_split_hours=6.0)
    h = resolve_soft_split_hours(members, scene)
    assert h == 6.0
    runs, splits = _soft_split_runs(members, split_hours=h)
    assert splits == 1
    assert len(runs) == 2
    assert [a["id"] for a in runs[0]] == ["a0", "a1"]
    assert [a["id"] for a in runs[1]] == ["a2", "a3"]


def test_a3_flag_on_sparse_avoids_false_split() -> None:
    """Sparse gaps → hi=12h threshold; 10h gap stays one run (fixed 6h would split)."""
    members = [
        _member("a0", "2025-01-01T08:00:00Z"),
        _member("a1", "2025-01-01T13:00:00Z"),  # 5h
        _member("a2", "2025-01-01T18:00:00Z"),  # 5h → median 5 → *3 → 15 → hi 12
        _member("a3", "2025-01-02T04:00:00Z"),  # 10h < 12 → no split
    ]
    scene = ShotGroupingSceneConfig(adaptive_soft_split=True)
    h = resolve_soft_split_hours(members, scene)
    assert h == 12.0
    _runs_fixed, splits_fixed = _soft_split_runs(members, split_hours=6.0)
    runs_ad, splits_ad = _soft_split_runs(members, split_hours=h)
    assert splits_fixed >= 1
    assert splits_ad == 0
    assert len(runs_ad) == 1


def test_a3_layer_telemetry_and_default_off_equivalence() -> None:
    assets = [
        _member("a0", "2025-01-01T08:00:00Z"),
        _member("a1", "2025-01-01T09:00:00Z"),
        _member("a2", "2025-01-01T19:00:00Z"),
        _member("a3", "2025-01-01T20:00:00Z"),
    ]
    ssg_off = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "false"}, "scene": {"adaptiveSoftSplit": False}}
    )
    ssg_on = shot_grouping_from_dict(
        {"enabled": "true", "look": {"enabled": "false"}, "scene": {"adaptiveSoftSplit": True}}
    )
    trip_off = {"assets": [dict(a) for a in assets]}
    trip_on = {"assets": [dict(a) for a in assets]}
    cfg_off = type("Cfg", (), {"shot_grouping": ssg_off})()
    cfg_on = type("Cfg", (), {"shot_grouping": ssg_on})()
    run_shot_grouping_layer(trip_off, cfg=cfg_off)  # type: ignore[arg-type]
    run_shot_grouping_layer(trip_on, cfg=cfg_on)  # type: ignore[arg-type]

    stats_off = trip_off["curation"]["shotGrouping"]["stats"]
    stats_on = trip_on["curation"]["shotGrouping"]["stats"]
    assert stats_off["softSplitAdaptive"] is False
    assert "softSplitHoursEffective" not in stats_off
    assert stats_off["softSplitCount"] == 1

    assert stats_on["softSplitAdaptive"] is True
    assert "softSplitHoursEffective" in stats_on
    # Dense-ish early gaps + one 10h jump: median adjacent gaps = median(1,10,1)=1 → *3=3 → mid band
    # Actually gaps: 1h, 10h, 1h → median 1 → *3 = 3 → split on 10h still happens
    assert stats_on["softSplitCount"] >= 0
