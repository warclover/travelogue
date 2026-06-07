"""LSE CLI · validate / probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from travelogue.layout_engine.registry import list_strategy_files, load_strategy_pack
from travelogue.layout_engine.validator import validate_strategy_file


def cmd_validate(args: argparse.Namespace) -> int:
    paths = [Path(p) for p in args.paths] if args.paths else list_strategy_files()
    failed = 0
    for path in paths:
        report = validate_strategy_file(path)
        if report.ok:
            pack = load_strategy_pack(path)
            print(f"OK {path} id={pack.id} hash={pack.content_hash}")
        else:
            failed += 1
            print(f"FAIL {path}")
            for issue in report.issues[:20]:
                print(f"  {issue.path}: {issue.message}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Travelogue LSE CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    val = sub.add_parser("validate", help="Validate strategy pack YAML against schema")
    val.add_argument("paths", nargs="*", help="Strategy YAML paths (default: all in strategies/)")
    val.set_defaults(func=cmd_validate)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
