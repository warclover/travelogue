"""M-D1 · removed dual-path switch lint helpers."""

from __future__ import annotations

import runpy
import sys
import tomllib
from io import StringIO

import pytest

from tests._repo_root import repo_root
from travelogue.config.loader import load_config

ROOT = repo_root(__file__)
EXPECTED_IMPORTLINTER_IGNORES = [
    "travelogue.media.ingest -> travelogue.curation.aesthetic_score",
    "travelogue.media.ingest -> travelogue.curation.photo_cull",
    "travelogue.media.ingest -> travelogue.curation.algorithm_profile",
    "travelogue.vision.aesthetic_mllm -> travelogue.curation.aesthetic_blind_review",
    "travelogue.vision.aesthetic_mllm -> travelogue.curation.aesthetic_score",
    "travelogue.vision.aesthetic_mllm -> travelogue.curation.album_profile",
]


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
    from click.testing import CliRunner
    from importlinter.cli import lint_imports_command

    result = CliRunner().invoke(lint_imports_command)
    assert result.exit_code == 0, result.output
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contract = data["tool"]["importlinter"]["contracts"][0]
    assert contract["ignore_imports"] == EXPECTED_IMPORTLINTER_IGNORES


def test_lint_lse_cross_import_at_baseline() -> None:
    code, out = _run_script("scripts/lint_lse_cross_import.py")
    assert code == 0, out
    # Shim retirement made previously importlib-masked curation→LSE imports visible (7→18).
    assert "edges: 18" in out
    assert "ceiling 18" in out

def test_load_config_warns_on_removed_planner_impl(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: trips\nlayout:\n  planner_impl: curation\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="layout.planner_impl=curation was removed"):
        load_config(cfg_path)
