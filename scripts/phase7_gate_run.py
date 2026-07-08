"""One-command Phase 7 gate runner (benchmark + NR collect + perf + equivalence + pytest).

Usage:
  python scripts/phase7_gate_run.py
  python scripts/phase7_gate_run.py --write --strict
  python scripts/phase7_gate_run.py --write --run-benchmark --photos 30 --repeats 2
  python scripts/phase7_gate_run.py --from-record --strict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PERF_SCRIPT = ROOT / "scripts" / "phase7_pipeline_perf.py"
EQ_SCRIPT = ROOT / "scripts" / "phase7_equivalence_check.py"
BENCH_SCRIPT = ROOT / "scripts" / "phase7_benchmark_run.py"
NR_SCRIPT = ROOT / "scripts" / "phase7_nr_collect.py"
ROLLBACK_SCRIPT = ROOT / "scripts" / "phase7_verify_rollback.py"
DEFAULT_RECORD = ROOT / "docs" / "acceptance-records" / "phase7-perf-eval.json"
DEFAULT_PHASE6_RECORD = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
REQUIRED_AC_KEYS = tuple(f"AC-P7-{i:02d}" for i in range(1, 13))
PYTEST_TARGETS = (
    "tests/test_phase7_equivalence.py",
    "tests/test_phase7_ingest_micro.py",
    "tests/test_phase7_parallel_embed.py",
    "tests/test_phase7_incremental_modes.py",
    "tests/test_phase7_cache_abi.py",
    "tests/test_phase7_fault_recovery.py",
    "tests/test_phase7_rollback_flags.py",
    "tests/unit/layout_engine/test_layout_golden.py",
)


def _append_opt(cmd: list[str], flag: str, value: Any) -> None:
    if value is None:
        return
    cmd.extend([flag, str(value)])


def _run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exitCode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _tail(text: str, limit: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _from_record_summary(record: Path, strict: bool) -> tuple[dict[str, Any], int]:
    if not record.is_file():
        summary = {
            "overallPassed": False,
            "mode": "from-record",
            "record": str(record),
            "error": "record not found",
        }
        return summary, 2

    payload = json.loads(record.read_text(encoding="utf-8"))
    ac = payload.get("ac_p7") or {}
    missing = [key for key in REQUIRED_AC_KEYS if ac.get(key) is None]
    failed = [key for key in REQUIRED_AC_KEYS if ac.get(key) is False]
    passed = [key for key in REQUIRED_AC_KEYS if ac.get(key) is True]
    overall = len(failed) == 0 and len(missing) == 0
    summary = {
        "overallPassed": overall,
        "mode": "from-record",
        "record": str(record),
        "strict": strict,
        "counts": {
            "passed": len(passed),
            "failed": len(failed),
            "missing": len(missing),
        },
        "failedKeys": failed,
        "missingKeys": missing,
    }
    if strict and missing:
        return summary, 2
    return summary, (0 if overall else 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 7 gate pipeline in one command")
    parser.add_argument("--write", action="store_true", help="persist results to record JSON")
    parser.add_argument("--strict", action="store_true", help="fail on missing AC fields")
    parser.add_argument("--from-record", action="store_true", help="evaluate gate directly from record JSON")
    parser.add_argument("--skip-proxy", action="store_true", help="skip 1k proxy call in perf script")
    parser.add_argument("--run-benchmark", action="store_true", help="run phase7_benchmark_run before checks")
    parser.add_argument("--run-nr-collect", action="store_true", help="run phase7_nr_collect before checks")
    parser.add_argument("--run-pytest", action="store_true", help="run Phase 7 pytest subset")
    parser.add_argument("--run-rollback-verify", action="store_true", help="run phase7_verify_rollback.py")
    parser.add_argument("--photos", type=int, default=30, help="benchmark album size")
    parser.add_argument("--repeats", type=int, default=2, help="benchmark repeats")
    parser.add_argument("--album-dir", type=Path, default=None, help="real photo folder for benchmark")
    parser.add_argument("--work-dir", type=Path, default=None, help="benchmark cache directory")
    parser.add_argument("--skip-pytest", action="store_true", help="skip pytest subset (faster real-album runs)")
    parser.add_argument("--update-report", action="store_true", help="refresh phase7-perf-baseline.md after benchmark")
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD, help="phase7 perf-eval record path")
    parser.add_argument("--phase6-record", type=Path, default=DEFAULT_PHASE6_RECORD, help="phase6 quality record")
    parser.add_argument("--device-tier", default=None)
    parser.add_argument("--device-note", default=None)
    parser.add_argument("--benchmark-id", default=None)
    parser.add_argument("--config-snapshot", default=None)
    parser.add_argument("--studio-e2e-ms", type=float, default=None)
    parser.add_argument("--studio-e2e-p95-ms", type=float, default=None)
    parser.add_argument("--ingest-ms", type=float, default=None)
    parser.add_argument("--clip-ms", type=float, default=None)
    parser.add_argument("--clip-p95-ms", type=float, default=None)
    parser.add_argument("--clip-incr-ms", type=float, default=None)
    parser.add_argument("--clip-incr-append-ms", type=float, default=None)
    parser.add_argument("--clip-incr-delete-ms", type=float, default=None)
    parser.add_argument("--clip-incr-replace-ms", type=float, default=None)
    parser.add_argument("--curate-beam-ms", type=float, default=None)
    parser.add_argument("--auto-batch-win-rate", type=float, default=None)
    parser.add_argument("--cache-rebuild-success-rate", type=float, default=None)
    parser.add_argument("--rollback-recovery-success", type=float, default=None)
    parser.add_argument("--nr-fixed-curate", type=float, default=None)
    parser.add_argument("--nr-fixed-cluster", type=float, default=None)
    parser.add_argument("--nr-real-curate", type=float, default=None)
    parser.add_argument("--nr-real-cluster", type=float, default=None)
    parser.add_argument("--subject-class-agreement", type=float, default=None)
    parser.add_argument("--cluster-noise-p7", type=float, default=None)
    parser.add_argument("--event-boundary-f1-p7", type=float, default=None)
    parser.add_argument("--layout-repeat-streak-p7", type=float, default=None)
    args = parser.parse_args()

    record = args.record.resolve()
    phase6_record = args.phase6_record.resolve()

    if args.from_record:
        summary, code = _from_record_summary(record, strict=args.strict)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return code

    if args.write:
        args.run_benchmark = True
        args.run_nr_collect = True
        if not args.skip_pytest:
            args.run_pytest = True
        args.run_rollback_verify = True
    if args.album_dir is not None:
        args.run_benchmark = True

    steps: list[dict[str, Any]] = []

    if args.run_pytest:
        pytest_cmd = [sys.executable, "-m", "pytest", *PYTEST_TARGETS, "-q"]
        pytest_res = _run(pytest_cmd)
        steps.append({"name": "pytest_phase7", "passed": pytest_res["exitCode"] == 0, "exitCode": pytest_res["exitCode"]})
        if pytest_res["exitCode"] != 0:
            print(json.dumps({"step": "pytest", "stderr": _tail(pytest_res["stderr"])}, indent=2))

    if args.run_benchmark:
        bench_cmd = [
            sys.executable,
            str(BENCH_SCRIPT),
            "--photos",
            str(args.photos),
            "--repeats",
            str(args.repeats),
            "--record",
            str(record),
        ]
        if args.write:
            bench_cmd.append("--write")
        if args.album_dir is not None:
            bench_cmd.extend(["--album-dir", str(args.album_dir.resolve())])
        if args.work_dir is not None:
            bench_cmd.extend(["--work-dir", str(args.work_dir.resolve())])
        if args.update_report:
            bench_cmd.append("--update-report")
        bench_res = _run(bench_cmd)
        steps.append({"name": "phase7_benchmark_run", "passed": bench_res["exitCode"] == 0, "exitCode": bench_res["exitCode"]})

    if args.run_nr_collect:
        nr_cmd = [sys.executable, str(NR_SCRIPT), "--record", str(record), "--phase6-record", str(phase6_record)]
        if args.write:
            nr_cmd.append("--write")
        if args.strict:
            nr_cmd.append("--strict")
        nr_res = _run(nr_cmd)
        steps.append({"name": "phase7_nr_collect", "passed": nr_res["exitCode"] == 0, "exitCode": nr_res["exitCode"]})

    if args.run_rollback_verify:
        rb_cmd = [sys.executable, str(ROLLBACK_SCRIPT), "--dry-run"]
        rb_res = _run(rb_cmd)
        steps.append({"name": "phase7_verify_rollback", "passed": rb_res["exitCode"] == 0, "exitCode": rb_res["exitCode"]})

    perf_cmd: list[str] = [sys.executable, str(PERF_SCRIPT), "--record", str(record), "--phase6-record", str(phase6_record)]
    if args.write:
        perf_cmd.append("--write")
    if args.strict:
        perf_cmd.append("--strict")
    if args.skip_proxy:
        perf_cmd.append("--skip-proxy")
    _append_opt(perf_cmd, "--device-tier", args.device_tier)
    _append_opt(perf_cmd, "--device-note", args.device_note)
    _append_opt(perf_cmd, "--benchmark-id", args.benchmark_id)
    _append_opt(perf_cmd, "--config-snapshot", args.config_snapshot)
    _append_opt(perf_cmd, "--studio-e2e-ms", args.studio_e2e_ms)
    _append_opt(perf_cmd, "--studio-e2e-p95-ms", args.studio_e2e_p95_ms)
    _append_opt(perf_cmd, "--ingest-ms", args.ingest_ms)
    _append_opt(perf_cmd, "--clip-ms", args.clip_ms)
    _append_opt(perf_cmd, "--clip-p95-ms", args.clip_p95_ms)
    _append_opt(perf_cmd, "--clip-incr-ms", args.clip_incr_ms)
    _append_opt(perf_cmd, "--clip-incr-append-ms", args.clip_incr_append_ms)
    _append_opt(perf_cmd, "--clip-incr-delete-ms", args.clip_incr_delete_ms)
    _append_opt(perf_cmd, "--clip-incr-replace-ms", args.clip_incr_replace_ms)
    _append_opt(perf_cmd, "--curate-beam-ms", args.curate_beam_ms)
    _append_opt(perf_cmd, "--auto-batch-win-rate", args.auto_batch_win_rate)
    _append_opt(perf_cmd, "--cache-rebuild-success-rate", args.cache_rebuild_success_rate)
    _append_opt(perf_cmd, "--rollback-recovery-success", args.rollback_recovery_success)

    eq_cmd: list[str] = [sys.executable, str(EQ_SCRIPT), "--record", str(record), "--phase6-record", str(phase6_record)]
    if args.write:
        eq_cmd.append("--write")
    if args.strict:
        eq_cmd.append("--strict")
    _append_opt(eq_cmd, "--nr-fixed-curate", args.nr_fixed_curate)
    _append_opt(eq_cmd, "--nr-fixed-cluster", args.nr_fixed_cluster)
    _append_opt(eq_cmd, "--nr-real-curate", args.nr_real_curate)
    _append_opt(eq_cmd, "--nr-real-cluster", args.nr_real_cluster)
    _append_opt(eq_cmd, "--subject-class-agreement", args.subject_class_agreement)
    _append_opt(eq_cmd, "--cluster-noise-p7", args.cluster_noise_p7)
    _append_opt(eq_cmd, "--event-boundary-f1-p7", args.event_boundary_f1_p7)
    _append_opt(eq_cmd, "--layout-repeat-streak-p7", args.layout_repeat_streak_p7)

    perf = _run(perf_cmd)
    eq = _run(eq_cmd)
    steps.extend(
        [
            {"name": "phase7_pipeline_perf", "passed": perf["exitCode"] == 0, "exitCode": perf["exitCode"]},
            {"name": "phase7_equivalence_check", "passed": eq["exitCode"] == 0, "exitCode": eq["exitCode"]},
        ]
    )

    critical = {
        "pytest_phase7",
        "phase7_benchmark_run",
        "phase7_nr_collect",
        "phase7_equivalence_check",
    }
    overall_ok = all(step["passed"] for step in steps if step["name"] in critical)
    summary = {
        "overallPassed": overall_ok,
        "steps": steps,
        "record": str(record),
        "perfStdoutTail": _tail(perf["stdout"]),
        "equivalenceStdoutTail": _tail(eq["stdout"]),
        "errors": {
            "perfStderrTail": _tail(perf["stderr"]),
            "equivalenceStderrTail": _tail(eq["stderr"]),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if overall_ok:
        return 0
    fatal = any(step["exitCode"] >= 2 for step in steps)
    return 2 if fatal else 1


if __name__ == "__main__":
    raise SystemExit(main())
