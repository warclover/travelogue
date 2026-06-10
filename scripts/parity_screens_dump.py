"""A5 等价性回归 · dump screens 签名（架构收敛验证用，临时脚本）。

用法：python scripts/parity_screens_dump.py <trip_id> <out_json>
对 trips/<trip_id>/trip.json 在内存中重跑 run_curate，导出
[chapterId, patternId, slotAssetIds] 序列供 before/after diff。
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    trip_id, out_path = sys.argv[1], sys.argv[2]
    trip_file = ROOT / "trips" / trip_id / "trip.json"
    trip = json.loads(trip_file.read_text(encoding="utf-8"))
    trip = copy.deepcopy(trip)

    from travelogue.curation.curate import run_curate

    run_curate(trip, apply_layout=True, trip_dir=None)

    sig = []
    for ch in trip.get("chapters") or []:
        for sc in ch.get("screens") or []:
            sig.append(
                {
                    "ch": ch.get("id"),
                    "pattern": sc.get("patternId"),
                    "assets": [
                        s.get("assetId") for s in (sc.get("slots") or []) if s.get("assetId")
                    ],
                }
            )
    Path(out_path).write_text(
        json.dumps(sig, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"{trip_id}: {len(sig)} screens -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
