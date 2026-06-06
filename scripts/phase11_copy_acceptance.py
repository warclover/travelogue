#!/usr/bin/env python3
"""Phase 11 offline acceptance metrics → JSON record."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from travelogue.config import AppConfig, NarrativeConfig
from travelogue.services.decor_line import apply_decor_lines


def _fixture_trips() -> list[dict]:
    base = {
        "tripId": "p11-metrics",
        "meta": {"title": "指标", "tone": "relaxed"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["街景"],
                "place": {"city": "大阪"},
            }
        ],
    }
    filled = {
        **base,
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "抵达",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"memoryAnchors": ["道顿堀"]},
            }
        ],
    }
    sparse = {
        **base,
        "chapters": [
            {
                "id": "ch-02",
                "index": 1,
                "patternId": "open",
                "title": "",
                "items": [],
            }
        ],
    }
    return [filled, sparse]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 11 copy acceptance metrics")
    parser.add_argument(
        "--write",
        type=Path,
        default=REPO / "docs" / "acceptance-records" / "phase11-copy.json",
    )
    args = parser.parse_args()
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=True))
    total = 0
    filled = 0
    for trip in _fixture_trips():
        apply_decor_lines(trip, cfg=cfg)
        for ch in trip.get("chapters") or []:
            total += 1
            if (ch.get("decorLine") or "").strip():
                filled += 1
    record = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "P11-LiteCopy",
        "metrics": {
            "decor_line_fill_rate": round(filled / total, 3) if total else 0.0,
            "chapters_sampled": total,
            "chapters_with_decor_line": filled,
        },
        "notes": "Synthetic fixture only; blind review (AC-P11-04) remains manual.",
    }
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
