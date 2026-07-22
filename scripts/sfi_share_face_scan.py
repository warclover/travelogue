#!/usr/bin/env python3
"""Share-Face Integrity W0 · 读者面禁入句抽检（QA-SFI-01 / AC-SFI-01）。

扫描 trip 目录下 index.html / index-mobile.html / index-longshot.html / present.html
是否仍含禁入子串（含 decorLine 透传遗留）。

用法::

    python scripts/sfi_share_face_scan.py
    python scripts/sfi_share_face_scan.py --trips-dir trips --only demo-album
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 与 domain/share_face_copy._BANNED_SUBSTRINGS + 弱枚举样本对齐（抽检用）
_BANNED = (
    "竖幅",
    "横幅",
    "抬头看见",
    "慢慢翻",
    "碎片拼成",
    "下次再见",
    "示例游记",
    "白天，傍晚",
    "夜景，白天",
    "上午、下午",
)

_SURFACES = (
    "index.html",
    "index-mobile.html",
    "index-longshot.html",
    "present.html",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"read-error:{exc}"]
    hits = [phrase for phrase in _BANNED if phrase in text]
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SFI W0 · share-face banned-phrase scan")
    parser.add_argument("--trips-dir", type=Path, default=_repo_root() / "trips")
    parser.add_argument("--only", type=str, default="")
    args = parser.parse_args(argv)

    trips_dir = args.trips_dir.resolve()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    total_hits = 0
    scanned = 0

    for child in sorted(trips_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if only and child.name not in only:
            continue
        if not (child / "trip.json").is_file():
            continue
        for name in _SURFACES:
            path = child / name
            if not path.is_file():
                continue
            scanned += 1
            hits = scan_file(path)
            if hits:
                total_hits += len(hits)
                print(f"HIT {child.name}/{name}: {', '.join(hits)}")

    print(f"scanned={scanned} hit_phrases={total_hits}")
    return 1 if total_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
