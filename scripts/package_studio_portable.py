#!/usr/bin/env python3
"""Finalize Travelogue Studio onedir into a portable zip (M-INS-0a).

Assumes PyInstaller already wrote dist/TravelogueStudio/.
Injects portable.flag, 使用说明.txt, VERSION.txt, SHA256SUMS, then zips.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging"
DIST = ROOT / "dist"
ONEDIR_NAME = "TravelogueStudio"


def _read_version() -> str:
    raw = (PACKAGING / "VERSION").read_text(encoding="utf-8").strip()
    if not raw:
        raise SystemExit("packaging/VERSION is empty")
    return raw.splitlines()[0].strip()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_onedir(onedir: Path) -> Path:
    exe = onedir / f"{ONEDIR_NAME}.exe"
    internal = onedir / "_internal"
    if not exe.is_file():
        raise SystemExit(f"missing exe: {exe}")
    if not internal.is_dir():
        raise SystemExit(f"missing onedir _internal/: {internal} (is the build still onefile?)")
    return exe


def finalize(dist_dir: Path, *, make_zip: bool = True) -> Path:
    onedir = dist_dir / ONEDIR_NAME
    if not onedir.is_dir():
        raise SystemExit(f"onedir not found: {onedir} — run PyInstaller first")

    exe = _require_onedir(onedir)
    version = _read_version()

    shutil.copy2(PACKAGING / "portable.flag", onedir / "portable.flag")
    shutil.copy2(PACKAGING / "使用说明.txt", onedir / "使用说明.txt")
    (onedir / "VERSION.txt").write_text(version + "\n", encoding="utf-8")

    # Gate A invite sidecars (T-A-02) — optional folder next to exe
    gate_a_src = PACKAGING / "gate-a"
    gate_a_dst = onedir / "gate-a"
    if gate_a_src.is_dir():
        if gate_a_dst.exists():
            shutil.rmtree(gate_a_dst)
        shutil.copytree(gate_a_src, gate_a_dst)
    else:
        gate_a_dst = Path()  # nonexistent sentinel

    # Hash key user-facing files at zip root (exe + sidecar docs).
    hash_targets = [
        exe,
        onedir / "portable.flag",
        onedir / "使用说明.txt",
        onedir / "VERSION.txt",
    ]
    lines: list[str] = []
    for path in hash_targets:
        digest = _sha256_file(path)
        rel = path.relative_to(onedir).as_posix()
        lines.append(f"{digest}  {rel}")
    (onedir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OK: {onedir}")
    print(f"    VERSION={version}")
    print(f"    sidecar: portable.flag, 使用说明.txt, VERSION.txt, SHA256SUMS")
    if gate_a_dst.is_dir():
        print(f"    gate-a invite materials: {gate_a_dst}")

    if not make_zip:
        return onedir

    zip_name = f"{ONEDIR_NAME}-portable-{version}.zip"
    zip_path = dist_dir / zip_name
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(onedir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=Path(ONEDIR_NAME) / path.relative_to(onedir))

    print(f"OK: {zip_path}")
    print(f"    size={zip_path.stat().st_size / (1024 * 1024):.1f} MiB")
    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        type=Path,
        default=DIST,
        help="directory containing TravelogueStudio/ (default: repo dist/)",
    )
    parser.add_argument("--no-zip", action="store_true", help="skip portable zip")
    args = parser.parse_args(argv)
    finalize(args.dist.resolve(), make_zip=not args.no_zip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
