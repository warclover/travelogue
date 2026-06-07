"""LSE registry and schema validation."""

from __future__ import annotations

from pathlib import Path

from travelogue.layout_engine.cli import main as lse_cli_main
from travelogue.layout_engine.registry import get_strategy_pack, list_active_strategies
from travelogue.layout_engine.validator import validate_strategy_file

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "travelogue/layout_engine/strategies/default.yaml"


def test_default_strategy_pack_validates() -> None:
    report = validate_strategy_file(DEFAULT_PACK)
    assert report.ok, [f"{i.path}: {i.message}" for i in report.issues]


def test_get_default_strategy_pack() -> None:
    pack = get_strategy_pack("lse-default-2026-06")
    assert pack.id == "lse-default-2026-06"
    assert pack.version == 1
    assert pack.weights_hash("default").startswith("sha256:")


def test_list_active_strategies_includes_default() -> None:
    packs = list_active_strategies()
    ids = {p.id for p in packs}
    assert "lse-default-2026-06" in ids


def test_lse_cli_validate_exit_zero() -> None:
    assert lse_cli_main(["validate", str(DEFAULT_PACK)]) == 0
