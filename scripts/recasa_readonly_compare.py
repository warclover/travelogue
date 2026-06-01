"""M12-0-3 · Recasa read-only clustering comparison (not integrated).

Usage:
  python scripts/recasa_readonly_compare.py --fixture golden-mixed-scenes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Recasa read-only spike (M12-0-3)")
    parser.add_argument("--fixture", default="golden-mixed-scenes")
    args = parser.parse_args()
    from tests.clustering_fixtures import load_fixture_assets

    assets = load_fixture_assets(args.fixture)
    payload = {
        "fixture": args.fixture,
        "assetCount": len(assets),
        "status": "not_integrated",
        "note": "Recasa library not wired; use phase3 spike matrix for Go/No-Go.",
    }
    out = ROOT / "docs" / "acceptance-records" / "phase3-m12-0-spike.json"
    if out.is_file():
        data = json.loads(out.read_text(encoding="utf-8"))
        data["recasaReadonly"] = payload
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
