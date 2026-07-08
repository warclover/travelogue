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


def test_lint_lse_cross_import_at_baseline() -> None:
    code, out = _run_script("scripts/lint_lse_cross_import.py")
    assert code == 0, out
    assert "27" in out


def test_load_config_warns_on_removed_planner_impl(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: trips\nlayout:\n  planner_impl: curation\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="layout.planner_impl=curation was removed"):
        load_config(cfg_path)
