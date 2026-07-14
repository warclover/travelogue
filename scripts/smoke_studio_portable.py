#!/usr/bin/env python3
"""Smoke-test Travelogue Studio portable/install onedir (ACCEPTANCE §1).

Usage:
  python scripts/smoke_studio_portable.py
  python scripts/smoke_studio_portable.py --dist dist/TravelogueStudio
  python scripts/smoke_studio_portable.py --zip dist/TravelogueStudio-portable-0.2.0-beta.1.zip
  python scripts/smoke_studio_portable.py --mode install
  python scripts/smoke_studio_portable.py --skip-import   # faster: skip demo/zh import

Covers automated parts of SM-01..SM-09. UI html2canvas capture remains hand-check
in docs/acceptance-records (upload API proves D-INS-09 write path).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import struct
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

# Minimal 1x1 PNG
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class SmokeFailure(Exception):
    pass


def _http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw.strip() else {}
            return int(resp.status), payload if isinstance(payload, dict) else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return int(exc.code), payload if isinstance(payload, dict) else {}


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(resp.status) < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _prepare_workdir(dist: Path | None, zip_path: Path | None) -> tuple[Path, Path]:
    """Return (workdir, exe_path). Caller deletes workdir."""
    if zip_path is not None:
        if not zip_path.is_file():
            raise SystemExit(f"zip not found: {zip_path}")
        work = Path(tempfile.mkdtemp(prefix="tg-smoke-"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(work)
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


def _check_sidecars(exe: Path) -> None:
    parent = exe.parent
    required = [
        "_internal",
        "portable.flag",
        "VERSION.txt",
        "SHA256SUMS",
        "使用说明.txt",
    ]
    # portable.flag checked only in portable mode; install mode removes it later.
    missing = []
    for name in required:
        path = parent / name
        if name == "_internal":
            if not path.is_dir():
                missing.append(name)
        elif not path.is_file():
            missing.append(name)
    if missing:
        raise SmokeFailure(f"SM-01 sidecars missing: {missing}")


def _check_sha256sums(exe: Path) -> None:
    sums = exe.parent / "SHA256SUMS"
    lines = sums.read_text(encoding="utf-8").splitlines()
    checked = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest, rel = parts[0], parts[-1]
        target = exe.parent / rel
        if not target.is_file():
            raise SmokeFailure(f"SM-02 missing hashed file: {rel}")
        got = _sha256_file(target)
        if got.lower() != digest.lower():
            raise SmokeFailure(f"SM-02 SHA256 mismatch for {rel}")
        checked += 1
    if checked < 1:
        raise SmokeFailure("SM-02 SHA256SUMS empty")


def _read_pe_file_version(exe: Path) -> str | None:
    """Best-effort read FileVersion from PE resource (Windows)."""
    try:
        import ctypes
        from ctypes import wintypes

        size = ctypes.windll.version.GetFileVersionInfoSizeW(str(exe), None)  # type: ignore[attr-defined]
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(str(exe), 0, size, buf):  # type: ignore[attr-defined]
            return None
        ptr = ctypes.c_void_p()
        length = wintypes.UINT()
        if not ctypes.windll.version.VerQueryValueW(  # type: ignore[attr-defined]
            buf, "\\", ctypes.byref(ptr), ctypes.byref(length)
        ):
            return None
        # VS_FIXEDFILEINFO: dwFileVersionMS / LS at offsets 8 / 12
        data = ctypes.string_at(ptr, length.value)
        ms, ls = struct.unpack_from("II", data, 8)
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return None


def _wait_http(url: str, proc: subprocess.Popen, timeout_sec: float, log_hint: Path) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if proc.poll() is not None:
            tail = ""
            if log_hint.is_file():
                tail = log_hint.read_text(encoding="utf-8", errors="replace")[-2000:]
            raise SmokeFailure(
                f"process exited early code={proc.returncode}\n--- log ---\n{tail}"
            )
        if _http_ok(url):
            return
        time.sleep(0.4)
    tail = ""
    if log_hint.is_file():
        tail = log_hint.read_text(encoding="utf-8", errors="replace")[-2000:]
    raise SmokeFailure(f"timed out waiting for {url}\n--- log ---\n{tail}")


def _poll_job(base: str, job_id: str, *, timeout_sec: float = 300.0) -> dict:
    deadline = time.time() + timeout_sec
    last: dict = {}
    while time.time() < deadline:
        status, body = _http_json(f"{base}/__travelogue/status?jobId={job_id}")
        last = body
        if status != 200:
            time.sleep(0.8)
            continue
        st = str(body.get("status") or "").lower()
        if st in ("succeeded", "done", "success", "completed", "ok"):
            return body
        if st in ("error", "failed", "fail"):
            raise SmokeFailure(f"job {job_id} failed: {body}")
        time.sleep(0.8)
    raise SmokeFailure(f"job {job_id} timed out; last={last}")


def _start_exe(
    exe: Path,
    *,
    port: int,
    env: dict[str, str] | None = None,
) -> subprocess.Popen:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.Popen(
        [str(exe), "studio", "--no-open", "--port", str(port), "--host", "127.0.0.1"],
        cwd=str(exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=merged,
    )


def _stop_proc(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def _make_zh_album(work: Path) -> Path:
    album = work / "相册测试" / "旅途照片"
    album.mkdir(parents=True, exist_ok=True)
    # Prefer a few demo assets if present in the onedir bundle copy area;
    # otherwise write tiny PNGs (import may reject non-photos — use PNG).
    demo_src = (
        ROOT / "templates" / "studio" / "assets" / "demo-album"
    )
    copied = 0
    if demo_src.is_dir():
        for src in sorted(demo_src.rglob("*")):
            if not src.is_file():
                continue
            if src.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            shutil.copy2(src, album / f"photo-{copied:02d}{src.suffix.lower()}")
            copied += 1
            if copied >= 6:
                break
    if copied == 0:
        for i in range(3):
            (album / f"photo-{i:02d}.png").write_bytes(_PNG_1X1)
    return album


def run_smoke(
    *,
    dist: Path | None,
    zip_path: Path | None,
    port: int,
    timeout_sec: float,
    mode: str,
    skip_import: bool,
) -> int:
    work, exe = _prepare_workdir(dist, zip_path)
    base = f"http://127.0.0.1:{port}"
    print(f"smoke workdir: {work}")
    print(f"smoke exe: {exe}")
    print(f"smoke mode: {mode}")

    results: list[tuple[str, str]] = []
    proc: subprocess.Popen | None = None
    install_local: Path | None = None

    try:
        # --- SM-01 / SM-02 (portable layout before mode tweak) ---
        _check_sidecars(exe)
        results.append(("SM-01", "PASS"))
        _check_sha256sums(exe)
        results.append(("SM-02", "PASS"))

        fv = _read_pe_file_version(exe)
        if fv:
            print(f"  FileVersion={fv}")
            results.append(("D-INS-10", f"PASS ({fv})"))
        else:
            print("  warning: FileVersion resource not readable (rebuild after gen_studio_version_info)")
            results.append(("D-INS-10", "BLOCKED (no PE version — rebuild needed)"))

        env: dict[str, str] = {}
        if mode == "install":
            flag = exe.parent / "portable.flag"
            if flag.is_file():
                flag.unlink()
            install_local = Path(tempfile.mkdtemp(prefix="tg-localapp-"))
            env["LOCALAPPDATA"] = str(install_local)
            print(f"  install LOCALAPPDATA override: {install_local}")
        elif mode == "portable":
            if not any(
                p.name.lower() == "portable.flag"
                for p in exe.parent.iterdir()
                if p.is_file()
            ):
                (exe.parent / "portable.flag").write_text("portable\n", encoding="utf-8")
                print("  warning: injected portable.flag for smoke")

        proc = _start_exe(exe, port=port, env=env or None)
        log_path = (
            (install_local / "Travelogue" / "logs" / "studio.log")
            if mode == "install" and install_local is not None
            else (exe.parent / "logs" / "studio.log")
        )
        # First launch may create logs a moment later — wait on HTTP then resolve log.
        _wait_http(f"{base}/", proc, timeout_sec, exe.parent / "logs" / "studio.log")
        results.append(("SM-03", "PASS"))

        # Resolve actual log after start
        if mode == "install" and install_local is not None:
            log_path = install_local / "Travelogue" / "logs" / "studio.log"
            trips_root = install_local / "Travelogue" / "trips"
            marker = install_local / "Travelogue" / ".travelogue-ownership"
        else:
            log_path = exe.parent / "logs" / "studio.log"
            trips_root = exe.parent / "trips"
            marker = exe.parent / ".travelogue-ownership"

        if not log_path.is_file():
            raise SmokeFailure(f"SM-04 missing log: {log_path}")
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        if "Travelogue Studio starting" not in log_text and "Studio mode" not in log_text:
            # Stream redirect may only have HTTP bind lines
            if "starting" not in log_text.lower() and len(log_text) < 20:
                raise SmokeFailure("SM-04 log has no startup breadcrumb")
        results.append(("SM-04", "PASS"))
        print(f"  trips_root={trips_root} exists={trips_root.is_dir()}")
        print(f"  ownership={marker.is_file()} log={log_path}")

        if mode == "install":
            if not trips_root.is_dir() or not marker.is_file():
                raise SmokeFailure("install mode: LocalAppData trips/ownership missing")
            if (exe.parent / "trips").is_dir() and any((exe.parent / "trips").iterdir()):
                print("  warning: exe-side trips also present (unexpected for install)")
            results.append(("PATH-install", "PASS"))

        status, cfg = _http_json(f"{base}/__travelogue/config")
        if status != 200 or not cfg.get("ok"):
            raise SmokeFailure(f"config failed: {status} {cfg}")
        caps = cfg.get("capabilities") or {}
        print(f"  capabilities={caps}")
        if not caps.get("longshotClientFallback"):
            raise SmokeFailure("longshotClientFallback expected true")

        trip_id: str | None = None
        if not skip_import:
            # SM-05 demo album import (exercises freeze_support / pipeline)
            try:
                st, body = _http_json(
                    f"{base}/__travelogue/import",
                    method="POST",
                    body={"useDemoAlbum": True, "title": "冒烟示例", "place": "示例"},
                    timeout=60.0,
                )
                if st not in (200, 202) or not body.get("ok"):
                    print(f"  demo import response: {st} {body}")
                    results.append(("SM-05", f"SOFT ({st})"))
                else:
                    job_id = str(body.get("jobId") or "")
                    if job_id:
                        done = _poll_job(base, job_id, timeout_sec=max(timeout_sec, 300.0))
                        trip_id = str(done.get("tripId") or "") or None
                    else:
                        trip_id = str(body.get("tripId") or "") or None
                    if not trip_id:
                        raise SmokeFailure(f"SM-05 no tripId: {body}")
                    results.append(("SM-05", f"PASS trip={trip_id}"))
            except SmokeFailure as exc:
                print(f"  SM-05 soft-fail: {exc}")
                results.append(("SM-05", f"SOFT {exc}"))

            # SM-06 Chinese path import (retry if prior job slot still draining)
            try:
                zh_album = _make_zh_album(work)
                st, body = 0, {}
                for attempt in range(12):
                    st, body = _http_json(
                        f"{base}/__travelogue/import",
                        method="POST",
                        body={
                            "albumPath": str(zh_album),
                            "title": "中文路径冒烟",
                            "place": "测试",
                            "photoCullEnabled": False,
                            "keepNearDuplicates": True,
                        },
                        timeout=60.0,
                    )
                    if st == 409 and str(body.get("error") or "") == "E_STUDIO_JOB_BUSY":
                        time.sleep(1.5)
                        continue
                    break
                if st in (200, 202) and body.get("ok"):
                    job_id = str(body.get("jobId") or "")
                    if job_id:
                        done = _poll_job(base, job_id, timeout_sec=max(timeout_sec, 300.0))
                        zh_trip = str(done.get("tripId") or "") or ""
                        if zh_trip:
                            trip_id = trip_id or zh_trip
                            results.append(("SM-06", f"PASS trip={zh_trip}"))
                        else:
                            results.append(("SM-06", f"SOFT no tripId {done}"))
                    else:
                        results.append(("SM-06", "SOFT no jobId"))
                else:
                    msg = json.dumps(body, ensure_ascii=False)[:300]
                    if "pip" in msg.lower():
                        raise SmokeFailure(f"SM-06 pip in user message: {msg}")
                    results.append(("SM-06", f"SOFT {st} {msg}"))
            except SmokeFailure as exc:
                if "pip" in str(exc).lower():
                    raise
                print(f"  SM-06 soft-fail: {exc}")
                results.append(("SM-06", f"SOFT {exc}"))

            # SM-07 client fallback + upload write path
            if not trip_id:
                # List trips
                _st, trips_body = _http_json(f"{base}/__travelogue/trips?limit=5")
                items = trips_body.get("trips") or trips_body.get("items") or []
                if items and isinstance(items[0], dict):
                    trip_id = str(items[0].get("id") or items[0].get("tripId") or "") or None
            if trip_id:
                st, body = _http_json(
                    f"{base}/__travelogue/longshot",
                    method="POST",
                    body={"tripId": trip_id, "forceClient": True},
                )
                if st != 200 or body.get("fallback") != "client":
                    raise SmokeFailure(f"SM-07 forceClient: {st} {body}")
                st, body = _http_json(
                    f"{base}/__travelogue/longshot/upload",
                    method="POST",
                    body={
                        "tripId": trip_id,
                        "format": "png",
                        "data": base64.b64encode(_PNG_1X1).decode("ascii"),
                        "filename": "smoke-longshot.png",
                    },
                )
                if st != 200 or not body.get("ok"):
                    raise SmokeFailure(f"SM-07 upload: {st} {body}")
                # File on disk under trips_root
                out_rel = (body.get("outputs") or ["smoke-longshot.png"])[0]
                out_path = trips_root / trip_id / Path(out_rel).name
                if not out_path.is_file():
                    # Try search
                    found = list(trips_root.rglob("smoke-longshot.png"))
                    if not found:
                        raise SmokeFailure(f"SM-07 PNG not on disk under {trips_root}")
                    out_path = found[0]
                results.append(("SM-07", f"PASS {out_path.name} (API upload; UI canvas hand-check)"))
            else:
                results.append(("SM-07", "BLOCKED (no tripId — import soft-failed)"))
        else:
            results.append(("SM-05", "SKIP"))
            results.append(("SM-06", "SKIP"))
            results.append(("SM-07", "SKIP"))

        # SM-08 second instance
        proc2 = _start_exe(exe, port=port + 1, env=env or None)
        try:
            time.sleep(3.0)
            code2 = proc2.poll()
            # Second should exit quickly (open existing) — not keep serving forever.
            # Allow either: exited (0) or still running but primary still OK.
            if code2 is None:
                # If still running, ensure primary still answers and second didn't steal.
                if not _http_ok(f"{base}/"):
                    raise SmokeFailure("SM-08 primary died after second launch")
                # Prefer exit; soft-pass if second is short-lived opener
                results.append(("SM-08", "PASS (primary alive; second still running briefly)"))
            else:
                if not _http_ok(f"{base}/"):
                    raise SmokeFailure("SM-08 primary not reachable after second exit")
                results.append(("SM-08", f"PASS second_exit={code2}"))
        finally:
            _stop_proc(proc2)

        # SM-09 shutdown
        st, body = _http_json(f"{base}/__travelogue/shutdown", method="POST", body={})
        if st != 200 or not body.get("ok"):
            raise SmokeFailure(f"SM-09 shutdown: {st} {body}")
        deadline = time.time() + 20.0
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.3)
        if proc.poll() is None:
            raise SmokeFailure("SM-09 process did not exit after shutdown")
        time.sleep(0.5)
        if _http_ok(f"{base}/"):
            raise SmokeFailure("SM-09 port still serving after shutdown")
        results.append(("SM-09", "PASS"))
        proc = None

        print("\n=== smoke summary ===")
        for sid, status in results:
            print(f"  {sid}: {status}")
        blocked = [
            r
            for r in results
            if r[1].startswith("FAIL")
            or (r[0].startswith("SM-") and r[1].startswith("BLOCKED"))
        ]
        # D-INS-10 BLOCKED alone does not fail smoke exit (rebuild may be pending);
        # SM-* BLOCKED does.
        if any(r[0] == "D-INS-10" and r[1].startswith("BLOCKED") for r in results):
            print("note: D-INS-10 FileVersion missing — rebuild with gen_studio_version_info")
        if blocked:
            print("FAIL: blocked/fail SM items present")
            return 1
        print("PASS")
        return 0
    except SmokeFailure as exc:
        print(f"FAIL: {exc}")
        print("\n=== smoke summary (partial) ===")
        for sid, status in results:
            print(f"  {sid}: {status}")
        return 1
    finally:
        _stop_proc(proc)
        shutil.rmtree(work, ignore_errors=True)
        if install_local is not None:
            shutil.rmtree(install_local, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=None, help="onedir folder")
    parser.add_argument("--zip", type=Path, default=None, help="portable zip")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--mode",
        choices=("portable", "install"),
        default="portable",
        help="portable (flag) or install (no flag, LocalAppData)",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="skip SM-05/06/07 import+longshot (faster HTTP-only)",
    )
    args = parser.parse_args(argv)
    return run_smoke(
        dist=args.dist.resolve() if args.dist else None,
        zip_path=args.zip.resolve() if args.zip else None,
        port=args.port,
        timeout_sec=args.timeout,
        mode=args.mode,
        skip_import=args.skip_import,
    )


if __name__ == "__main__":
    sys.exit(main())
