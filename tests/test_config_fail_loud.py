"""M-A2 config fail-loud acceptance tests (AC-ARC-03/04)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from travelogue.config.errors import ConfigError
from travelogue.config.loader import load_config
from travelogue.config.yaml_loader import load_yaml_mapping

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "config.yaml.example"


def test_duplicate_top_level_key_raises_config_error_with_line(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "trips_dir: ./trips\n"
        "trips_dir: ./other\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match=r"duplicate config key 'trips_dir' at line 2"):
        load_config(cfg)


def test_unknown_key_emits_single_aggregated_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "trips_dir: ./trips\n"
        "curate:\n"
        "  fooo: 1\n",
        encoding="utf-8",
    )
    caplog.set_level(logging.WARNING)
    load_config(cfg)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert warnings[0].getMessage() == "config: unknown keys: curate.fooo"


def test_strict_unknown_key_raises_config_error(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "strict: true\n"
        "trips_dir: ./trips\n"
        "curate:\n"
        "  fooo: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="config: unknown keys: curate.fooo"):
        load_config(cfg)


def test_config_yaml_example_has_zero_unknown_key_warnings(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    caplog.set_level(logging.WARNING)
    load_config(cfg)
    unknown_warnings = [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING and r.getMessage().startswith("config: unknown keys:")
    ]
    assert unknown_warnings == []


def test_load_yaml_mapping_duplicate_nested_key_includes_line() -> None:
    with pytest.raises(ConfigError, match=r"duplicate config key 'enabled' at line 3"):
        load_yaml_mapping("clustering:\n  enabled: true\n  enabled: false\n")
