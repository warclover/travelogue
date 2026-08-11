#!/usr/bin/env python3
"""LSE cross-import regression gate (ADR-015 · M-B4 follow-up).

Fails if total layout_engine ↔ curation edges exceed ceiling (default: current baseline).
"""

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
DEFAULT_CEILING = 10


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


def _baseline_snapshot(report: dict[str, object]) -> dict[str, object]:
    return {
        "totalCrossEdges": _edge_total(report),
        "layoutEngineToCuration": int(report.get("layoutEngineToCuration", 0)),
        "curationToLayoutEngine": int(report.get("curationToLayoutEngine", 0)),
        "edgeSignatures": _edge_signatures(report),
    }


def _parse_due_date(raw: str) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _validate_tracking_issue(raw: str) -> tuple[bool, str]:
    text = str(raw or "").strip()
    if not text:
        return False, "missing --tracking-issue"
    rel_path, sep, anchor = text.partition("#")
    if not sep or not rel_path.strip() or not anchor.strip():
        return False, "tracking issue must be repo-relative path#anchor"
    target = (ROOT / rel_path.strip()).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return False, "tracking issue path must stay inside repository"
    if not target.is_file():
        return False, f"tracking issue file not found: {rel_path.strip()}"
    content = target.read_text(encoding="utf-8")
    if anchor.strip() not in content:
        return False, f"tracking issue anchor not found: {anchor.strip()}"
    return True, ""


def _load_growth_log(path: Path) -> dict[str, object]:
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    return {"ratchet": "lse-cross-import", "currentBaseline": {}, "entries": []}


def _write_growth_log(
    path: Path,
    *,
    report: dict[str, object],
    old_report: dict[str, object] | None,
    tracking_issue: str | None,
    due_date: str | None,
) -> tuple[dict[str, object], bool]:
    payload = _load_growth_log(path)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        entries = []
    grew = old_report is not None and _edge_total(report) > _edge_total(old_report)
    if grew:
        entries.append(
            {
                "date": date.today().isoformat(),
                "old_ceiling": _edge_total(old_report),
                "new_ceiling": _edge_total(report),
                "old_layoutEngineToCuration": int(old_report.get("layoutEngineToCuration", 0)),
                "new_layoutEngineToCuration": int(report.get("layoutEngineToCuration", 0)),
                "old_curationToLayoutEngine": int(old_report.get("curationToLayoutEngine", 0)),
                "new_curationToLayoutEngine": int(report.get("curationToLayoutEngine", 0)),
                "tracking_issue": str(tracking_issue or "").strip(),
                "due_date": str(due_date or "").strip(),
            }
        )
    payload = {
        "ratchet": "lse-cross-import",
        "currentBaseline": _baseline_snapshot(report),
        "entries": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload, grew


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-file", type=Path, default=BASELINE, help=argparse.SUPPRESS)
    parser.add_argument("--growth-log-file", type=Path, default=GROWTH_LOG, help=argparse.SUPPRESS)
    parser.add_argument(
        "--max-edges",
        type=int,
        default=None,
        help="Fail if total cross-import edges exceed this count",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Refresh baseline JSON when edge count decreased",
    )
    parser.add_argument(
        "--allow-growth",
        action="store_true",
        help="Permit baseline update when cross-import edges intentionally grow",
    )
    parser.add_argument(
        "--tracking-issue",
        default="",
        help="Repo-local backlog anchor for intentional growth, e.g. docs/ARCH-OPT-P2-BACKLOG.md#P2-A",
    )
    parser.add_argument(
        "--due-date",
        default="",
        help="Retirement date for intentional growth (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    from scripts.lse_cross_import_stats import scan_edges, summarize

    report = summarize(scan_edges())
    total = _edge_total(report)
    ceiling = args.max_edges
    if ceiling is None and args.baseline_file.is_file():
        ceiling = _edge_total(json.loads(args.baseline_file.read_text(encoding="utf-8")))
    if ceiling is None:
        ceiling = DEFAULT_CEILING

    if args.update_baseline:
        old_report = None
        if args.baseline_file.is_file():
            old_report = json.loads(args.baseline_file.read_text(encoding="utf-8"))
            old_total = _edge_total(old_report)
            if total > old_total and not args.allow_growth:
                print(
                    "refusing baseline update; growth without --allow-growth:",
                    file=sys.stderr,
                )
                print(f"  totalCrossEdges: {old_total} -> {total}", file=sys.stderr)
                return 1
            if total > old_total:
                valid, reason = _validate_tracking_issue(args.tracking_issue)
                if not valid:
                    print(f"invalid --tracking-issue: {reason}", file=sys.stderr)
                    return 1
                parsed_due = _parse_due_date(args.due_date)
                if parsed_due is None:
                    print("invalid --due-date: expected YYYY-MM-DD", file=sys.stderr)
                    return 1
                if parsed_due < date.today():
                    print("invalid --due-date: date already passed", file=sys.stderr)
                    return 1
        args.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        args.baseline_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _payload, grew = _write_growth_log(
            args.growth_log_file,
            report=report,
            old_report=old_report,
            tracking_issue=args.tracking_issue,
            due_date=args.due_date,
        )
        print(f"baseline updated: {total} edges")
        if grew:
            print(f"growth logged: {args.tracking_issue} until {args.due_date}")
        return 0

    print(f"LSE cross-import edges: {total} (ceiling {ceiling})")
    if total > ceiling:
        print("REGRESSION: edge count above ceiling", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
