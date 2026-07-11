"""M0/M5 gate / benchmark CLI smoke (in-process; avoids Win subprocess handle issues)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pipeline_throughput_benchmark import main as bench_main
from scripts.pipeline_throughput_gate import _schema_only
from scripts.pipeline_throughput_gate import main as gate_main


def test_gate_require_schema_only(capsys, monkeypatch) -> None:
    record = ROOT / "docs" / "acceptance-records" / "pipeline-throughput-perf-eval.json"
    summary, rc = _schema_only(record)
    assert rc == 0
    assert summary["overallPassed"] is True
    assert summary["mode"] == "from-record-schema-only"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline_throughput_gate.py",
            "--from-record",
            "--require-schema-only",
            "--record",
            str(record),
        ],
    )
    assert gate_main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["overallPassed"] is True


def test_gate_check_default_on_passes_while_defaults_off(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["pipeline_throughput_gate.py", "--check-default-on"],
    )
    assert gate_main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["overallPassed"] is True
    assert out["acceleratedDefaults"] is False


def test_benchmark_register_baseline_dry_run(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline_throughput_benchmark.py",
            "--register-baseline",
            "--dry-run",
            "--photos",
            "100,250",
            "--tier",
            "S2",
        ],
    )
    assert bench_main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "register-baseline"
    assert payload["dryRun"] is True


def test_benchmark_run_microbench(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline_throughput_benchmark.py",
            "--run-microbench",
            "--photos",
            "4",
            "--repeats",
            "1",
            "--compare-parallel",
        ],
    )
    assert bench_main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "run-microbench"
    assert payload["serial"]["medianMs"] > 0
    assert "parallel" in payload
    assert payload["parallel"]["medianMs"] > 0
    assert "dropVsSerialIngest" in payload["parallel"]
