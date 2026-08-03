"""LVP M1 · layout vibe → mosaic profile (AC-LVP-01/02/03/07/08)."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from travelogue.config import AppConfig, get_config, reset_config_cache
from travelogue.config.layout_vibe import (
    PROFILE_FIT_PHOTO_EXPERIMENTAL,
    PROFILE_MAGAZINE_DEFAULT,
    VIBE_FIT_PHOTO_EXPERIMENTAL,
    VIBE_MAGAZINE_DEFAULT,
    apply_layout_vibe_to_config,
    mosaic_profile_for_vibe,
    mosaic_switches,
    read_trip_layout_vibe,
    resolve_layout_vibe,
    set_trip_layout_vibe,
)
from travelogue.config.mosaic import (
    EqualGridContractConfig,
    SelectionOptimizationConfig,
    SlotAdaptationConfig,
)
from travelogue.layout_engine.capabilities import capability_flags_snapshot
from travelogue.paths import ROOT


@pytest.fixture(autouse=True)
def _restore_config_cache() -> None:
    yield
    reset_config_cache()


def _hostile_overlay_cfg() -> AppConfig:
    """Process overlay that disagrees with GA (MSA on, MTSO off)."""
    base = get_config()
    return replace(
        base,
        mosaic=replace(
            base.mosaic,
            selection_optimization=SelectionOptimizationConfig(enabled=False),
            equal_grid_contract=EqualGridContractConfig(enabled=True),
            slot_adaptation=SlotAdaptationConfig(enabled=True),
        ),
    )


def test_ac_lvp_01_magazine_default_equals_repo_ga() -> None:
    """AC-LVP-01 · magazine_default ≡ 仓库 GA（MTSO on · MEGC on · MSA off）."""
    profile = mosaic_profile_for_vibe(VIBE_MAGAZINE_DEFAULT)
    assert profile == PROFILE_MAGAZINE_DEFAULT
    assert profile.as_dict() == {
        "selection_optimization": True,
        "equal_grid_contract": True,
        "slot_adaptation": False,
    }

    example = ROOT / "config.yaml.example"
    data = yaml.safe_load(example.read_text(encoding="utf-8"))
    mosaic = data["mosaic"]
    assert mosaic["selection_optimization"]["enabled"] is True
    assert mosaic["equal_grid_contract"]["enabled"] is True
    assert mosaic["slot_adaptation"]["enabled"] is False

    cfg = apply_layout_vibe_to_config(
        {"studio": {"layoutVibe": VIBE_MAGAZINE_DEFAULT}},
        _hostile_overlay_cfg(),
    )
    assert mosaic_switches(cfg) == profile.as_dict()


def test_ac_lvp_02_fit_photo_only_enables_msa() -> None:
    """AC-LVP-02 · fit_photo_experimental 仅多开 slot_adaptation."""
    mag = mosaic_profile_for_vibe(VIBE_MAGAZINE_DEFAULT).as_dict()
    fit = mosaic_profile_for_vibe(VIBE_FIT_PHOTO_EXPERIMENTAL).as_dict()
    assert fit == {
        "selection_optimization": mag["selection_optimization"],
        "equal_grid_contract": mag["equal_grid_contract"],
        "slot_adaptation": True,
    }
    assert PROFILE_FIT_PHOTO_EXPERIMENTAL.slot_adaptation is True

    cfg = apply_layout_vibe_to_config(
        {"studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL}},
        _hostile_overlay_cfg(),
    )
    assert mosaic_switches(cfg) == fit


def test_ac_lvp_03_layout_vibe_persists_roundtrip(tmp_path: Path) -> None:
    """AC-LVP-03 · 写入 trip.studio.layoutVibe 后重载仍在."""
    trip: dict = {"tripId": "demo-lvp-persist", "studio": {}}
    set_trip_layout_vibe(trip, VIBE_FIT_PHOTO_EXPERIMENTAL)
    assert read_trip_layout_vibe(trip) == VIBE_FIT_PHOTO_EXPERIMENTAL

    path = tmp_path / "trip.json"
    path.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert read_trip_layout_vibe(reloaded) == VIBE_FIT_PHOTO_EXPERIMENTAL
    assert resolve_layout_vibe(reloaded) == VIBE_FIT_PHOTO_EXPERIMENTAL

    # Schema accepts studio.layoutVibe when present on a minimal property check
    from travelogue.paths import SCHEMA_PATH

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    studio_def = schema["$defs"]["tripStudio"]
    assert "layoutVibe" in studio_def["properties"]
    assert VIBE_FIT_PHOTO_EXPERIMENTAL in studio_def["properties"]["layoutVibe"]["enum"]


def test_ac_lvp_07_does_not_rewrite_ssg_look_or_lse_flags() -> None:
    """AC-LVP-07 · 不改写 SSG look / LSE capability flags."""
    base = get_config()
    look_before = copy.deepcopy(base.shot_grouping.look)
    se_before = copy.deepcopy(base.layout.strategy_engine)
    caps_before = capability_flags_snapshot(base)

    trip = {"studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL}}
    out = apply_layout_vibe_to_config(trip, base)

    assert out.shot_grouping.look == look_before
    assert out.layout.strategy_engine == se_before
    assert capability_flags_snapshot(out) == caps_before
    # mosaic MSA flipped, but look untouched
    assert mosaic_switches(out)["slot_adaptation"] is True
    assert out.shot_grouping is base.shot_grouping


def test_ac_lvp_08_clear_or_missing_equals_magazine_default() -> None:
    """AC-LVP-08 · 清除 vibe / 无字段 → ≡ magazine_default / GA."""
    hostile = _hostile_overlay_cfg()
    assert mosaic_switches(hostile)["slot_adaptation"] is True
    assert mosaic_switches(hostile)["selection_optimization"] is False

    missing = apply_layout_vibe_to_config({}, hostile)
    assert resolve_layout_vibe({}) == VIBE_MAGAZINE_DEFAULT
    assert mosaic_switches(missing) == PROFILE_MAGAZINE_DEFAULT.as_dict()

    trip = {"studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL}}
    set_trip_layout_vibe(trip, None)
    assert read_trip_layout_vibe(trip) is None
    cleared = apply_layout_vibe_to_config(trip, hostile)
    assert resolve_layout_vibe(trip) == VIBE_MAGAZINE_DEFAULT
    assert mosaic_switches(cleared) == PROFILE_MAGAZINE_DEFAULT.as_dict()

    # invalid id fail-open
    bad = apply_layout_vibe_to_config(
        {"studio": {"layoutVibe": "not_a_real_vibe"}},
        hostile,
    )
    assert resolve_layout_vibe({"studio": {"layoutVibe": "not_a_real_vibe"}}) == (
        VIBE_MAGAZINE_DEFAULT
    )
    assert mosaic_switches(bad) == PROFILE_MAGAZINE_DEFAULT.as_dict()


def test_blk_lvp_05_trip_vibe_beats_process_overlay() -> None:
    """BLK-LVP-05 · trip.studio.layoutVibe > 进程 overlay."""
    hostile = _hostile_overlay_cfg()
    # trip recommends magazine → must kill MSA-on overlay
    mag = apply_layout_vibe_to_config(
        {"studio": {"layoutVibe": VIBE_MAGAZINE_DEFAULT}},
        hostile,
    )
    assert mosaic_switches(mag) == PROFILE_MAGAZINE_DEFAULT.as_dict()

    # trip picks experimental → MSA on even if process had MSA off + MTSO off
    base = get_config()
    mtso_off = replace(
        base,
        mosaic=replace(
            base.mosaic,
            selection_optimization=SelectionOptimizationConfig(enabled=False),
            equal_grid_contract=EqualGridContractConfig(enabled=False),
            slot_adaptation=SlotAdaptationConfig(enabled=False),
        ),
    )
    fit = apply_layout_vibe_to_config(
        {"studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL}},
        mtso_off,
    )
    assert mosaic_switches(fit) == PROFILE_FIT_PHOTO_EXPERIMENTAL.as_dict()


def test_apply_layout_to_trip_uses_vibe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Layout entry applies vibe before planning (smoke · no full mosaic)."""
    from travelogue.services import layout as layout_mod

    seen: dict[str, object] = {}

    def _fake_build(*_a, **kwargs):
        cfg = kwargs.get("cfg")
        seen["switches"] = mosaic_switches(cfg) if cfg is not None else None
        return ([], None)

    monkeypatch.setattr(layout_mod, "build_chapters_from_plan", _fake_build)
    monkeypatch.setattr(layout_mod, "summarize_orientations", lambda *a, **k: type(
        "S", (), {"to_dict": lambda self: {}}
    )())
    monkeypatch.setattr(layout_mod, "format_layout_summary", lambda *a, **k: "")
    monkeypatch.setattr(layout_mod, "append_pipeline_run", lambda *a, **k: None)
    monkeypatch.setattr(layout_mod, "set_layout_status", lambda *a, **k: None)

    trip = {
        "exportLayout": "web",
        "layoutEngine": "legacy",
        "studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL},
        "assets": [{"id": f"a{i}"} for i in range(6)],
        "chapters": [
            {
                "items": [
                    {"type": "media-card", "assetId": f"a{i}"} for i in range(6)
                ]
            }
        ],
        "coverAssetId": "a0",
    }
    layout_mod.apply_layout_to_trip(trip, cfg=_hostile_overlay_cfg())
    assert seen["switches"] == PROFILE_FIT_PHOTO_EXPERIMENTAL.as_dict()
