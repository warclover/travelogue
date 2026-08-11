#!/usr/bin/env python3
"""Validate LSE ratchet baseline against computed edges and growth log."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = ROOT / "docs" / "acceptance-records" / "lse-cross-import-baseline.json"
GROWTH_LOG = ROOT / "docs" / "acceptance-records" / "lse-cross-import-growth-log.json"


def _edge_total(report: dict[str, object]) -> int:
    return int(report.get("totalCrossEdges", report.get("total_edges", 0)))


def _edge_signatures(report: dict[str, object]) -> list[str]:
    edges = report.get("edges") or []
    out: list[str] = []
    for item in edges:
        if not isinstance(item, dict):
            continue
        importer = str(item.get("importer") or "").strip()
        imported = str(item.get("imported") or "").strip()
        if importer and imported:
            out.append(f"{importer}->{imported}")
    return sorted(out)


def _snapshot(report: dict[str, object]) -> dict[str, object]:
    return {
        "totalCrossEdges": _edge_total(report),
        "layoutEngineToCuration": int(report.get("layoutEngineToCuration", 0)),
        "curationToLayoutEngine": int(report.get("curationToLayoutEngine", 0)),
        "edgeSignatures": _edge_signatures(report),
    }


def _parse_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _validate_tracking_issue(root: Path, raw: object) -> str | None:
    text = str(raw or "").strip()
    rel_path, sep, anchor = text.partition("#")
    if not sep or not rel_path.strip() or not anchor.strip():
        return "tracking issue must be repo-relative path#anchor"
    target = (root / rel_path.strip()).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return "tracking issue path must stay inside repository"
    if not target.is_file():
        return f"tracking issue file not found: {rel_path.strip()}"
    if anchor.strip() not in target.read_text(encoding="utf-8"):
        return f"tracking issue anchor not found: {anchor.strip()}"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-file", type=Path, default=BASELINE, help=argparse.SUPPRESS)
    parser.add_argument("--growth-log-file", type=Path, default=GROWTH_LOG, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not args.baseline_file.is_file():
        print("missing baseline; run scripts/lint_lse_cross_import.py --update-baseline", file=sys.stderr)
        return 1
    if not args.growth_log_file.is_file():
        print("missing growth log; run scripts/lint_lse_cross_import.py --update-baseline", file=sys.stderr)
        return 1

    from scripts.lse_cross_import_stats import scan_edges, summarize

    computed = summarize(scan_edges())
    baseline = json.loads(args.baseline_file.read_text(encoding="utf-8"))
    growth = json.loads(args.growth_log_file.read_text(encoding="utf-8"))
    computed_snapshot = _snapshot(computed)
    baseline_snapshot = _snapshot(baseline)
    current_baseline = growth.get("currentBaseline")

    if baseline_snapshot != computed_snapshot:
        print("REGRESSION: committed baseline diverges from computed edges", file=sys.stderr)
        print(
            f"  baseline total={baseline_snapshot['totalCrossEdges']} computed total={computed_snapshot['totalCrossEdges']}",
            file=sys.stderr,
        )
        return 1

    if current_baseline != computed_snapshot:
        print("REGRESSION: growth log currentBaseline diverges from computed edges", file=sys.stderr)
        return 1

    entries = growth.get("entries")
    if not isinstance(entries, list):
        print("REGRESSION: growth log entries must be a list", file=sys.stderr)
        return 1

    today = date.today()
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            print(f"REGRESSION: growth log entry #{idx} must be an object", file=sys.stderr)
            return 1
        due = _parse_date(entry.get("due_date"))
        if due is None:
            print(f"REGRESSION: growth log entry #{idx} has invalid due_date", file=sys.stderr)
            return 1
        if due < today:
            print(
                f"REGRESSION: growth log entry #{idx} expired on {entry.get('due_date')}",
                file=sys.stderr,
            )
            return 1
        issue_error = _validate_tracking_issue(ROOT, entry.get("tracking_issue"))
        if issue_error:
            print(f"REGRESSION: growth log entry #{idx} {issue_error}", file=sys.stderr)
            return 1

    print(
        "LSE ratchet growth log OK: "
        f"{computed_snapshot['totalCrossEdges']} edges, {len(entries)} growth entr"
        f"{'y' if len(entries) == 1 else 'ies'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
