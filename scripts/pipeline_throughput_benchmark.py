"""Pipeline Throughput benchmark (M0 + P1 microbench).

Usage:
  python scripts/pipeline_throughput_benchmark.py --register-baseline --photos 100,250 --tier S2 --repeats 3
  python scripts/pipeline_throughput_benchmark.py --register-baseline --dry-run
  python scripts/pipeline_throughput_benchmark.py --run-microbench --photos 12 --repeats 2
  python scripts/pipeline_throughput_benchmark.py --run-microbench --photos 12 --compare-parallel
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "docs" / "acceptance-records" / "pipeline-throughput-perf-eval.json"
DEFAULT_CONFIG = ROOT / "docs" / "config-pipeline-throughput.example.yaml"
BASELINE_REPORT = ROOT / "docs" / "reports" / "pipeline-throughput-baseline.md"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _device_fingerprint(*, tier: str, note: str) -> dict[str, Any]:
    ram_gb = None
    try:
        import psutil  # type: ignore

        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        pass
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or platform.machine(),
        "ramGb": ram_gb,
        "tier": tier,
        "note": note,
    }


def _parse_photos(raw: str) -> list[int]:
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("photos list is empty")
    return [int(p) for p in parts]


def _load_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"record not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _register_baseline(
    record_path: Path,
    *,
    photos: list[int],
    tier: str,
    repeats: int,
    replace: bool,
    reason: str,
    dry_run: bool,
    note: str,
) -> dict[str, Any]:
    payload = _load_record(record_path)
    baseline = payload.setdefault("baseline", {})
    if isinstance(baseline, dict) and baseline.get("recordedAt") and not replace:
        raise SystemExit(
            "baseline already recorded; pass --replace-baseline with --reason to overwrite"
        )
    if replace and not reason.strip():
        raise SystemExit("--replace-baseline requires --reason")

    baseline.update(
        {
            "label": "P7-fastpath-serial-ingest",
            "recordedAt": _now(),
            "photoCount": photos[0] if photos else 100,
            "photoCounts": photos,
            "repeats": repeats,
            "parallel_ingest": False,
            "narrate_concurrency": 1,
            "deviceTier": tier,
            "replaceReason": reason.strip() if replace else None,
            "status": "skeleton-registered",
            "note": (
                "Metadata stamp for G-PT dogfood. Use --run-microbench for local "
                "ingest wall-clock samples (does not claim G-PT-01 thresholds)."
            ),
        }
    )
    payload["commit"] = _git_commit() or payload.get("commit") or ""
    payload["deviceTier"] = tier
    payload["deviceFingerprint"] = _device_fingerprint(tier=tier, note=note)
    payload["configSnapshot"] = str(DEFAULT_CONFIG.relative_to(ROOT)).replace("\\", "/")

    summary = {
        "mode": "register-baseline",
        "dryRun": dry_run,
        "record": str(record_path),
        "photos": photos,
        "tier": tier,
        "repeats": repeats,
        "replaced": replace,
        "baseline": {
            "recordedAt": baseline.get("recordedAt"),
            "photoCounts": baseline.get("photoCounts"),
            "status": baseline.get("status"),
        },
    }
    if dry_run:
        return summary

    record_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if BASELINE_REPORT.is_file():
        stamp = (
            f"\n\n<!-- register-baseline {_now()} tier={tier} photos={photos} "
            f"repeats={repeats} -->\n"
        )
        BASELINE_REPORT.write_text(
            BASELINE_REPORT.read_text(encoding="utf-8") + stamp,
            encoding="utf-8",
        )
    return summary


def _synth_album(root: Path, n: int) -> Path:
    from PIL import Image, ImageDraw

    album = root / "album"
    album.mkdir(parents=True, exist_ok=True)
    base_t = 1_700_000_000.0
    for i in range(n):
        img = Image.new("RGB", (800, 1000), (20 + (i * 11) % 200, 40, 70))
        draw = ImageDraw.Draw(img)
        for x in range(0, 800, 30):
            draw.line((x, 0, x, 1000), fill=(180, 180, 180))
        path = album / f"p{i:03d}.jpg"
        img.save(path, quality=88)
        os.utime(path, (base_t + i * 90, base_t + i * 90))
    return album


def _count_album_photos(album_dir: Path) -> int:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    return sum(1 for p in album_dir.iterdir() if p.is_file() and p.suffix.lower() in exts)


def _pt_bench_config(*, parallel: bool, workers: int, stages: str):
    """P7 fast-path + PT ingest toggle. Only parallel_ingest differs across arms."""
    from dataclasses import replace

    from travelogue.config import AppConfig

    cfg = AppConfig()
    cfg.cull.enabled = False
    vision_on = stages == "pipeline"
    return replace(
        cfg,
        vision=replace(
            cfg.vision,
            enabled="true" if vision_on else "false",
            batch_size=16,
            session_singleton=True,
            prefer_web_derivative=True,
            batch_auto_tune=True,
            dynamic_backoff=True,
        ),
        pipeline=replace(
            cfg.pipeline,
            parallel_embed=vision_on,
            parallel_embed_chunk=32,
            parallel_ingest=parallel,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=workers if parallel else 1,
            persist_every_n=8,
        ),
        ingest=replace(cfg.ingest, webp_method=4, shared_color_thumb_px=32),
        clustering=replace(cfg.clustering, deterministic=True, force_recluster=False),
        layout=replace(
            cfg.layout,
            scoring=replace(
                cfg.layout.scoring,
                skip_duplicate_signatures=True,
                incremental=False,
            ),
        ),
    )


def _time_pipeline_once(
    album: Path,
    *,
    parallel: bool,
    workers: int = 2,
    stages: str = "ingest",
    work_root: Path | None = None,
) -> dict[str, Any]:
    """Time ingest (+ optional cluster/curate). Fair A/B: only parallel_ingest differs."""
    from travelogue.config import app_config_scope
    from travelogue.media.ingest import ingest_into_trip
    from travelogue.services.trip_factory import create_trip

    cfg = _pt_bench_config(parallel=parallel, workers=workers, stages=stages)
    own_tmp = work_root is None
    td_ctx = tempfile.TemporaryDirectory(prefix="pt-bench-") if own_tmp else None
    try:
        root = Path(td_ctx.name) if td_ctx else work_root
        assert root is not None
        trips = root / "trips"
        trip_json = create_trip("pt-bench", trips, title="pt-bench", export_layout="auto")
        trip_dir = trip_json.parent
        trip = json.loads(trip_json.read_text(encoding="utf-8"))
        metrics: dict[str, Any] = {"parallel": parallel}

        with app_config_scope(cfg):
            parallel_embed = None
            if stages == "pipeline" and cfg.pipeline.parallel_embed:
                from travelogue.vision.parallel_embed import ParallelEmbedCoordinator

                parallel_embed = ParallelEmbedCoordinator(
                    trip_dir,
                    cfg=cfg,
                    chunk_size=cfg.pipeline.parallel_embed_chunk,
                )

            def _on_asset_added(entry: dict) -> None:
                if parallel_embed is not None:
                    parallel_embed.offer(entry)

            t0 = time.perf_counter()
            result = ingest_into_trip(
                trip,
                trip_dir,
                from_dir=album,
                dedupe=True,
                app_cfg=cfg,
                resume_ingest=False,
                min_assets=1,
                on_asset_added=_on_asset_added if parallel_embed is not None else None,
            )
            if parallel_embed is not None:
                parallel_embed.finish()
            metrics["ingestMs"] = round((time.perf_counter() - t0) * 1000.0, 1)
            metrics["added"] = int(result.added)
            metrics["assets"] = len(trip.get("assets") or [])
            metrics["ingestWorkers"] = int(result.stats.get("ingestWorkers") or 1)

            if stages == "pipeline":
                from travelogue.curation.clustering import run_clustering_layer
                from travelogue.curation.curate import run_curate

                t1 = time.perf_counter()
                run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
                metrics["clusterMs"] = round((time.perf_counter() - t1) * 1000.0, 1)
                embed_stats = (
                    ((trip.get("curation") or {}).get("clustering") or {}).get("embedStats") or {}
                )
                metrics["embedMs"] = float(embed_stats.get("elapsedMs") or metrics["clusterMs"])

                t2 = time.perf_counter()
                run_curate(
                    trip, export_layout="auto", apply_layout=True, trip_dir=trip_dir, cfg=cfg
                )
                metrics["curateMs"] = round((time.perf_counter() - t2) * 1000.0, 1)
                metrics["totalMs"] = round(
                    metrics["ingestMs"] + metrics["clusterMs"] + metrics["curateMs"], 1
                )
            else:
                metrics["totalMs"] = metrics["ingestMs"]
        return metrics
    finally:
        if td_ctx is not None:
            td_ctx.cleanup()


def _summarize_arm(runs: list[dict[str, Any]], key: str = "ingestMs") -> dict[str, Any]:
    samples = [float(r[key]) for r in runs]
    return {
        "samplesMs": samples,
        "medianMs": round(statistics.median(samples), 1),
        "meanMs": round(statistics.fmean(samples), 1),
        "last": runs[-1],
    }


def _run_microbench(
    *,
    photos: int,
    repeats: int,
    compare_parallel: bool,
    workers: int,
    write_record: Path | None,
    dry_run: bool,
    album_dir: Path | None = None,
    stages: str = "ingest",
    work_dir: Path | None = None,
) -> dict[str, Any]:
    own_album_tmp = None
    if album_dir is None:
        own_album_tmp = tempfile.TemporaryDirectory(prefix="pt-album-")
        album = _synth_album(Path(own_album_tmp.name), photos)
        album_label = f"synthetic:{photos}"
        photo_count = photos
    else:
        album = album_dir.resolve()
        if not album.is_dir():
            raise FileNotFoundError(f"album not found: {album}")
        photo_count = _count_album_photos(album)
        if photo_count < 1:
            raise FileNotFoundError(f"no photos in album: {album}")
        album_label = str(album)

    try:
        work_root = work_dir or (ROOT / ".cache" / "pt-bench")
        work_root.mkdir(parents=True, exist_ok=True)

        serial_runs: list[dict[str, Any]] = []
        for i in range(repeats):
            serial_runs.append(
                _time_pipeline_once(
                    album,
                    parallel=False,
                    workers=workers,
                    stages=stages,
                    work_root=work_root / f"serial-{i}",
                )
            )
        summary: dict[str, Any] = {
            "mode": "run-microbench",
            "dryRun": dry_run,
            "album": album_label,
            "photos": photo_count,
            "repeats": repeats,
            "stages": stages,
            "serial": _summarize_arm(serial_runs, "ingestMs"),
            "note": (
                "Same-album A/B: only pipeline.parallel_ingest differs. "
                "stages=ingest → G-PT-02 direction; stages=pipeline → ingest+cluster+curate "
                "(no narrate/render; stub LLM not timed)."
            ),
        }
        if stages == "pipeline":
            summary["serialTotal"] = _summarize_arm(serial_runs, "totalMs")

        if compare_parallel:
            parallel_runs = [
                _time_pipeline_once(
                    album,
                    parallel=True,
                    workers=workers,
                    stages=stages,
                    work_root=work_root / f"parallel-{i}",
                )
                for i in range(repeats)
            ]
            med_s = summary["serial"]["medianMs"]
            arm = _summarize_arm(parallel_runs, "ingestMs")
            drop = None if med_s <= 0 else round((med_s - arm["medianMs"]) / med_s, 4)
            summary["parallel"] = {
                **arm,
                "workers": workers,
                "dropVsSerialIngest": drop,
            }
            if stages == "pipeline":
                tot = _summarize_arm(parallel_runs, "totalMs")
                med_st = summary["serialTotal"]["medianMs"]
                drop_t = None if med_st <= 0 else round((med_st - tot["medianMs"]) / med_st, 4)
                summary["parallelTotal"] = {**tot, "dropVsSerialTotal": drop_t}
    finally:
        if own_album_tmp is not None:
            own_album_tmp.cleanup()

    if write_record and not dry_run:
        payload = _load_record(write_record)
        payload["microbench"] = {
            "recordedAt": _now(),
            "commit": _git_commit(),
            "deviceFingerprint": _device_fingerprint(tier="local", note="album-compare"),
            **{k: v for k, v in summary.items() if k not in ("mode", "dryRun")},
        }
        write_record.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        summary["record"] = str(write_record)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline Throughput benchmark")
    parser.add_argument(
        "--register-baseline",
        action="store_true",
        help="stamp baseline metadata into perf-eval record (P7 serial / PT flags off)",
    )
    parser.add_argument(
        "--run-microbench",
        action="store_true",
        help="time ingest (synthetic or --album-dir); local sampling",
    )
    parser.add_argument(
        "--album-dir",
        type=Path,
        default=None,
        help="real album directory for same-folder A/B (overrides synthetic --photos)",
    )
    parser.add_argument(
        "--stages",
        choices=("ingest", "pipeline"),
        default="ingest",
        help="ingest only, or ingest+cluster+curate (no narrate/render)",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="scratch dir for trip outputs (default: .cache/pt-bench)",
    )
    parser.add_argument(
        "--compare-parallel",
        action="store_true",
        help="with --run-microbench, also time parallel_ingest=true",
    )
    parser.add_argument(
        "--write-record",
        action="store_true",
        help="persist microbench block into --record JSON",
    )
    parser.add_argument(
        "--replace-baseline",
        action="store_true",
        help="allow overwriting an existing baseline (requires --reason)",
    )
    parser.add_argument("--reason", default="", help="reason when replacing baseline")
    parser.add_argument(
        "--photos",
        type=_parse_photos,
        default=_parse_photos("100,250"),
        help="comma-separated photo counts (microbench uses first value when no --album-dir)",
    )
    parser.add_argument("--tier", default="S2", help="device tier label (S1/S2/S3)")
    parser.add_argument("--repeats", type=int, default=3, help="repeat count for timed runs")
    parser.add_argument("--workers", type=int, default=2, help="parallel ingest workers")
    parser.add_argument("--dry-run", action="store_true", help="print plan without writing")
    parser.add_argument("--note", default="", help="optional device fingerprint note")
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()

    if not args.register_baseline and not args.run_microbench:
        parser.error("specify --register-baseline and/or --run-microbench")

    summaries: list[dict[str, Any]] = []
    try:
        if args.register_baseline:
            summaries.append(
                _register_baseline(
                    args.record,
                    photos=args.photos,
                    tier=args.tier,
                    repeats=args.repeats,
                    replace=args.replace_baseline,
                    reason=args.reason,
                    dry_run=args.dry_run,
                    note=args.note,
                )
            )
        if args.run_microbench:
            summaries.append(
                _run_microbench(
                    photos=int(args.photos[0]),
                    repeats=max(1, int(args.repeats)),
                    compare_parallel=bool(args.compare_parallel),
                    workers=max(1, int(args.workers)),
                    write_record=args.record if args.write_record else None,
                    dry_run=args.dry_run,
                    album_dir=args.album_dir,
                    stages=str(args.stages),
                    work_dir=args.work_dir,
                )
            )
    except FileNotFoundError as exc:
        print(json.dumps({"overallPassed": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps(summaries if len(summaries) > 1 else summaries[0], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
