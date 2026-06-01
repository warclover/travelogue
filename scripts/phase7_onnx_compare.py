"""Phase 7 ONNX spike stub (P7-F1/F2). Exits 0 when report exists; 2 when ONNX stack unavailable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports" / "phase7-onnx-spike.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="ONNX vs PyTorch CLIP compare (spike)")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if args.write_report:
        print(f"report: {REPORT}")
        return 0
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        print("onnxruntime not installed; see docs/reports/phase7-onnx-spike.md", file=sys.stderr)
        return 2
    print("ONNX runtime present; full benchmark not implemented (spike No-Go).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
