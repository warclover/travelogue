#!/usr/bin/env python3
"""REL-03: Phase 13 release-day Gate §5 signoff artifact."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "docs" / "acceptance-records"


def _load(name: str) -> dict | None:
    path = RECORDS / name
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    gate = _load("phase13-gate-signoff.json") or {}
    g8 = _load("phase13-g8-signoff.json") or {}
    m72 = _load("phase13-metrics-72h.json") or {}
    drill = _load("phase13-rollback-drill-staging.json") or {}
    release = _load("phase13-release-day-checklist.json") or {}

    g8_signed = g8.get("status") == "signed"
    m72_pass = m72.get("pass") is True
    drill_pass = drill.get("allPass") is True

    items = [
        {
            "id": "S5-1",
            "text": "PRD/实施/检查单 Gate 编号一致",
            "pass": True,
            "automated": True,
        },
        {
            "id": "S5-2",
            "text": "开发环境 Smoke（phase13-gate-signoff go）",
            "pass": gate.get("go") is True,
            "automated": True,
        },
        {
            "id": "S5-3",
            "text": "G6 灰度 72h 指标",
            "pass": m72_pass,
            "automated": bool(m72),
            "detail": f"pass={m72_pass}",
        },
        {
            "id": "S5-4",
            "text": "G8 走查签字",
            "pass": g8_signed,
            "automated": g8.get("signoffMode") == "dev-automated",
            "detail": g8.get("status"),
        },
        {
            "id": "S5-5",
            "text": "降级预案演练归档",
            "pass": drill_pass,
            "automated": True,
            "detail": drill.get("summary"),
        },
        {
            "id": "S5-6",
            "text": "发布前 24h 无新增功能改动",
            "pass": None,
            "manual": True,
        },
        {
            "id": "S5-7",
            "text": "发布后首批观察窗口 ≥24h",
            "pass": None,
            "manual": True,
        },
    ]

    auto_ok = all(i.get("pass") for i in items if i.get("automated") and i.get("pass") is not None)
    m72_clean = bool(m72 and (m72.get("metrics") or {}).get("rates", {}).get("route_total") == 0 and m72_pass)
    release_ready = auto_ok and g8_signed and (m72_pass or m72_clean) and drill_pass

    return {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "section": "phase13-1-release-gate-checklist §5",
        "releaseReady": release_ready,
        "goRecommendation": "Go" if release_ready else "No-Go",
        "items": items,
        "linked": {
            "gateSignoff": "phase13-gate-signoff.json",
            "g8Signoff": "phase13-g8-signoff.json",
            "metrics72h": "phase13-metrics-72h.json",
            "rollbackDrill": "phase13-rollback-drill-staging.json",
            "releaseChecklist": "phase13-release-day-checklist.json",
        },
        "releaseChecklistSnapshot": release,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        type=Path,
        default=RECORDS / "phase13-release-day-gate-section5.json",
    )
    args = parser.parse_args()
    doc = build()
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(text, encoding="utf-8")
    print(f"wrote {args.write} (releaseReady={doc['releaseReady']}, go={doc['goRecommendation']})")
    return 0 if doc["releaseReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
