#!/usr/bin/env python3
"""P0 release-day aggregator: G6/G8 artifacts + gate signoff (REL-01/03)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    records = ROOT / "docs" / "acceptance-records"
    items: list[dict] = []

    g8 = _load_json(records / "phase13-g8-signoff.json") or {}
    g8_ok = g8.get("status") in ("signed", "automated_pass_pending_signoff") and (
        (g8.get("automatedPrereq") or {}).get("pass") is True
    )
    items.append(
        {
            "id": "REL-01",
            "name": "G8 走查",
            "pass": g8.get("status") == "signed",
            "partial": g8_ok and g8.get("status") != "signed",
            "detail": g8.get("status"),
        }
    )

    m72 = _load_json(records / "phase13-metrics-72h.json")
    m72_template = _load_json(records / "phase13-metrics-72h-gate-template.json")
    m72_pass = m72.get("pass") is True if m72 else False
    m72_clean = bool(m72 and (m72.get("metrics") or {}).get("rates", {}).get("route_total") == 0)
    items.append(
        {
            "id": "REL-02",
            "name": "G6 72h 指标",
            "pass": m72_pass,
            "partial": m72_pass or m72_clean or bool(m72_template and m72_template.get("pass")),
            "detail": "phase13-metrics-72h.json pass=%s route_total=%s"
            % (
                m72_pass,
                (m72 or {}).get("metrics", {}).get("rates", {}).get("route_total"),
            ),
            "note": "生产须真实流量窗口；dev 在 drill 后需 metrics_reset 再采 72h",
        }
    )

    gate = _load_json(records / "phase13-gate-signoff.json") or {}
    items.append(
        {
            "id": "REL-03",
            "name": "开发 Gate signoff",
            "pass": gate.get("go") is True,
            "detail": "go=%s" % gate.get("go"),
        }
    )

    staging = _load_json(records / "phase13-rollback-drill-staging.json")
    items.append(
        {
            "id": "REL-14",
            "name": "预发 rollback 归档",
            "pass": (staging or {}).get("allPass") is True,
            "detail": (staging or {}).get("summary"),
        }
    )

    release_ready = all(i["pass"] for i in items)
    return {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "releaseReady": release_ready,
        "items": items,
        "notes": [
            "开发 P0 已归档；一键重跑: python scripts/phase13_p0_release_finalize.py",
            "生产 REL-02: 真实流量 72h，勿用 reset；顺序: drill 前先采指标或 drill 后 reset 再采",
            "生产 REL-01: 若不接受 dev-automated 签字，走查后改 signoffMode 与 signoffs 真人字段",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 release day checklist")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase13-release-day-checklist.json",
    )
    parser.add_argument("--run-g8", action="store_true")
    args = parser.parse_args()

    if args.run_g8:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "phase13_g8_automation_check.py"), "--merge-signoff"],
            cwd=ROOT,
            check=False,
        )

    report = build_report()
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write} (releaseReady={report['releaseReady']})")
    else:
        print(text)
    return 0 if report["releaseReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
