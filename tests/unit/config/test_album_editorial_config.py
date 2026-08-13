"""AEL L0 config shell — PRD-ALBUM-EDITORIAL-LAB-V1 T-AEL-01/03."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config.album_editorial import (
    AlbumEditorialLabConfig,
    album_editorial_lab_from_dict,
    effective_ael,
)
from travelogue.config.app import AppConfig
from travelogue.config.errors import ConfigError
from travelogue.config.loader import load_config

pytestmark = pytest.mark.unit


def test_defaults_all_off() -> None:
    lab = AlbumEditorialLabConfig()
    assert lab.enabled is False
    assert lab.crop.enabled is False
    assert lab.roles.enabled is False
    assert lab.probes.enabled is False
    assert lab.crop.face_hard_gate is True
    assert lab.crop.max_solve_ms == 8000
    assert lab.probes.allowlist == ()


def test_unknown_key_fail_loud() -> None:
    with pytest.raises(ConfigError, match="album_editorial_lab unknown keys"):
        album_editorial_lab_from_dict({"enabled": False, "foo": 1})


def test_nested_unknown_key_fail_loud() -> None:
    with pytest.raises(ConfigError, match="album_editorial_lab.crop unknown keys"):
        album_editorial_lab_from_dict({"crop": {"enabled": False, "horizon": True}})


def test_face_hard_gate_false_rejected() -> None:
    with pytest.raises(ConfigError, match="face_hard_gate cannot be false"):
        album_editorial_lab_from_dict({"crop": {"face_hard_gate": False}})


def test_load_config_round_trip(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: ./trips\n"
        "album_editorial_lab:\n"
        "  enabled: true\n"
        "  crop:\n"
        "    enabled: false\n"
        "    group_face_min: 3\n"
        "    max_solve_ms: 8000\n"
        "  roles:\n"
        "    enabled: false\n"
        "  probes:\n"
        "    enabled: false\n"
        "    allowlist: []\n",
        encoding="utf-8",
    )
    app = load_config(cfg_path)
    assert app.album_editorial_lab.enabled is True
    assert app.album_editorial_lab.crop.enabled is False
    assert app.album_editorial_lab.crop.face_hard_gate is True


def test_effective_ael_four_combos() -> None:
    off = AppConfig()
    parent_on = AppConfig(
        album_editorial_lab=album_editorial_lab_from_dict({"enabled": True})
    )
    crop_on = AppConfig(
        album_editorial_lab=album_editorial_lab_from_dict(
            {"enabled": True, "crop": {"enabled": True}}
        )
    )

    xhs_off = effective_ael(parent_on, "xiaohongshu")
    assert xhs_off.enabled is False
    assert xhs_off.crop is False

    album_parent_off = effective_ael(off, "album_spread")
    assert album_parent_off.enabled is False
    assert album_parent_off.crop is False

    album_children_off = effective_ael(parent_on, "album_spread")
    assert album_children_off.enabled is True
    assert album_children_off.crop is False
    assert album_children_off.roles is False
    assert album_children_off.probes is False

    album_crop = effective_ael(crop_on, "album_spread")
    assert album_crop.enabled is True
    assert album_crop.crop is True
    assert album_crop.face_hard_gate is True

    none_cfg = effective_ael(None, "album_spread")
    assert none_cfg.enabled is False
