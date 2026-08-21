"""M-D1 · removed dual-path switch lint helpers."""

from __future__ import annotations

import json
import runpy
import sys
import tomllib
from io import StringIO

import pytest

from tests._repo_root import repo_root
from travelogue.config.loader import load_config

ROOT = repo_root(__file__)
VALID_LSE_TRACKING_ISSUE = "docs/ARCH-OPT-P2-BACKLOG.md#P2-C"
EXPECTED_IMPORTLINTER_IGNORES = [
    "travelogue.media.ingest -> travelogue.curation.aesthetic_score",
    "travelogue.media.ingest -> travelogue.curation.photo_cull",
    "travelogue.media.ingest -> travelogue.curation.algorithm_profile",
    "travelogue.media.ingest -> travelogue.curation.aesthetic_warm",
    "travelogue.media.ingest_worker -> travelogue.curation.aesthetic_score",
    "travelogue.media.ingest_parallel -> travelogue.curation.aesthetic_score",
    "travelogue.cover_engine.title_art.engine -> travelogue.render.context",
    "travelogue.cover_engine.title_art.engine -> travelogue.render.cover_opening",
]


def _run_script(rel: str, *argv: str) -> tuple[int, str]:
    buf = StringIO()
    old_argv = sys.argv
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.argv = [rel, *argv]
        sys.stdout = buf
        sys.stderr = buf
        runpy.run_path(str(ROOT / rel), run_name="__main__")
        code = 0
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
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
    baseline = json.loads(
        (ROOT / "docs/acceptance-records/lse-cross-import-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    expected = int(baseline.get("totalCrossEdges", baseline.get("total_edges", 0)))
    code, out = _run_script("scripts/lint_lse_cross_import.py")
    assert code == 0, out
    assert f"edges: {expected}" in out
    assert f"ceiling {expected}" in out


def test_lint_lse_cross_import_reduction_refreshes_growth_log(tmp_path) -> None:
    baseline_path = tmp_path / "lse-cross-import-baseline.json"
    growth_log_path = tmp_path / "lse-cross-import-growth-log.json"
    code, out = _run_script(
        "scripts/lint_lse_cross_import.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
        "--update-baseline",
    )
    assert code == 0, out
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    growth = json.loads(growth_log_path.read_text(encoding="utf-8"))
    assert baseline["totalCrossEdges"] == 10
    assert growth["currentBaseline"]["totalCrossEdges"] == 10
    assert growth["currentBaseline"]["edgeSignatures"]
    assert growth["entries"] == []


def test_lint_lse_cross_import_growth_requires_metadata(tmp_path) -> None:
    baseline_path = tmp_path / "lse-cross-import-baseline.json"
    growth_log_path = tmp_path / "lse-cross-import-growth-log.json"
    baseline = json.loads(
        (ROOT / "docs/acceptance-records/lse-cross-import-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    baseline["totalCrossEdges"] = 8
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    code, out = _run_script(
        "scripts/lint_lse_cross_import.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
        "--update-baseline",
    )
    assert code == 1
    assert "growth without --allow-growth" in out

    code, out = _run_script(
        "scripts/lint_lse_cross_import.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
        "--update-baseline",
        "--allow-growth",
        "--tracking-issue",
        VALID_LSE_TRACKING_ISSUE,
        "--due-date",
        "2099-12-31",
    )
    assert code == 0, out
    growth = json.loads(growth_log_path.read_text(encoding="utf-8"))
    assert growth["currentBaseline"]["totalCrossEdges"] == 10
    assert len(growth["entries"]) == 1
    entry = growth["entries"][0]
    assert entry["old_ceiling"] == 8
    assert entry["new_ceiling"] == 10
    assert entry["tracking_issue"] == VALID_LSE_TRACKING_ISSUE
    assert entry["due_date"] == "2099-12-31"


def test_lint_ratchet_growth_log_detects_tampered_baseline(tmp_path) -> None:
    baseline_path = tmp_path / "lse-cross-import-baseline.json"
    growth_log_path = tmp_path / "lse-cross-import-growth-log.json"
    code, out = _run_script(
        "scripts/lint_lse_cross_import.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
        "--update-baseline",
    )
    assert code == 0, out

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["totalCrossEdges"] += 1
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        "scripts/lint_ratchet_growth_log.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
    )
    assert code == 1
    assert "committed baseline diverges from computed edges" in out


def test_lint_ratchet_growth_log_rejects_expired_entry(tmp_path) -> None:
    baseline_path = tmp_path / "lse-cross-import-baseline.json"
    growth_log_path = tmp_path / "lse-cross-import-growth-log.json"
    baseline = json.loads(
        (ROOT / "docs/acceptance-records/lse-cross-import-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    baseline["totalCrossEdges"] = 8
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        "scripts/lint_lse_cross_import.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
        "--update-baseline",
        "--allow-growth",
        "--tracking-issue",
        VALID_LSE_TRACKING_ISSUE,
        "--due-date",
        "2099-12-31",
    )
    assert code == 0, out

    growth = json.loads(growth_log_path.read_text(encoding="utf-8"))
    growth["entries"][0]["due_date"] = "2000-01-01"
    growth_log_path.write_text(
        json.dumps(growth, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        "scripts/lint_ratchet_growth_log.py",
        "--baseline-file",
        str(baseline_path),
        "--growth-log-file",
        str(growth_log_path),
    )
    assert code == 1
    assert "expired on 2000-01-01" in out


def test_load_config_warns_on_removed_planner_impl(tmp_path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: trips\nlayout:\n  planner_impl: curation\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="layout.planner_impl=curation was removed"):
        load_config(cfg_path)
