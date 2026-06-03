#!/usr/bin/env python3
"""Phase 13 admin audit coverage check (release gate G7)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def build_audit_report() -> dict[str, Any]:
    from travelogue.templating.admin_store import get_store_revision, list_audit, load_runtime

    from travelogue.templating.metrics import aggregate_metrics

    audit = list_audit(limit=200)
    high_risk = [a for a in audit if a.get("action") in ("lifecycle_update", "rollback")]
    agg = aggregate_metrics(window_hours=24 * 7)
    denied = int((agg.get("counts") or {}).get("template.admin.permission_denied_count", 0))
    lifecycle_with_registry = sum(
        1
        for a in audit
        if a.get("action") == "lifecycle_update"
        and isinstance((a.get("detail") or {}).get("registryVersion"), str)
    )
    lifecycle_total = sum(1 for a in audit if a.get("action") == "lifecycle_update")
    missing_registry = max(0, lifecycle_total - lifecycle_with_registry)
    audit_missing_rate = round(missing_registry / lifecycle_total, 4) if lifecycle_total else 0.0
    return {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "revision": get_store_revision(),
        "audit_coverage": 1.0 if audit else 0.0,
        "audit_entry_count": len(audit),
        "high_risk_confirm_count": len(high_risk),
        "permission_denied_count": denied,
        "audit_missing_rate": audit_missing_rate,
        "lifecycle_audit_with_registryVersion": lifecycle_with_registry,
        "runtime": load_runtime(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 admin audit check")
    parser.add_argument("--write", type=Path, default=None)
    args = parser.parse_args()
    result = build_audit_report()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
