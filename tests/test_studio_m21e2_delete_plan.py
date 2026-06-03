"""Tests for scripts/studio_m21e2_delete_plan.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "studio_m21e2_delete_plan.py"
_spec = importlib.util.spec_from_file_location("studio_m21e2_delete_plan", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_m21e2_delete_plan"] = mod
_spec.loader.exec_module(mod)


def test_build_delete_commands_count() -> None:
    cmds = mod.build_delete_commands()
    assert len(cmds) == 2
    assert cmds[0].startswith("git rm ")


def test_verify_files_exist_current_repo() -> None:
    # 当前阶段仍保留 v3 文件，验证应全存在。
    missing = mod.verify_files_exist()
    assert missing == []


def test_main_dry_run_success() -> None:
    assert mod.main([]) == 0
