"""AA · stratum audit CLI (compare / apply / rebuild merged)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.aesthetic_stratum_audit import (  # noqa: E402
    apply_stratum_audit,
    audit_label_strata,
)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · stratum label audit")
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Rewrite labels with audited strata")
    parser.add_argument("--write-audit", type=Path, default=None)
    parser.add_argument("--write-labels", type=Path, default=None, help="Defaults to --labels when --apply")
    args = parser.parse_args(argv)

    trip_dir = _resolve(args.trip_dir)
    labels_path = _resolve(args.labels)
    labels_doc = _load_json(labels_path)
    rows = labels_doc if isinstance(labels_doc, list) else list(labels_doc.get("rows") or [])

    audit = audit_label_strata(trip_dir=trip_dir, label_rows=rows)
    audit["auditedAt"] = datetime.now(UTC).isoformat()

    print(f"trip={audit['tripId']} labeled={audit['labeledCount']} changes={audit['changeCount']}")
    print(f"old={audit['oldStrata']}")
    print(f"new={audit['newStrata']}")

    if args.write_audit:
        _save_json(_resolve(args.write_audit), audit)
        print(_resolve(args.write_audit))

    if args.apply:
        note = (
            "stratum 批量修正：review_stratum_for_asset（faces[] bbox only；横图优先 landscape）"
        )
        updated = apply_stratum_audit(labels_doc if isinstance(labels_doc, dict) else {"rows": rows}, audit, audit_note=note)
        out_path = _resolve(args.write_labels) if args.write_labels else labels_path
        _save_json(out_path, updated)
        print(out_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
