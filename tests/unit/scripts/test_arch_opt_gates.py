"""Switch DoD + LSE cross-import lint scripts."""

from __future__ import annotations

import json
import runpy
import sys
from io import StringIO

from tests._repo_root import repo_root

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


def test_check_switch_dod_report_before_calendar_dod() -> None:
    code, out = _run_script("scripts/check_switch_dod.py", "--as-of", "2026-07-08")
    assert code == 0
    report = json.loads(out)
    assert report["calendar_dod_all_met"] is False
    assert report["switches"][0]["days_until_dod"] == 28
    assert report["m_d1_ready"] is False


def test_lint_lse_cross_import_at_baseline() -> None:
    code, out = _run_script("scripts/lint_lse_cross_import.py")
    assert code == 0, out
    assert "109" in out
