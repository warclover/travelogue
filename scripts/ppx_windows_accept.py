#!/usr/bin/env python3
"""Windows AC-PPX-03 / 08 / 10 acceptance runner (not CI)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

W0 = {
    "demo-49551086fe": {"n": 31, "tier": "high", "workers": 4},
    "demo-65db8fd377": {"n": 57, "tier": "high", "workers": 4},
    "demo-81d3442e92": {"n": 121, "tier": "high", "workers": 4},
    "demo-e52494839a": {"n": 134, "tier": "mid", "workers": 8},
}


def _machine() -> dict:
    info: dict = {
        "os": sys.platform,
        "cpuCount": os.cpu_count(),
    }
    try:
        out = subprocess.check_output(
            ["wmic", "cpu", "get", "Name", "/value"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            if line.startswith("Name="):
                info["cpu"] = line.split("=", 1)[1].strip()
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["wmic", "computersystem", "get", "TotalPhysicalMemory", "/value"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            if line.startswith("TotalPhysicalMemory="):
                raw = int(line.split("=", 1)[1].strip() or 0)
                info["ramGb"] = round(raw / (1024**3), 1)
    except Exception:
        pass
    try:
        ps = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-MpComputerStatus).RealTimeProtectionEnabled",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        info["defenderRealtime"] = ps.lower() == "true"
    except Exception:
        info["defenderRealtime"] = None
    cfg = ROOT / "config.yaml"
    text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
    info["configYamlExists"] = cfg.is_file()
    info["configHasParallelIngestKey"] = "parallel_ingest" in text
    info["frozenOnedir"] = False
    return info


def _python_procs() -> list[dict]:
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" "
                "| Select-Object ProcessId,ParentProcessId,CommandLine "
                "| ConvertTo-Json -Compress",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return []
    if not out:
        return []
    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]
    rows = []
    for row in data:
        rows.append(
            {
                "pid": int(row.get("ProcessId") or 0),
                "ppid": int(row.get("ParentProcessId") or 0),
                "cmd": str(row.get("CommandLine") or ""),
            }
        )
    return rows


def _write_yaml(path: Path, trips_dir: Path, *, workers: int = 2, min_photos: int = 8) -> None:
    path.write_text(
        "\n".join(
            [
                f"trips_dir: {trips_dir.as_posix()}",
                "vision:",
                "  enabled: false",
                "  preload_on_folder_pick: false",
                "pipeline:",
                "  parallel_ingest: true",
                f"  parallel_ingest_workers: {workers}",
                f"  parallel_ingest_min_photos: {min_photos}",
                "  parallel_embed: false",
                "  deferred_derivatives: true",
                "ingest:",
                "  detect_faces: false",
                "  generate_crops: false",
                "  portrait_analyze: false",
                "  webp_method: 0",
                "  webp_widths: [800, 1600]",
                "  webp_ingest_widths: [800]",
                "  min_edge_px: 320",
                "aesthetic:",
                "  enabled: false",
                "  ml_calibrate: false",
                "  warm_learned_on_ingest: false",
                "llm:",
                "  provider: stub",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_cancel(work: Path) -> dict:
    from PIL import Image

    from travelogue.web.studio_subprocess import ImportSubprocess

    album = work / "album"
    trips = work / "trips"
    album.mkdir(parents=True)
    trips.mkdir()
    for i in range(16):
        p = album / f"p{i:02d}.jpg"
        Image.new("RGB", (640, 800), (20 + i * 10, 40, 80)).save(p, quality=85)
    cfg = work / "ppx-cancel.yaml"
    _write_yaml(cfg, trips, workers=2, min_photos=8)
    before = {r["pid"] for r in _python_procs()}
    handle = ImportSubprocess(
        {
            "albumPath": str(album),
            "tripsDir": str(trips),
            "tripId": "ppx-cancel-w1",
            "title": "PPX 取消抽检",
            "place": "测试",
            "host": "127.0.0.1",
            "port": 8766,
            "configPath": str(cfg),
            "dedupe": False,
            "forceStub": True,
            "photoCullEnabled": False,
            "keepNearDuplicates": True,
            "stopAfter": "structure",
        }
    )
    handle.start()
    import_pid = int(handle._process.pid or 0)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 8.0 and handle.alive:
        if any(r["ppid"] == import_pid for r in _python_procs()):
            break
        time.sleep(0.2)
    time.sleep(0.6)
    mid = [r for r in _python_procs() if r["pid"] == import_pid or r["ppid"] == import_pid]
    handle.cancel()
    handle.join(timeout=12)
    time.sleep(1.0)
    after = [
        r
        for r in _python_procs()
        if r["pid"] not in before
        and (
            r["pid"] == import_pid
            or r["ppid"] == import_pid
            or "ppx-cancel-w1" in r["cmd"]
            or str(work).replace("\\", "\\\\") in r["cmd"]
        )
    ]
    leftover_dirs = []
    trip_dir = trips / "ppx-cancel-w1"
    for name in (".ingest-partial", ".materialize-partial"):
        p = trip_dir / name
        if p.exists():
            leftover_dirs.append(str(p))
    return {
        "importPid": import_pid,
        "aliveAfterCancel": handle.alive,
        "childrenSeenMid": len(mid),
        "orphanAfter": after,
        "leftoverDirs": leftover_dirs,
        "ok": (not handle.alive) and not after and not leftover_dirs,
    }


def run_oom36(work: Path) -> dict:
    from PIL import Image

    from travelogue.config import AppConfig, IngestConfig, PipelineConfig, VisionConfig
    from travelogue.media.ingest import ingest_into_trip
    from travelogue.services.trip_factory import create_trip

    album = work / "album36"
    album.mkdir(parents=True)
    trips = work / "trips36"
    trips.mkdir()
    t_make = time.monotonic()
    for i in range(4):
        img = Image.new("RGB", (7360, 4912), (12 + i * 20, 40, 70))
        img.save(album / f"big{i}.jpg", quality=70)
        img.close()
    make_s = round(time.monotonic() - t_make, 1)
    cfg = AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_workers=10,
            parallel_ingest_min_photos=4,
            deferred_derivatives=True,
            parallel_embed=False,
        ),
        ingest=IngestConfig(
            detect_faces=False,
            generate_crops=False,
            webp_method=0,
            webp_widths=(800, 1600),
            webp_ingest_widths=(800,),
            min_edge_px=320,
        ),
        vision=VisionConfig(enabled="false"),
    )
    trip_json = create_trip("ppx-36mp", trips, title="36mp", cfg=cfg)
    t0 = time.monotonic()
    try:
        result = ingest_into_trip(
            json.loads(trip_json.read_text(encoding="utf-8")),
            trip_json.parent,
            from_dir=album,
            app_cfg=cfg,
            min_assets=1,
            dedupe=False,
        )
        elapsed = round(time.monotonic() - t0, 1)
        stats = result.stats or {}
        leftover = (trip_json.parent / ".ingest-partial").exists()
        return {
            "makeSec": make_s,
            "elapsedSec": elapsed,
            "added": result.added,
            "workers": stats.get("ingestWorkers"),
            "requested": stats.get("ingestWorkersRequested"),
            "downscaled": bool(stats.get("ingestWorkersDownscaled")),
            "downscaleReason": stats.get("ingestWorkersDownscaleReason"),
            "median": stats.get("medianLongEdgePx") or stats.get("ingestMedianLongEdgePx"),
            "fallback": stats.get("ingestParallelFallback"),
            "leftoverPartial": leftover,
            "ok": (
                result.added >= 4
                and int(stats.get("ingestWorkers") or 0) <= 4
                and bool(stats.get("ingestWorkersDownscaled"))
                and not leftover
                and stats.get("ingestParallelFallback") is not True
            ),
        }
    except MemoryError as exc:
        return {"ok": False, "error": f"MemoryError:{exc}", "makeSec": make_s}


def _album_root(trip_id: str) -> Path:
    trip = json.loads((ROOT / "trips" / trip_id / "trip.json").read_text(encoding="utf-8"))
    for asset in trip.get("assets") or []:
        ref = asset.get("sourceRef") if isinstance(asset, dict) else None
        if isinstance(ref, dict) and ref.get("albumRoot"):
            return Path(str(ref["albumRoot"]))
    raise FileNotFoundError(trip_id)


def _app_cfg(*, parallel: bool, workers: int, max_photos: int):
    from travelogue.config import (
        AestheticConfig,
        AppConfig,
        IngestConfig,
        PipelineConfig,
        VisionConfig,
    )

    return AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=parallel,
            parallel_ingest_workers=workers if parallel else 1,
            parallel_ingest_min_photos=2,
            deferred_derivatives=True,
            parallel_embed=False,
        ),
        ingest=IngestConfig(
            detect_faces=False,
            generate_crops=False,
            webp_method=2,
            webp_widths=(800, 1600, 2400),
            webp_ingest_widths=(800, 1600),
            min_edge_px=320,
            max_photos=max_photos,
        ),
        vision=VisionConfig(enabled="false"),
        aesthetic=AestheticConfig(enabled=False, ml_calibrate=False, warm_learned_on_ingest=False),
    )


def _run_ingest_materialize(
    *,
    trip_id: str,
    album: Path,
    work: Path,
    tag: str,
    parallel: bool,
    workers: int,
    max_photos: int,
) -> dict:
    from travelogue.media.derivatives import ensure_derivatives_for_trip, resolve_materialize_workers
    from travelogue.media.ingest import ingest_into_trip
    from travelogue.services.trip_factory import create_trip

    cfg = _app_cfg(parallel=parallel, workers=workers, max_photos=max_photos)
    slug = f"ppx-bench-{trip_id[-6:]}-{tag}"
    trips = work / "trips"
    trips.mkdir(parents=True, exist_ok=True)
    dest = trips / slug
    if dest.exists():
        shutil.rmtree(dest)
    trip_json = create_trip(slug, trips, title=slug, cfg=cfg)
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    t0 = time.monotonic()
    ingest = ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=cfg,
        min_assets=1,
        dedupe=False,
        max_photos=max_photos,
    )
    ingest_s = round(time.monotonic() - t0, 1)
    ids = [a["id"] for a in trip.get("assets") or [] if isinstance(a, dict) and a.get("id")]
    picked = ids[: min(32, len(ids))]
    if picked:
        trip["coverAssetId"] = picked[0]
        trip["chapters"] = [{"items": [{"assetId": i} for i in picked]}]
    if not parallel:
        orig = resolve_materialize_workers
        import travelogue.media.derivatives as der

        der.resolve_materialize_workers = lambda **_k: 1  # type: ignore[method-assign]
    else:
        orig = None
        der = None
    t1 = time.monotonic()
    try:
        mat = ensure_derivatives_for_trip(trip, trip_json.parent, app_cfg=cfg)
    finally:
        if der is not None and orig is not None:
            der.resolve_materialize_workers = orig
    mat_s = round(time.monotonic() - t1, 1)
    stats = ingest.stats or {}
    return {
        "tag": tag,
        "tripId": trip_id,
        "parallel": parallel,
        "workersPinned": workers,
        "added": ingest.added,
        "ingestSec": ingest_s,
        "materializeSec": mat_s,
        "ingestWorkers": stats.get("ingestWorkers"),
        "fallback": stats.get("ingestParallelFallback"),
        "reason": stats.get("ingestParallelFallbackReason"),
        "median": stats.get("medianLongEdgePx") or stats.get("ingestMedianLongEdgePx"),
        "downscaled": bool(stats.get("ingestWorkersDownscaled")),
        "matWorkers": getattr(mat, "workers", None),
        "widthsWritten": mat.widths_written,
        "matErrors": list(mat.errors[:3]),
    }


def run_bench(work: Path, *, only: str | None = None) -> list[dict]:
    rows = []
    for trip_id, meta in W0.items():
        if only and only not in (trip_id, str(meta["n"])):
            continue
        album = _album_root(trip_id)
        if not album.is_dir():
            rows.append({"tripId": trip_id, "ok": False, "error": f"missing album {album}"})
            continue
        serial = _run_ingest_materialize(
            trip_id=trip_id,
            album=album,
            work=work,
            tag="serial",
            parallel=False,
            workers=1,
            max_photos=meta["n"],
        )
        par = _run_ingest_materialize(
            trip_id=trip_id,
            album=album,
            work=work,
            tag=f"par{meta['workers']}",
            parallel=True,
            workers=meta["workers"],
            max_photos=meta["n"],
        )
        ingest_x = (
            round(serial["ingestSec"] / par["ingestSec"], 2) if par["ingestSec"] else None
        )
        mat_x = (
            round(serial["materializeSec"] / par["materializeSec"], 2)
            if par["materializeSec"]
            else None
        )
        e2e_serial = serial["ingestSec"] + serial["materializeSec"]
        e2e_par = par["ingestSec"] + par["materializeSec"]
        drop = round(1.0 - (e2e_par / e2e_serial), 3) if e2e_serial else None
        rows.append(
            {
                "tripId": trip_id,
                "n": meta["n"],
                "tier": meta["tier"],
                "album": str(album),
                "serial": serial,
                "parallel": par,
                "ingestSpeedup": ingest_x,
                "materializeSpeedup": mat_x,
                "e2eIngestMatDrop": drop,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--skip-cancel", action="store_true")
    parser.add_argument("--skip-oom", action="store_true")
    parser.add_argument("--skip-bench", action="store_true")
    parser.add_argument("--only", default=None, help="trip id or photo count")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)
    work = args.work or Path(os.environ.get("TEMP", ".")) / f"ppx-accept-{int(time.time())}"
    work.mkdir(parents=True, exist_ok=True)
    report: dict = {"work": str(work), "machine": _machine(), "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if not args.skip_cancel:
        print("AC-PPX-03 cancel…", flush=True)
        report["cancel"] = run_cancel(work / "cancel")
        print(json.dumps(report["cancel"], ensure_ascii=False), flush=True)
    if not args.skip_oom:
        print("AC-PPX-08 36MP…", flush=True)
        report["oom36"] = run_oom36(work / "oom")
        print(json.dumps(report["oom36"], ensure_ascii=False), flush=True)
    if not args.skip_bench:
        print("AC-PPX-10 bench…", flush=True)
        report["bench"] = run_bench(work / "bench", only=args.only)
        print(json.dumps(report["bench"], ensure_ascii=False, indent=2), flush=True)
    report["endedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out = args.json_out or (work / "ppx-accept.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out, flush=True)
    cancel_ok = report.get("cancel", {}).get("ok", True)
    oom_ok = report.get("oom36", {}).get("ok", True)
    return 0 if cancel_ok and oom_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
