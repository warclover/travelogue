"""ALG-V3 OQ-02 · vision cohort opt-in (option C; no global auto default)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AppConfig, get_config
from travelogue.config.vision import (
    VisionConfig,
    vision_cohort_allows,
    vision_from_dict,
)
from travelogue.curation.algo_v3_summary import build_algo_v3_summary
from travelogue.curation.clustering import resolve_vision_mode


def test_oq02_defaults_keep_vision_off() -> None:
    cfg = AppConfig()
    assert cfg.vision.enabled == "false"
    assert cfg.vision.cohort_trip_ids == ()
    assert resolve_vision_mode([], cfg, trip_id="any-trip") is False


def test_oq02_loader_cohort_camel() -> None:
    vis = vision_from_dict(
        {"enabled": "false", "cohortTripIds": ["demo-a", " demo-b ", ""]}
    )
    assert vis.enabled == "false"
    assert vis.cohort_trip_ids == ("demo-a", "demo-b")


def test_oq02_cohort_allows_star_and_ids() -> None:
    assert vision_cohort_allows("t1", ()) is False
    assert vision_cohort_allows("t1", ("t1", "t2")) is True
    assert vision_cohort_allows("t9", ("t1", "t2")) is False
    assert vision_cohort_allows("", ("t1",)) is False
    assert vision_cohort_allows("anything", ("*",)) is True


def test_oq02_false_plus_cohort_force_on() -> None:
    base = get_config()
    cfg = replace(
        base,
        vision=replace(
            base.vision,
            enabled="false",
            cohort_trip_ids=("demo-hit",),
        ),
    )
    assert resolve_vision_mode([], cfg, trip_id="demo-miss") is False
    assert resolve_vision_mode([], cfg, trip_id="demo-hit") is True


def test_oq02_true_and_auto_unchanged() -> None:
    base = get_config()
    on = replace(base, vision=replace(base.vision, enabled="true", cohort_trip_ids=()))
    assert resolve_vision_mode([], on, trip_id=None) is True

    auto = replace(
        base,
        vision=replace(
            base.vision,
            enabled="auto",
            auto_min_photos=2,
            auto_min_eligible_ratio=0.5,
            cohort_trip_ids=(),
        ),
    )
    assets = [
        {"id": "a0", "type": "photo", "width": 100, "height": 100},
        {"id": "a1", "type": "photo", "width": 100, "height": 100},
    ]
    assert resolve_vision_mode(assets, auto, trip_id="x") is True
    assert resolve_vision_mode([assets[0]], auto, trip_id="x") is False


def test_oq02_summary_vision_effective_cohort() -> None:
    base = get_config()
    cfg = replace(
        base,
        vision=VisionConfig(enabled="false", cohort_trip_ids=("trip-c",)),
    )
    trip = {"id": "trip-c", "assets": [], "curation": {}}
    summary = build_algo_v3_summary(trip, cfg=cfg)
    assert summary["visionEffective"] == "cohort"

    miss = {"id": "other", "assets": [], "curation": {}}
    assert build_algo_v3_summary(miss, cfg=cfg)["visionEffective"] == "off"


def test_oq02_no_global_auto_in_defaults() -> None:
    """Product firewall: AppConfig must not ship vision.enabled=auto."""
    assert AppConfig().vision.enabled != "auto"
