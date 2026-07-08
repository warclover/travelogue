#!/usr/bin/env python3
"""M-A0 one-shot acceptance: duplicate top-level keys + load_config equivalence."""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "config.yaml.example"


def _top_level_keys(path: Path) -> list[str]:
    keys: list[str] = []
    for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")) or []:
        if isinstance(doc, dict):
            keys.extend(doc.keys())
    return keys


def check_no_duplicate_top_level_keys(path: Path) -> None:
    keys = _top_level_keys(path)
    seen: set[str] = set()
    dupes: set[str] = set()
    for key in keys:
        if key in seen:
            dupes.add(key)
        seen.add(key)
    if dupes:
        raise SystemExit(f"duplicate top-level keys: {sorted(dupes)}")


def _appconfig_snapshot(path: Path):
    from travelogue.config.loader import load_config

    return load_config(path)


def _normalize(obj, *, exclude_paths: bool = False):
    if dataclasses.is_dataclass(obj):
        out = {}
        for f in dataclasses.fields(obj):
            if exclude_paths and f.name == "config_path":
                continue
            out[f.name] = _normalize(getattr(obj, f.name), exclude_paths=exclude_paths)
        return out
    if isinstance(obj, dict):
        return {k: _normalize(v, exclude_paths=exclude_paths) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [_normalize(x, exclude_paths=exclude_paths) for x in obj]
    return obj


def compare_load_config(before_path: Path, after_path: Path) -> None:
    before = _normalize(_appconfig_snapshot(before_path), exclude_paths=True)
    after = _normalize(_appconfig_snapshot(after_path), exclude_paths=True)
    if before != after:
        # Print first differing top-level section for debugging.
        for key in sorted(set(before) | set(after)):
            if before.get(key) != after.get(key):
                raise SystemExit(f"load_config mismatch at AppConfig.{key}")
        raise SystemExit("load_config snapshots differ")
    print("load_config equivalence: OK (before duplicate-merge vs after merged example)")


def main() -> int:
    check_no_duplicate_top_level_keys(EXAMPLE)
    print(f"no duplicate top-level keys: OK ({EXAMPLE.name})")

    before_bytes = subprocess.check_output(
        ["git", "show", "master:config.yaml.example"],
        cwd=ROOT,
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        before_file = tmp_path / "config.yaml.example.before"
        before_file.write_bytes(before_bytes)
        compare_load_config(before_file, EXAMPLE)

    yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    print("yaml.safe_load: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
