"""Phase 6 P5 rollback CLI (AC-P6-07 drill)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Phase 6 P5 rollback config patch")
    parser.add_argument("--config", type=Path, default=None, help="config.yaml path")
    parser.add_argument("--dry-run", action="store_true", help="print patch only")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from travelogue.curation.phase6_rollout import apply_p5_rollback_config, p5_rollback_patch

    patch = p5_rollback_patch()
    if args.dry_run:
        print(json.dumps(patch, indent=2, ensure_ascii=False))
        return 0

    path = apply_p5_rollback_config(args.config)
    print(json.dumps({"applied": str(path), "patch": patch}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
