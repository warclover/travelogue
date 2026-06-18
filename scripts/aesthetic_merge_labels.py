"""AA · rebuild merged labels + stratified baseline report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.aesthetic_blind_review import srcc_report  # noqa: E402


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_label_docs(
    sources: list[tuple[str, Path]],
    *,
    frozen: bool,
    notes: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    trips: list[str] = []
    for trip_id, path in sources:
        doc = _load_json(path)
        part = [r for r in (doc.get("rows") or []) if r.get("humanScore") is not None]
        rows.extend(part)
        trips.append(trip_id)
    return {
        "version": "3",
        "frozen": frozen,
        "frozenAt": datetime.now(timezone.utc).isoformat() if frozen else None,
        "notes": notes,
        "mergedAt": datetime.now(timezone.utc).isoformat(),
        "trips": trips,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · merge labels + stratified baseline")
    parser.add_argument("--write-merged", type=Path, default=Path("docs/acceptance-records/aesthetic-human-labels.merged.v3.json"))
    parser.add_argument("--write-baseline", type=Path, default=Path("docs/acceptance-records/aesthetic-baseline-stratified.v3.json"))
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args(argv)

    sources = [
        ("demo-2025-6", _resolve(Path("docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json"))),
        ("demo-fc8b3a5c08", _resolve(Path("docs/acceptance-records/aesthetic-human-labels.demo-fc8b3a5c08.v3.json"))),
        ("demo-1a737d6205", _resolve(Path("docs/acceptance-records/aesthetic-human-labels.demo-1a737d6205.json"))),
        ("demo-53cda5151f", _resolve(Path("docs/acceptance-records/aesthetic-human-labels.demo-53cda5151f.json"))),
    ]
    merged = merge_label_docs(
        sources,
        frozen=bool(args.freeze),
        notes="Merged v3 · 东澳 109 + 锡兰 146 + 张智慧 60 + 美食 17 = 332",
    )
    merged_path = _resolve(args.write_merged)
    _save_json(merged_path, merged)

    per_trip: dict[str, Any] = {}
    for trip_id, path in sources:
        doc = _load_json(path)
        rows = [r for r in (doc.get("rows") or []) if r.get("humanScore") is not None]
        rep = srcc_report(rows, by_stratum=True)
        per_trip[trip_id] = {
            "labelsPath": str(path.relative_to(ROOT)).replace("\\", "/"),
            "labeledCount": len(rows),
            "frozen": bool(doc.get("frozen")),
            "stratumAudit": doc.get("stratumAudit"),
            "srcc": {
                "pooled": rep.get("srcc"),
                "byStratum": rep.get("byStratum"),
            },
        }

    pooled = srcc_report(merged["rows"], by_stratum=True)
    baseline = {
        "version": "1",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "mergedSource": str(merged_path.relative_to(ROOT)).replace("\\", "/"),
        "sampleCount": pooled.get("sampleCount"),
        "pooledSrcc": pooled.get("srcc"),
        "byStratum": pooled.get("byStratum"),
        "perTrip": per_trip,
        "frozen": merged.get("frozen"),
    }
    baseline_path = _resolve(args.write_baseline)
    _save_json(baseline_path, baseline)

    print(merged_path, f"n={len(merged['rows'])} frozen={merged['frozen']}")
    print(baseline_path, f"pooled SRCC={pooled.get('srcc')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
