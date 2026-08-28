"""Export the journal vertical-slice funnel baseline (MET-01 · Sprint 0).

Reads the local Studio jsonl and prints four stages:
home_enter → import_success → first_preview → first_export.

Usage:
    python scripts/studio_funnel_baseline.py [--input PATH] [--out JSON]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from travelogue.domain.studio_funnel import build_funnel_baseline, format_funnel_baseline
from travelogue.web.studio_homepage_telemetry import studio_homepage_events_path


def _parse_events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if isinstance(rec, dict) and rec.get("event"):
            rows.append(rec)
    return rows


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None, help="jsonl path")
    parser.add_argument("--out", type=Path, default=None, help="optional JSON dump")
    args = parser.parse_args(argv)

    source = args.input or studio_homepage_events_path()
    events = _parse_events(source)
    baseline = build_funnel_baseline(events)
    sys.stdout.write(format_funnel_baseline(baseline, source_path=str(source)))
    if args.out:
        payload = {
            "source": str(source),
            "total_events": baseline.total_events,
            "first_ts": baseline.first_ts,
            "last_ts": baseline.last_ts,
            "stages": [
                {
                    "id": stage.id,
                    "label": stage.label,
                    "event_count": stage.event_count,
                    "unique_trips": stage.unique_trips,
                    "conversion_from_prev": stage.conversion_from_prev,
                    "median_seconds_from_prev": stage.median_seconds_from_prev,
                    "source": stage.source,
                }
                for stage in baseline.stages
            ],
        }
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
