#!/usr/bin/env python3
"""Scan git-tracked images for magic-byte / extension drift (B-04).

B-03 (2026-08-28): historical docs attachments are signed abandoned.
``--strict`` fails only on drift outside that allowlist.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ABANDONED_LIST = ROOT / "docs/acceptance-records/b03-abandoned-binary-assets.txt"


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


def load_abandoned(*, root: Path = ROOT) -> set[str]:
    path = root / "docs/acceptance-records/b03-abandoned-binary-assets.txt"
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        out.add(text.replace("\\", "/"))
    return out


def issue_rel_key(issue: str, *, root: Path) -> str:
    raw, _, _ = issue.partition(": ")
    path = Path(raw)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(raw).as_posix().replace("\\", "/")


def partition_issues(
    issues: list[str], *, root: Path, abandoned: set[str]
) -> tuple[list[str], list[str]]:
    signed: list[str] = []
    fresh: list[str] = []
    for item in issues:
        if issue_rel_key(item, root=root) in abandoned:
            signed.append(item)
        else:
            fresh.append(item)
    return signed, fresh


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint tracked image signatures")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when a non-abandoned tracked image fails the signature check",
    )
    args = parser.parse_args()
    root = ROOT
    issues = scan(tracked_images(root=root))
    signed, fresh = partition_issues(
        issues, root=root, abandoned=load_abandoned(root=root)
    )
    if not issues:
        print("binary assets: ok")
        return 0
    if signed:
        print(f"binary assets: {len(signed)} abandoned (B-03 signed-off)")
    if fresh:
        print(f"binary assets: {len(fresh)} new issue(s)")
        for item in fresh:
            print(f"  {item}")
    elif not signed:
        print(f"binary assets: {len(issues)} issue(s)")
        for item in issues:
            print(f"  {item}")
    if fresh and args.strict:
        return 1
    if fresh and not args.strict:
        print("binary assets: warning only (pass --strict to fail)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
