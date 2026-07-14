#!/usr/bin/env python3
"""Smoke-test a Travelogue Studio portable onedir away from the source tree.

Usage:
  python scripts/smoke_studio_portable.py
  python scripts/smoke_studio_portable.py --dist dist/TravelogueStudio
  python scripts/smoke_studio_portable.py --zip dist/TravelogueStudio-portable-0.2.0-beta.1.zip
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ONEDIR = ROOT / "dist" / "TravelogueStudio"
DEFAULT_PORT = 18766


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(resp.status) < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _prepare_workdir(dist: Path | None, zip_path: Path | None) -> tuple[Path, Path]:
    """Return (workdir, exe_path). Caller must delete workdir if it is a temp dir."""
    if zip_path is not None:
        if not zip_path.is_file():
            raise SystemExit(f"zip not found: {zip_path}")
        work = Path(tempfile.mkdtemp(prefix="tg-smoke-"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(work)
        # Prefer nested TravelogueStudio/ from our zip layout.
        nested = work / "TravelogueStudio" / "TravelogueStudio.exe"
        if nested.is_file():
            return work, nested
        flat = work / "TravelogueStudio.exe"
        if flat.is_file():
            return work, flat
        raise SystemExit(f"TravelogueStudio.exe not found under extracted zip: {work}")

    src = dist or DEFAULT_ONEDIR
    if not src.is_dir():
        raise SystemExit(f"onedir not found: {src}")
    exe_src = src / "TravelogueStudio.exe"
    if not exe_src.is_file():
        raise SystemExit(f"exe not found: {exe_src}")
    work = Path(tempfile.mkdtemp(prefix="tg-smoke-"))
    dest = work / "TravelogueStudio"
    shutil.copytree(src, dest)
    return work, dest / "TravelogueStudio.exe"


def run_smoke(*, dist: Path | None, zip_path: Path | None, port: int, timeout_sec: float) -> int:
    work, exe = _prepare_workdir(dist, zip_path)
    url = f"http://127.0.0.1:{port}/"
    print(f"smoke workdir: {work}")
    print(f"smoke exe: {exe}")

    # Ensure portable mode sidecars exist (copytree/zip should already).
    if not any(p.name.lower() == "portable.flag" for p in exe.parent.iterdir() if p.is_file()):
        (exe.parent / "portable.flag").write_text("portable\n", encoding="utf-8")
        print("warning: injected portable.flag for smoke")

    proc = subprocess.Popen(
        [str(exe), "studio", "--no-open", "--port", str(port), "--host", "127.0.0.1"],
        cwd=str(exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if proc.poll() is not None:
                print(f"FAIL: process exited early code={proc.returncode}")
                log_path = exe.parent / "logs" / "studio.log"
                if log_path.is_file():
                    print("--- studio.log (tail) ---")
                    print(log_path.read_text(encoding="utf-8", errors="replace")[-2000:])
                return 1
            if _http_ok(url):
                print(f"PASS: HTTP 200 {url}")
                trips = exe.parent / "trips"
                logs = exe.parent / "logs"
                print(f"  portable trips dir exists={trips.is_dir()} path={trips}")
                print(f"  portable logs dir exists={logs.is_dir()} path={logs}")
                marker = exe.parent / ".travelogue-ownership"
                print(f"  ownership marker exists={marker.is_file()}")
                return 0
            time.sleep(0.5)
        print(f"FAIL: timed out waiting for {url} after {timeout_sec:.0f}s")
        log_path = exe.parent / "logs" / "studio.log"
        if log_path.is_file():
            print("--- studio.log (tail) ---")
            print(log_path.read_text(encoding="utf-8", errors="replace")[-2000:])
        return 1
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=None, help="onedir folder")
    parser.add_argument("--zip", type=Path, default=None, help="portable zip")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args(argv)
    return run_smoke(
        dist=args.dist.resolve() if args.dist else None,
        zip_path=args.zip.resolve() if args.zip else None,
        port=args.port,
        timeout_sec=args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
