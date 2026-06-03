"""Generate M21-e2 v3 retirement delete command plan.

By default this script only prints a safe command plan.
It does not delete anything unless --apply is explicitly provided.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DELETE_GROUPS: list[tuple[str, list[str]]] = [
    (
        "group-1-v3-entry",
        [
            "templates/studio/studio.html",
            "templates/studio/studio.js",
            "templates/studio/studio.css",
        ],
    ),
    (
        "group-2-v3-only-modules",
        [
            "templates/studio/js/navigation.js",
            "templates/studio/js/render.js",
            "templates/studio/js/sheet.js",
            "templates/studio/js/samples.js",
            "templates/studio/js/init.js",
            "templates/studio/js/viewport.js",
        ],
    ),
]


def build_delete_commands() -> list[str]:
    cmds: list[str] = []
    for _group, files in DELETE_GROUPS:
        joined = " ".join(files)
        cmds.append(f"git rm {joined}")
    return cmds


def verify_files_exist() -> list[str]:
    missing: list[str] = []
    for _group, files in DELETE_GROUPS:
        for rel in files:
            if not (ROOT / rel).exists():
                missing.append(rel)
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M21-e2 delete plan generator")
    parser.add_argument("--apply", action="store_true", help="execute generated git rm commands")
    args = parser.parse_args(argv)

    missing = verify_files_exist()
    if missing:
        print("missing_files:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    commands = build_delete_commands()
    print("planned_commands:")
    for i, cmd in enumerate(commands, start=1):
        print(f"{i}. {cmd}")

    if not args.apply:
        print("dry_run=true")
        return 0

    for cmd in commands:
        rc = subprocess.run(cmd, shell=True, cwd=ROOT).returncode
        if rc != 0:
            print(f"apply_failed: {cmd}")
            return rc
    print("apply_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
