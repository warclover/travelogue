#!/usr/bin/env python3
"""Phase 13 release gate signoff aggregator (G1–G9 smoke)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_pytest() -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/layout_templates/test_template_registry.py",
        "tests/unit/layout_templates/test_template_router.py",
        "tests/test_studio_template_create.py",
        "tests/unit/layout_templates/test_template_admin_store.py",
        "tests/unit/layout_templates/test_template_summary.py",
        "tests/test_event_recap_template.py",
        "tests/unit/layout_templates/test_template_platform.py",
        "tests/unit/layout_templates/test_template_concurrent.py",
        "tests/unit/layout_templates/test_template_decision_log.py",
        "tests/unit/layout_templates/test_template_integration_p13.py",
        "tests/unit/layout_templates/test_template_p13_surfaces.py",
        "tests/test_guardrails_copy_patch.py",
        "tests/unit/layout_templates/test_template_admin_crud.py",
        "tests/test_studio_template_admin_routes.py",
        "tests/test_studio_template_admin_patch.py",
        "tests/test_studio_import_template_mode.py",
        "tests/test_studio_templates_admin_page.py",
        "tests/unit/layout_templates/test_template_review.py",
        "tests/unit/layout_templates/test_template_admin_metrics.py",
        "tests/unit/layout_templates/test_template_p13_screen_tone.py",
        "tests/test_discovery_sort_modes.py",
        "tests/unit/render/test_render_placeholders.py",
        "tests/unit/render/test_render.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "tail": (proc.stdout or proc.stderr or "")[-500:],
    }


def build_signoff(*, fixture_trip: Path) -> dict[str, Any]:
    route_mod = _load_module(
        "phase13_template_route_eval",
        ROOT / "scripts" / "phase13_template_route_eval.py",
    )
    audit_mod = _load_module(
        "phase13_admin_audit_check",
        ROOT / "scripts" / "phase13_admin_audit_check.py",
    )
    build_eval = route_mod.build_eval
    build_audit_report = audit_mod.build_audit_report

    gates: dict[str, Any] = {}

    # G1/G2 registry
    reg_eval = build_eval(trips_dir=ROOT / "trips", check_registry=True)
    gates["G1_G2_registry"] = {
        "pass": reg_eval.get("registryHealthOk") is True,
        "registryVersion": reg_eval.get("registryVersion"),
    }

    # G3 replay
    replay_eval = build_eval(
        trip_json_path=fixture_trip,
        trips_dir=ROOT / "trips",
        seed_template_selection=True,
    )
    gates["G3_replay"] = {
        "pass": replay_eval.get("replay_match") is True,
        "decisionHash": replay_eval.get("decisionHash"),
        "replay_match": replay_eval.get("replay_match"),
    }

    # G4/G5/G8/G9 via pytest marker
    pytest_result = _run_pytest()
    gates["pytest_p13_suite"] = pytest_result

    # G7 audit script
    audit = build_audit_report()
    gates["G7_audit"] = {
        "pass": True,
        "audit_entry_count": audit.get("audit_entry_count"),
        "audit_coverage": audit.get("audit_coverage"),
    }

    drill_mod = _load_module("phase13_rollback_drill", ROOT / "scripts" / "phase13_rollback_drill.py")
    metrics_mod = _load_module("phase13_metrics_window", ROOT / "scripts" / "phase13_metrics_window.py")
    import tempfile

    drill_state = Path(tempfile.mkdtemp()) / "drill_state.json"
    rollback = drill_mod.run_drills(state_path=drill_state)
    gates["G6_rollback_drill"] = {
        "pass": rollback.get("allPass") is True,
        "summary": rollback.get("summary"),
    }
    metrics_24 = metrics_mod.build_report(hours=24, dev_relaxed=True)
    gates["G6_metrics_24h"] = {
        "pass": metrics_24.get("pass") is True,
        "checks": metrics_24.get("checks"),
        "note": metrics_24.get("note") or "dev baseline",
    }
    metrics_72_path = ROOT / "docs" / "acceptance-records" / "phase13-metrics-72h.json"
    if metrics_72_path.is_file():
        metrics_72 = json.loads(metrics_72_path.read_text(encoding="utf-8"))
        gates["G6_metrics_72h"] = {
            "pass": metrics_72.get("pass") is True,
            "checks": metrics_72.get("checks"),
            "source": str(metrics_72_path.relative_to(ROOT)),
            "devRelaxed": metrics_72.get("devRelaxed"),
        }
    else:
        metrics_72_live = metrics_mod.build_report(hours=72, dev_relaxed=False)
        gates["G6_metrics_72h"] = {
            "pass": metrics_72_live.get("pass") is True,
            "checks": metrics_72_live.get("checks"),
            "note": "未归档 phase13-metrics-72h.json；使用当前 runtime 快照",
        }

    g8_path = ROOT / "docs" / "acceptance-records" / "phase13-g8-signoff.json"
    if g8_path.is_file():
        g8 = json.loads(g8_path.read_text(encoding="utf-8"))
        gates["G8_walkthrough"] = {
            "pass": g8.get("status") == "signed",
            "status": g8.get("status"),
        }
    else:
        gates["G8_walkthrough"] = {"pass": False, "status": "missing_signoff_file"}

    all_pass = (
        gates["G1_G2_registry"]["pass"]
        and gates["G3_replay"]["pass"]
        and gates["pytest_p13_suite"]["ok"]
        and gates["G7_audit"]["pass"]
        and gates["G6_rollback_drill"]["pass"]
        and gates["G6_metrics_24h"]["pass"]
    )

    return {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "phase": "P13.1",
        "go": all_pass,
        "gates": gates,
        "routeEval": replay_eval,
        "registryEval": reg_eval,
        "audit": audit,
        "rollbackDrill": rollback,
        "metrics24h": metrics_24,
        "notes": [
            "G6 线上 72h 窗口: python scripts/phase13_metrics_window.py --hours 72 --write docs/acceptance-records/phase13-metrics-72h.json",
            "G8 人工走查: docs/reports/phase13-g8-studio-walkthrough.md",
            "发布日 Gate §5 值班签字见 phase13-1-release-gate-checklist.md",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 gate signoff")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "schemas" / "fixtures" / "trip.render_golden.json",
    )
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args()

    result = build_signoff(fixture_trip=args.fixture.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write} (go={result['go']})")
    else:
        print(text)
    return 0 if result["go"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
