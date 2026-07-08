"""AC-P17-12 · aggregate pattern_diversity by strategyId/profileId.

Usage:
  python scripts/phase17_strategy_telemetry.py
  python scripts/phase17_strategy_telemetry.py --golden-cache .cache/p17-golden-metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def aggregate_from_golden_record(record: dict) -> dict:
    by_strategy: dict[str, dict] = {}
    for fr in record.get("fixtures") or []:
        for pair in fr.get("pairs") or []:
            cand = (pair.get("candidateMetrics") or {})
            diversity = cand.get("layout.chapter.pattern_diversity_p50")
            strategy_id = "lse-default-2026-06"
            profile_id = "default"
            bucket = by_strategy.setdefault(
                strategy_id,
                {"strategyId": strategy_id, "profiles": {}, "fixtureCount": 0},
            )
            prof = bucket["profiles"].setdefault(profile_id, {"values": [], "fixtureIds": []})
            if diversity is not None:
                prof["values"].append(float(diversity))
            prof["fixtureIds"].append(fr.get("fixtureId"))
            bucket["fixtureCount"] += 1
    for bucket in by_strategy.values():
        for prof in bucket["profiles"].values():
            vals = prof.pop("values", [])
            prof["patternDiversityP50Median"] = (
                round(sorted(vals)[len(vals) // 2], 4) if vals else None
            )
    return {"strategies": list(by_strategy.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description="P17 strategy telemetry aggregate")
    parser.add_argument(
        "--golden-cache",
        type=Path,
        default=ROOT / ".cache" / "p17-golden-metrics.json",
    )
    args = parser.parse_args()
    if not args.golden_cache.is_file():
        print(json.dumps({"error": "golden cache missing", "path": str(args.golden_cache)}))
        return 1
    record = json.loads(args.golden_cache.read_text(encoding="utf-8"))
    payload = {
        "emittedAt": _now(),
        "source": str(args.golden_cache.relative_to(ROOT)),
        "aggregate": aggregate_from_golden_record(record),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
