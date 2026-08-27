#!/usr/bin/env python3
"""Scan git-tracked images for magic-byte / extension drift (B-04).

Default is warning-only (exit 0 after printing). ``--strict`` fails CI.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def tracked_images(*, root: Path = ROOT) -> list[Path]:
    raw = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "*.png", "*.jpg", "*.jpeg", "*.webp"],
        cwd=root,
    )
    out: list[Path] = []
    for rel in raw.split(b"\0"):
        if not rel:
            continue
        path = root / rel.decode("utf-8")
        if path.suffix.lower() in IMAGE_SUFFIXES:
            out.append(path)
    return out


def classify_bytes(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


def expected_kind(suffix: str) -> str:
    if suffix in {".jpg", ".jpeg"}:
        return "jpeg"
    return suffix.lstrip(".")


def scan(paths: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in paths:
        try:
            data = path.read_bytes()[:16]
        except OSError as exc:
            issues.append(f"{path.as_posix()}: unreadable ({exc})")
            continue
        kind = classify_bytes(data)
        want = expected_kind(path.suffix.lower())
        if kind is None:
            issues.append(f"{path.as_posix()}: unrecognized signature")
        elif kind != want:
            issues.append(f"{path.as_posix()}: signature is {kind}, extension expects {want}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint tracked image signatures")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any tracked image fails the signature check",
    )
    args = parser.parse_args()
    issues = scan(tracked_images())
    if not issues:
        print("binary assets: ok")
        return 0
    print(f"binary assets: {len(issues)} issue(s)")
    for item in issues:
        print(f"  {item}")
    if args.strict:
        return 1
    print("binary assets: warning only (pass --strict to fail)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
