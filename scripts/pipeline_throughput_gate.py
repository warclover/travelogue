"""Pipeline Throughput gate (M5).

Usage:
  python scripts/pipeline_throughput_gate.py --from-record --require-schema-only
  python scripts/pipeline_throughput_gate.py --from-record --strict
  python scripts/pipeline_throughput_gate.py --check-default-on
  python scripts/pipeline_throughput_gate.py --run-pytest
  python scripts/pipeline_throughput_gate.py --run-equivalence --from-record
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "docs" / "acceptance-records" / "pipeline-throughput-perf-eval.json"
DEFAULT_FLAG_SIGNOFF = (
    ROOT / "docs" / "acceptance-records" / "pipeline-throughput-default-flag-signoff.json"
)
EQ_SCRIPT = ROOT / "scripts" / "pipeline_throughput_equivalence_check.py"

REQUIRED_TOP_KEYS = (
    "schemaVersion",
    "benchmarkId",
    "baseline",
    "candidate",
    "kpi",
    "nr_pt",
    "ac_pt",
)
REQUIRED_AC_KEYS = tuple(f"AC-PT-{i:02d}" for i in range(1, 13))
REQUIRED_BASELINE_KEYS = (
    "parallel_ingest",
    "narrate_concurrency",
    "studio_e2e_100_ms",
    "ingest_time_100_ms",
)

PYTEST_UNIT = (
    "tests/unit/config/test_pipeline_throughput_config.py",
    "tests/unit/media/test_ingest_merge_mutator.py",
    "tests/unit/media/test_parallel_ingest_worker.py",
    "tests/unit/llm/test_llm_narrate_backoff.py",
    "tests/unit/llm/test_llm_narrate_lead_seen_order.py",
    "tests/unit/llm/test_llm_narrate_concurrency.py",
    "tests/unit/orchestrator/test_throughput_precheck.py",
    "tests/unit/orchestrator/test_studio_profile_pt.py",
    "tests/unit/vision/test_clip_resolve_prefer_source.py",
    "tests/unit/scripts/test_pipeline_throughput_gate.py",
    "tests/unit/scripts/test_lint_pt_default_flags.py",
)
PYTEST_INTEGRATION = (
    "tests/integration/test_pt_ingest_serial_parity.py",
    "tests/integration/test_pt_narrate_stub_equiv.py",
    "tests/integration/test_pt_ingest_algorithm_fixtures.py",
    "tests/integration/test_pt_ingest_progress_offer.py",
    "tests/integration/test_pt_persist_cas_parallel.py",
    "tests/integration/test_pt_ingest_geocode_main.py",
    "tests/integration/test_pt_ingest_resume_orphan.py",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_only(record: Path) -> tuple[dict[str, Any], int]:
    if not record.is_file():
        return {
            "overallPassed": False,
            "mode": "from-record-schema-only",
            "record": str(record),
            "error": "record not found",
        }, 2

    payload = _load_json(record)
    missing_top = [k for k in REQUIRED_TOP_KEYS if k not in payload]
    ac = payload.get("ac_pt") if isinstance(payload.get("ac_pt"), dict) else {}
    missing_ac = [k for k in REQUIRED_AC_KEYS if k not in ac]
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    missing_baseline = [k for k in REQUIRED_BASELINE_KEYS if k not in baseline]

    ok = not missing_top and not missing_ac and not missing_baseline
    summary = {
        "overallPassed": ok,
        "mode": "from-record-schema-only",
        "record": str(record),
        "missingTopKeys": missing_top,
        "missingAcKeys": missing_ac,
        "missingBaselineKeys": missing_baseline,
        "schemaVersion": payload.get("schemaVersion"),
    }
    return summary, (0 if ok else 1)


def _from_record(record: Path, *, strict: bool) -> tuple[dict[str, Any], int]:
    schema_summary, schema_rc = _schema_only(record)
    if schema_rc != 0:
        schema_summary["mode"] = "from-record"
        schema_summary["strict"] = strict
        return schema_summary, schema_rc

    payload = _load_json(record)
    ac = payload.get("ac_pt") or {}
    missing = [key for key in REQUIRED_AC_KEYS if ac.get(key) is None]
    failed = [key for key in REQUIRED_AC_KEYS if ac.get(key) is False]
    passed = [key for key in REQUIRED_AC_KEYS if ac.get(key) is True]
    nr = payload.get("nr_pt") or {}
    nr_passed = nr.get("passed")
    overall = len(failed) == 0 and len(missing) == 0 and nr_passed is not False
    summary = {
        "overallPassed": overall and (nr_passed is True or not strict or nr_passed is None),
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
        "nr_pt_passed": nr_passed,
    }
    if strict and (missing or nr_passed is None):
        summary["overallPassed"] = False
        return summary, 2
    return summary, (0 if summary["overallPassed"] else 1)


def _check_default_on(signoff: Path) -> tuple[dict[str, Any], int]:
    """Block product default acceleration unless signoff + lint agree."""
    # Import in-process (avoid Windows pytest subprocess handle issues).
    from scripts.lint_pt_default_flags import check_defaults

    lint_rc, lint_payload = check_defaults(signoff=signoff)

    if not signoff.is_file():
        return {
            "overallPassed": False,
            "mode": "check-default-on",
            "signoff": str(signoff),
            "error": "default-flag signoff record not found",
            "lint": lint_payload,
        }, 2

    payload = _load_json(signoff)
    status = str(payload.get("status") or "").strip().lower()
    lint_ok = lint_rc == 0 and bool(lint_payload.get("overallPassed", True))
    accelerated = bool(lint_payload.get("acceleratedDefaults"))
    approved = status == "approved"
    if accelerated:
        overall = approved and lint_ok
    else:
        overall = lint_ok
    summary = {
        "overallPassed": overall,
        "mode": "check-default-on",
        "signoff": str(signoff),
        "status": status,
        "flags": payload.get("flags"),
        "acceleratedDefaults": accelerated,
        "lint": lint_payload,
    }
    return summary, (0 if overall else 1)


def _run_pytest(*, integration: bool) -> tuple[dict[str, Any], int]:
    targets = list(PYTEST_UNIT)
    if integration:
        targets.extend(PYTEST_INTEGRATION)
    existing = [t for t in targets if (ROOT / t).is_file()]
    cmd = [sys.executable, "-m", "pytest", "-q", *existing]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    summary = {
        "overallPassed": proc.returncode == 0,
        "mode": "pytest-integration" if integration else "pytest-unit",
        "exitCode": proc.returncode,
        "targets": existing,
        "stdoutTail": (proc.stdout or "")[-800:],
        "stderrTail": (proc.stderr or "")[-400:],
    }
    return summary, proc.returncode


def _run_equivalence(record: Path, *, strict: bool) -> tuple[dict[str, Any], int]:
    cmd = [
        sys.executable,
        str(EQ_SCRIPT),
        "--from-record",
        "--record",
        str(record),
    ]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"rawStdout": proc.stdout, "stderr": proc.stderr}
    summary = {
        "overallPassed": proc.returncode == 0,
        "mode": "equivalence",
        "exitCode": proc.returncode,
        "result": payload,
    }
    return summary, proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline Throughput gate (M5)")
    parser.add_argument("--from-record", action="store_true")
    parser.add_argument("--require-schema-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--check-default-on", action="store_true")
    parser.add_argument("--run-pytest", action="store_true", help="run PT unit pytest targets")
    parser.add_argument(
        "--run-pytest-integration",
        action="store_true",
        help="run PT unit + integration pytest targets",
    )
    parser.add_argument(
        "--run-equivalence",
        action="store_true",
        help="run equivalence_check --from-record",
    )
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--signoff", type=Path, default=DEFAULT_FLAG_SIGNOFF)
    args = parser.parse_args()

    if not any(
        [
            args.from_record,
            args.check_default_on,
            args.run_pytest,
            args.run_pytest_integration,
            args.run_equivalence,
        ]
    ):
        parser.error(
            "specify --from-record / --check-default-on / --run-pytest / --run-equivalence"
        )

    exit_code = 0
    summaries: list[dict[str, Any]] = []

    if args.from_record:
        if args.require_schema_only:
            summary, rc = _schema_only(args.record)
        else:
            summary, rc = _from_record(args.record, strict=args.strict)
        summaries.append(summary)
        exit_code = max(exit_code, rc)

    if args.check_default_on:
        summary, rc = _check_default_on(args.signoff)
        summaries.append(summary)
        exit_code = max(exit_code, rc)

    if args.run_pytest or args.run_pytest_integration:
        summary, rc = _run_pytest(integration=bool(args.run_pytest_integration))
        summaries.append(summary)
        exit_code = max(exit_code, rc)

    if args.run_equivalence:
        summary, rc = _run_equivalence(args.record, strict=args.strict)
        summaries.append(summary)
        exit_code = max(exit_code, rc)

    print(json.dumps(summaries if len(summaries) > 1 else summaries[0], indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
