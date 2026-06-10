"""B4 验收 · 双样本节奏指标（demo-2025-2 / linzhi）。

用法：python scripts/rhythm_acceptance.py <trip_id>
在内存中重跑 run_curate，输出 portrait-2 最大连续、全竖朝向最大连续、
audit_rhythm_violations 与 pattern 分布。
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    trip_id = sys.argv[1]
    trip = json.loads((ROOT / "trips" / trip_id / "trip.json").read_text(encoding="utf-8"))
    trip = copy.deepcopy(trip)

    from travelogue.curation.curate import run_curate
    from travelogue.curation.layout_constraints import (
        audit_rhythm_violations,
        is_portrait_orientation_pattern,
        is_portrait_pair_pattern,
    )

    run_curate(trip, apply_layout=True, trip_dir=None)
    chapters = trip.get("chapters") or []

    pats: list[str] = []
    for ch in chapters:
        for sc in ch.get("screens") or []:
            if any(s.get("assetId") for s in (sc.get("slots") or [])):
                pats.append(str(sc.get("patternId") or ""))

    def max_streak(pred) -> int:
        best = cur = 0
        for p in pats:
            if p.startswith("screen-breath") or p.startswith("screen-decor"):
                continue
            cur = cur + 1 if pred(p) else 0
            best = max(best, cur)
        return best

    pair_streak = max_streak(is_portrait_pair_pattern)
    orient_streak = max_streak(is_portrait_orientation_pattern)
    viol = audit_rhythm_violations(chapters)

    print(f"=== {trip_id} ===")
    print(f"content screens: {len(pats)}")
    print(f"max portrait-2 streak: {pair_streak}")
    print(f"max portrait-orientation streak: {orient_streak}")
    print(f"audit_rhythm_violations: {len(viol)}")
    for v in viol:
        print(f"  - {v.code} ch={v.chapter_id} screen={v.screen_index}")
    print("pattern distribution:")
    for pid, n in sorted(Counter(pats).items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
