"""M-D1 · removed dual-path switch lint helpers."""

from __future__ import annotations

import json
import runpy
import sys
from io import StringIO

import pytest

from tests._repo_root import repo_root
from travelogue.config.loader import load_config

ROOT = repo_root(__file__)


def _run_script(rel: str, *argv: str) -> tuple[int, str]:
    buf = StringIO()
    old_argv = sys.argv
    old_stdout = sys.stdout
    try:
        sys.argv = [rel, *argv]
        sys.stdout = buf
        runpy.run_path(str(ROOT / rel), run_name="__main__")
        code = 0
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
    return code, buf.getvalue()


def test_lint_imports_no_exemptions() -> None:
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "lint-imports"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    ignore_block = (ROOT / "pyproject.toml").read_text(encoding="utf-8").split("ignore_imports = ", 1)[-1]
    assert ignore_block.startswith("[]"), "ignore_imports must be empty"


def test_lint_lse_cross_import_at_baseline() -> None:
    code, out = _run_script("scripts/lint_lse_cross_import.py")
    assert code == 0, out
    assert "7" in out


def test_load_config_warns_on_removed_planner_impl(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: trips\nlayout:\n  planner_impl: curation\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="layout.planner_impl=curation was removed"):
        load_config(cfg_path)
