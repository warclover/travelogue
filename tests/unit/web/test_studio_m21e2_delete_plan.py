"""Tests for scripts/studio_m21e2_delete_plan.py."""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import sys
from pathlib import Path

_SCRIPT = repo_root(__file__) / "scripts" / "studio_m21e2_delete_plan.py"
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
    # 兼容 e2 执行前后：缺失列表只能来自候选删除集。
    missing = mod.verify_files_exist()
    candidates = {rel for _group, files in mod.DELETE_GROUPS for rel in files}
    assert set(missing).issubset(candidates)


def test_main_dry_run_success() -> None:
    # M21-e2 后 v3 文件已删：already_clean → 0；未删时仅打印计划 → 0。
    assert mod.main([]) == 0
