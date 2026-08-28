"""Deferred WebP derivative materialization (PRD-PIPELINE-PERF-V1 · R2.1/R2.2).

``srcset`` only lists files on disk. Planned widths live in ``asset.derivedPlan``.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import shutil
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, IngestConfig, get_config
from travelogue.media.image_ops import export_webp_variants, focal_from_asset

DERIVED_PLAN_VERSION = "ppf-v1"


def build_derived_plan(
    *,
    planned_widths: tuple[int, ...] | list[int],
    ready_widths: tuple[int, ...] | list[int],
    status: str | None = None,
) -> dict[str, Any]:
    planned = sorted({int(w) for w in planned_widths if int(w) > 0})
    ready = sorted({int(w) for w in ready_widths if int(w) > 0 and int(w) in planned})
    if status is None:
        if ready == planned:
            status = "ready"
        elif not ready:
            status = "pending"
        else:
            status = "partial"
    return {
        "version": DERIVED_PLAN_VERSION,
        "plannedWidths": planned,
        "readyWidths": ready,
        "status": status,
    }


def sync_derived_plan_from_srcset(
    asset: dict,
    *,
    planned_widths: tuple[int, ...] | list[int],
) -> dict[str, Any]:
    have = [
        int(e.get("width") or 0)
        for e in (asset.get("srcset") or [])
        if isinstance(e, dict)
    ]
    plan = build_derived_plan(planned_widths=planned_widths, ready_widths=have)
    asset["derivedPlan"] = plan
    return plan


def effective_ingest_widths(cfg: IngestConfig, *, deferred: bool) -> tuple[int, ...]:
    """Widths written during ingest."""
    from travelogue.media.ingest_widths import effective_ingest_widths as _impl

    return _impl(cfg, deferred=deferred)


def selected_asset_ids(trip: dict) -> set[str]:
    """Assets that appear in cover / moment / closing / chapters / screens."""
    ids: set[str] = set()
    for key in ("coverAssetId", "momentAssetId"):
        raw = trip.get(key)
        if isinstance(raw, str) and raw.strip():
            ids.add(raw.strip())
    curation = trip.get("curation")
    if isinstance(curation, dict):
        closing = curation.get("closingAssetId")
        if isinstance(closing, str) and closing.strip():
            ids.add(closing.strip())
        # exportLayout=auto · web/mobile covers may differ from root coverAssetId
        cover_by = curation.get("coverByLayout")
        if isinstance(cover_by, dict):
            for slot in cover_by.values():
                if isinstance(slot, str) and slot.strip():
                    ids.add(slot.strip())
    meta = trip.get("meta")
    if isinstance(meta, dict):
        # Legacy diptych (and any dual-panel opening) secondary asset
        secondary = meta.get("coverSecondaryAssetId")
        if isinstance(secondary, str) and secondary.strip():
            ids.add(secondary.strip())
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        for item in ch.get("items") or []:
            if not isinstance(item, dict):
                continue
            aid = item.get("assetId")
            if isinstance(aid, str) and aid.strip():
                ids.add(aid.strip())
            for sub in item.get("assetIds") or []:
                if isinstance(sub, str) and sub.strip():
                    ids.add(sub.strip())
        for screen in ch.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            for slot in screen.get("slots") or []:
                if not isinstance(slot, dict):
                    continue
                aid = slot.get("assetId")
                if isinstance(aid, str) and aid.strip():
                    ids.add(aid.strip())
    return ids


def asset_ids_needing_materialize(
    trip: dict,
    *,
    asset_ids: set[str] | None = None,
    planned_widths: tuple[int, ...] | list[int] | None = None,
) -> list[str]:
    """Selected (or explicit) asset ids that still miss planned WebP widths."""
    planned = tuple(
        int(w)
        for w in (
            planned_widths
            if planned_widths is not None
            else (get_config().ingest.webp_widths or (800, 1600, 2400, 3200))
        )
    )
    wanted = asset_ids if asset_ids is not None else selected_asset_ids(trip)
    by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and a.get("type", "image") == "image"
    }
    missing: list[str] = []
    for aid in sorted(wanted):
        asset = by_id.get(aid)
        if asset is None:
            continue
        if missing_planned_widths(asset, planned_widths=planned):
            missing.append(aid)
    return missing


# MF-09 · sync budget for refine swap (≤3 assets); larger sets go background.
ON_DEMAND_SYNC_MAX_ASSETS = 3


@dataclass
class OnDemandMaterializeResult:
    mode: str  # sync | async | noop
    asset_ids: list[str] = field(default_factory=list)
    preparing_count: int = 0
    sync_result: MaterializeResult | None = None
    elapsed_ms: float = 0.0


_on_demand_lock = threading.Lock()
_on_demand_threads: dict[str, threading.Thread] = {}
_on_demand_pending: dict[str, set[str]] = {}


def _trip_key(trip_dir: Path) -> str:
    try:
        return str(trip_dir.resolve())
    except OSError:
        return str(trip_dir)


def is_on_demand_alive(trip_dir: Path) -> bool:
    """True when an on-demand materialize thread is alive for ``trip_dir``."""
    key = _trip_key(trip_dir)
    with _on_demand_lock:
        thread = _on_demand_threads.get(key)
        return thread is not None and thread.is_alive()


def is_on_demand_alive_for_trip_id(trip_id: str) -> bool:
    """Busy probe by trip folder name (CQA AC-10b · extends ``is_trip_busy``)."""
    tid = (trip_id or "").strip()
    if not tid:
        return False
    with _on_demand_lock:
        for key, thread in _on_demand_threads.items():
            if thread is None or not thread.is_alive():
                continue
            if Path(key).name == tid:
                return True
    return False


def _bump_on_demand_telemetry(trip: dict, *, count: int) -> None:
    pipe = trip.setdefault("pipeline", {})
    timings = dict(pipe.get("timings") or {})
    timings["derivativesOnDemandCount"] = float(
        timings.get("derivativesOnDemandCount") or 0.0
    ) + float(count)
    pipe["timings"] = timings


def materialize_on_demand(
    trip: dict,
    trip_dir: Path,
    *,
    asset_ids: set[str] | None = None,
    app_cfg: AppConfig | None = None,
    sync_max_assets: int = ON_DEMAND_SYNC_MAX_ASSETS,
    persist: bool = True,
) -> OnDemandMaterializeResult:
    """MF-09 · refine/curate on-demand materialize.

    ≤ ``sync_max_assets`` missing assets: synchronous ensure (≤3s budget intent).
    More: background thread + ``pipeline.derivativesPreparing`` for FE badge.
    """
    resolved = app_cfg or get_config()
    if not resolved.pipeline.deferred_derivatives:
        return OnDemandMaterializeResult(mode="noop")
    planned = tuple(int(w) for w in resolved.ingest.webp_widths)
    need = asset_ids_needing_materialize(
        trip,
        asset_ids=asset_ids,
        planned_widths=planned,
    )
    if not need:
        pipe = trip.setdefault("pipeline", {})
        if pipe.get("derivativesPreparing"):
            pipe["derivativesPreparing"] = 0
        return OnDemandMaterializeResult(mode="noop")

    _bump_on_demand_telemetry(trip, count=len(need))
    t0 = time.monotonic()
    if len(need) <= int(sync_max_assets):
        sync = ensure_derivatives_for_trip(
            trip,
            trip_dir,
            app_cfg=resolved,
            asset_ids=set(need),
            mark_unselected_skipped=False,
        )
        pipe = trip.setdefault("pipeline", {})
        pipe["derivativesPreparing"] = 0
        if not sync.errors:
            still = asset_ids_needing_materialize(
                trip, asset_ids=asset_ids, planned_widths=planned
            )
            pipe["derivativesStatus"] = "ready" if not still else "preview"
        elapsed = round((time.monotonic() - t0) * 1000.0, 2)
        if persist:
            _persist_trip_json(trip_dir, trip)
        return OnDemandMaterializeResult(
            mode="sync",
            asset_ids=need,
            preparing_count=0,
            sync_result=sync,
            elapsed_ms=elapsed,
        )

    pipe = trip.setdefault("pipeline", {})
    pipe["derivativesPreparing"] = len(need)
    pipe["derivativesStatus"] = "preview"
    if persist:
        _persist_trip_json(trip_dir, trip)

    trip_key = _trip_key(trip_dir)
    need_set = set(need)

    def _bg() -> None:
        try:
            while True:
                with _on_demand_lock:
                    batch = set(_on_demand_pending.get(trip_key) or ())
                    _on_demand_pending[trip_key] = set()
                if not batch:
                    break
                if not trip_dir.is_dir():
                    return
                result = ensure_derivatives_for_trip(
                    trip,
                    trip_dir,
                    app_cfg=resolved,
                    asset_ids=batch,
                    mark_unselected_skipped=False,
                )
                if not trip_dir.is_dir():
                    return
                pipe2 = trip.setdefault("pipeline", {})
                if result.errors:
                    pipe2["derivativesStatus"] = "error"
                    pipe2["derivativesError"] = "; ".join(
                        str(e) for e in result.errors[:3]
                    )[:240]
                still = asset_ids_needing_materialize(
                    trip, asset_ids=batch, planned_widths=planned
                )
                with _on_demand_lock:
                    more = bool(_on_demand_pending.get(trip_key))
                if not more:
                    pipe2["derivativesPreparing"] = 0
                    if not result.errors:
                        pipe2["derivativesStatus"] = "ready" if not still else "preview"
                    if persist:
                        _persist_trip_json(trip_dir, trip)
        except OSError:
            # PDG · directory may vanish mid-flight during delete rename
            return
        except Exception as exc:  # noqa: BLE001 — surface to trip pipeline for UI
            try:
                pipe2 = trip.setdefault("pipeline", {})
                pipe2["derivativesPreparing"] = 0
                pipe2["derivativesStatus"] = "error"
                pipe2["derivativesError"] = str(exc)[:240]
                if persist:
                    _persist_trip_json(trip_dir, trip)
            except OSError:
                return
        finally:
            with _on_demand_lock:
                _on_demand_threads.pop(trip_key, None)
                _on_demand_pending.pop(trip_key, None)

    with _on_demand_lock:
        prior = _on_demand_threads.get(trip_key)
        if prior is not None and prior.is_alive():
            # CQA D-05 · coalesce into in-flight worker; do not spawn a second thread
            pending = _on_demand_pending.setdefault(trip_key, set())
            pending |= need_set
            pipe["derivativesPreparing"] = max(
                int(pipe.get("derivativesPreparing") or 0), len(pending)
            )
            if persist:
                # persist preparing bump outside lock below
                pass
            coalesced = True
        else:
            _on_demand_pending[trip_key] = set(need_set)
            thread = threading.Thread(
                target=_bg, name="derivative-ondemand", daemon=True
            )
            _on_demand_threads[trip_key] = thread
            thread.start()
            coalesced = False

    if coalesced and persist:
        _persist_trip_json(trip_dir, trip)

    return OnDemandMaterializeResult(
        mode="async",
        asset_ids=need,
        preparing_count=len(need),
        elapsed_ms=round((time.monotonic() - t0) * 1000.0, 2),
    )


def stop_or_join_on_demand(
    trip_dir: Path,
    *,
    timeout: float = 2.0,
) -> None:
    """PDG · stop/join on-demand materialize thread for ``trip_dir``.

    Lock is only held to pop the thread reference; join runs **outside** the lock.
    On timeout, rename/delete may proceed; background persist must tolerate missing dir.
    """
    trip_key = _trip_key(trip_dir)
    with _on_demand_lock:
        thread = _on_demand_threads.pop(trip_key, None)
        _on_demand_pending.pop(trip_key, None)
    if thread is None or not thread.is_alive():
        return
    thread.join(timeout=max(0.0, float(timeout)))


def register_on_demand_thread_for_tests(
    trip_dir: Path, thread: threading.Thread
) -> None:
    """Test hook · inject a live on-demand thread for AC-PDG-07 barrier cases."""
    trip_key = _trip_key(trip_dir)
    with _on_demand_lock:
        _on_demand_threads[trip_key] = thread


def _persist_trip_json(trip_dir: Path, trip: dict) -> None:
    """Atomically rewrite ``trip.json`` (tmp + os.replace · CQA D-05)."""
    path = trip_dir / "trip.json"
    if not path.is_file():
        return
    import json
    import os
    import tempfile

    text = json.dumps(trip, ensure_ascii=False, indent=2) + "\n"
    tmp_path: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix="trip.json.", suffix=".tmp", dir=str(trip_dir)
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(str(tmp_path), str(path))
        tmp_path = None
    except OSError:
        # PDG · directory may have been renamed/deleted mid-flight
        return
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


def missing_planned_widths(asset: dict, *, planned_widths: tuple[int, ...] | list[int]) -> list[int]:
    have = {
        int(e.get("width") or 0)
        for e in (asset.get("srcset") or [])
        if isinstance(e, dict)
    }
    return [int(w) for w in sorted(planned_widths) if int(w) not in have]


def materialize_asset_widths(
    asset: dict,
    trip_dir: Path,
    *,
    widths: list[int] | tuple[int, ...],
    cfg: IngestConfig,
    planned_widths: tuple[int, ...] | list[int] | None = None,
) -> list[int]:
    """Write missing WebP widths and merge into ``srcset``. Returns widths added."""
    need = [int(w) for w in widths if int(w) > 0]
    if not need:
        return []
    from travelogue.media.ingest import IngestError, _load_photo
    from travelogue.media.source_resolve import MediaSourceMissingError, resolve_source_path

    try:
        source_path = resolve_source_path(asset, trip_dir, raise_on_missing=True)
    except MediaSourceMissingError as exc:
        raise IngestError("E_MEDIA_SOURCE_MISSING", str(exc)) from exc
    if source_path is None:
        raise IngestError("E_MEDIA_SOURCE_MISSING", "missing source after resolve")

    loaded = _load_photo(source_path)
    img = loaded.image
    focal = focal_from_asset(asset)
    assets_dir = trip_dir / "assets"
    _display, srcset_new, out_w, out_h, _crop_m, _crop_w = export_webp_variants(
        img,
        assets_dir,
        str(asset["id"]),
        widths=tuple(need),
        quality=cfg.webp_quality,
        webp_method=cfg.webp_method,
        generate_crops=False,
        focal=focal,
        pyramid=bool(getattr(cfg, "webp_pyramid", False)),
    )
    existing = [
        dict(e)
        for e in (asset.get("srcset") or [])
        if isinstance(e, dict) and e.get("file") and e.get("width")
    ]
    by_w = {int(e["width"]): e for e in existing}
    for entry in srcset_new:
        by_w[int(entry["width"])] = {"file": entry["file"], "width": int(entry["width"])}
    merged = [by_w[w] for w in sorted(by_w)]
    asset["srcset"] = merged
    max_w = max(int(e["width"]) for e in merged)
    asset["displayFile"] = f"assets/{asset['id']}-w{max_w}.webp"
    asset["width"] = out_w if max_w == max(need) else asset.get("width", out_w)
    asset["height"] = out_h if max_w == max(need) else asset.get("height", out_h)
    plan_widths = planned_widths or tuple(
        (asset.get("derivedPlan") or {}).get("plannedWidths") or cfg.webp_widths
    )
    sync_derived_plan_from_srcset(asset, planned_widths=plan_widths)
    return need


@dataclass
class MaterializeResult:
    materialized_assets: int = 0
    widths_written: int = 0
    skipped_assets: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    workers: int = 1
    decode_ms: float = 0.0
    encode_ms: float = 0.0


def materialize_widths_worker(payload: dict[str, Any]) -> dict[str, Any]:
    """Decode once and write WebP into a temp dir. Never receives a trip dict."""
    from travelogue.media.ingest import _load_photo

    asset_id = str(payload["asset_id"])
    tmp_dir = Path(str(payload["tmp_dir"]))
    tmp_dir.mkdir(parents=True, exist_ok=True)
    widths = tuple(int(w) for w in payload.get("widths") or () if int(w) > 0)
    t0 = time.monotonic()
    try:
        loaded = _load_photo(Path(str(payload["source_path"])))
        decode_ms = round((time.monotonic() - t0) * 1000.0, 2)
        t1 = time.monotonic()
        _display, srcset_new, out_w, out_h, _crop_m, _crop_w = export_webp_variants(
            loaded.image,
            tmp_dir,
            asset_id,
            widths=widths,
            quality=int(payload.get("quality") or 82),
            webp_method=int(payload.get("webp_method") or 4),
            generate_crops=False,
            focal=tuple(payload.get("focal") or (0.5, 0.45)),
            pyramid=bool(payload.get("pyramid") or False),
        )
        encode_ms = round((time.monotonic() - t1) * 1000.0, 2)
        return {
            "asset_id": asset_id,
            "ok": True,
            "error": None,
            "srcset": list(srcset_new),
            "out_w": int(out_w),
            "out_h": int(out_h),
            "tmp_dir": str(tmp_dir),
            "widths": list(widths),
            "decode_ms": decode_ms,
            "encode_ms": encode_ms,
        }
    except Exception as exc:  # noqa: BLE001 — collected by the parent process
        return {
            "asset_id": asset_id,
            "ok": False,
            "error": f"{type(exc).__name__}:{exc}",
            "srcset": [],
            "out_w": 0,
            "out_h": 0,
            "tmp_dir": str(tmp_dir),
            "widths": list(widths),
            "decode_ms": 0.0,
            "encode_ms": 0.0,
        }


def resolve_materialize_workers(
    *,
    asset_count: int,
    median_long_edge_px: int | None,
) -> int:
    if asset_count < 2:
        return 1
    from travelogue.media.ingest_parallel import _combined_worker_cap

    cpu = os.cpu_count() or 2
    uncapped = max(1, min(cpu // 2, 10))
    cap, _reason = _combined_worker_cap(
        median_long_edge_px=median_long_edge_px, widths_in_flight=2
    )
    return max(1, min(uncapped, cap))


def _write_materialize_timings(
    trip: dict,
    *,
    workers: int,
    assets: int,
    decode_ms: float,
    encode_ms: float,
) -> None:
    pipe = trip.setdefault("pipeline", {})
    timings = dict(pipe.get("timings") or {})
    timings["materializeWorkers"] = float(workers)
    timings["materializeAssets"] = float(assets)
    timings["materializeDecodeMs"] = float(decode_ms)
    timings["materializeEncodeMs"] = float(encode_ms)
    pipe["timings"] = timings


def _apply_materialize_worker_result(
    asset: dict,
    trip_dir: Path,
    worker_out: dict[str, Any],
    *,
    planned_widths: tuple[int, ...],
) -> list[int]:
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(str(worker_out.get("tmp_dir") or ""))
    written: list[int] = []
    for entry in worker_out.get("srcset") or []:
        if not isinstance(entry, dict):
            continue
        width = int(entry.get("width") or 0)
        if width <= 0:
            continue
        src = tmp_dir / f"{asset['id']}-w{width}.webp"
        dest = assets_dir / f"{asset['id']}-w{width}.webp"
        if src.is_file():
            shutil.move(str(src), str(dest))
            written.append(width)
    if tmp_dir.is_dir():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    existing = [
        dict(e)
        for e in (asset.get("srcset") or [])
        if isinstance(e, dict) and e.get("file") and e.get("width")
    ]
    by_w = {int(e["width"]): e for e in existing}
    for entry in worker_out.get("srcset") or []:
        if isinstance(entry, dict) and entry.get("width"):
            by_w[int(entry["width"])] = {
                "file": f"assets/{asset['id']}-w{int(entry['width'])}.webp",
                "width": int(entry["width"]),
            }
    if not by_w:
        return written
    merged = [by_w[w] for w in sorted(by_w)]
    asset["srcset"] = merged
    max_w = max(int(e["width"]) for e in merged)
    asset["displayFile"] = f"assets/{asset['id']}-w{max_w}.webp"
    out_w = int(worker_out.get("out_w") or asset.get("width") or 0)
    out_h = int(worker_out.get("out_h") or asset.get("height") or 0)
    need = [int(w) for w in worker_out.get("widths") or written]
    if need and max_w == max(need):
        asset["width"] = out_w or asset.get("width")
        asset["height"] = out_h or asset.get("height")
    sync_derived_plan_from_srcset(asset, planned_widths=planned_widths)
    return written


def collect_materialize_jobs(
    trip: dict,
    trip_dir: Path,
    *,
    app_cfg: AppConfig,
    asset_ids: set[str] | None = None,
    mark_unselected_skipped: bool = True,
) -> tuple[list[dict[str, Any]], MaterializeResult]:
    """Build worker payloads. Marks skipped plans on the calling thread only."""
    cfg = app_cfg.ingest
    planned = tuple(int(w) for w in cfg.webp_widths)
    selected = asset_ids if asset_ids is not None else selected_asset_ids(trip)
    result = MaterializeResult()
    jobs: list[dict[str, Any]] = []
    from travelogue.media.source_resolve import MediaSourceMissingError, resolve_source_path

    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict) or asset.get("type", "image") != "image":
            continue
        aid = str(asset.get("id") or "")
        if aid not in selected:
            if mark_unselected_skipped:
                plan = asset.get("derivedPlan")
                if isinstance(plan, dict):
                    plan = dict(plan)
                    plan["status"] = "skipped"
                    asset["derivedPlan"] = plan
                else:
                    sync_derived_plan_from_srcset(asset, planned_widths=planned)
                    asset["derivedPlan"]["status"] = "skipped"
                result.skipped_assets += 1
            continue
        missing = missing_planned_widths(asset, planned_widths=planned)
        if not missing:
            sync_derived_plan_from_srcset(asset, planned_widths=planned)
            continue
        try:
            source_path = resolve_source_path(asset, trip_dir, raise_on_missing=True)
        except MediaSourceMissingError as exc:
            result.errors.append(f"{aid}:{type(exc).__name__}:{exc}")
            continue
        if source_path is None:
            result.errors.append(f"{aid}:E_MEDIA_SOURCE_MISSING:missing source")
            continue
        jobs.append(
            {
                "asset_id": aid,
                "source_path": str(source_path),
                "widths": tuple(missing),
                "focal": focal_from_asset(asset),
                "quality": int(cfg.webp_quality),
                "webp_method": int(cfg.webp_method),
                "pyramid": bool(getattr(cfg, "webp_pyramid", False)),
            }
        )
    return jobs, result


def apply_materialize_worker_results(
    trip: dict,
    trip_dir: Path,
    outcomes: list[dict[str, Any]],
    *,
    planned_widths: tuple[int, ...],
    seed: MaterializeResult | None = None,
) -> MaterializeResult:
    """Merge worker files + metadata on the calling thread, in assets[] order."""
    result = seed or MaterializeResult()
    by_id = {str(o.get("asset_id") or ""): o for o in outcomes}
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        aid = str(asset.get("id") or "")
        worker_out = by_id.get(aid)
        if worker_out is None:
            continue
        if not worker_out.get("ok"):
            result.errors.append(f"{aid}:{worker_out.get('error') or 'worker_failed'}")
            tmp_dir = worker_out.get("tmp_dir")
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            continue
        written = _apply_materialize_worker_result(
            asset, trip_dir, worker_out, planned_widths=planned_widths
        )
        if written:
            result.materialized_assets += 1
            result.widths_written += len(written)
            result.decode_ms += float(worker_out.get("decode_ms") or 0.0)
            result.encode_ms += float(worker_out.get("encode_ms") or 0.0)
    return result


def run_materialize_jobs(
    jobs: list[dict[str, Any]],
    *,
    trip_dir: Path,
    workers: int,
) -> list[dict[str, Any]]:
    if not jobs:
        return []
    tmp_root = trip_dir / ".materialize-partial"
    if tmp_root.exists():
        shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    payloads: list[dict[str, Any]] = []
    for job in jobs:
        payload = dict(job)
        payload["tmp_dir"] = str(tmp_root / str(job["asset_id"]))
        payloads.append(payload)
    try:
        if workers <= 1 or len(payloads) == 1:
            return [materialize_widths_worker(p) for p in payloads]
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
            return list(pool.map(materialize_widths_worker, payloads))
    finally:
        if tmp_root.exists() and not any(tmp_root.iterdir()):
            shutil.rmtree(tmp_root, ignore_errors=True)


def ensure_derivatives_for_trip(
    trip: dict,
    trip_dir: Path,
    *,
    app_cfg: AppConfig | None = None,
    asset_ids: set[str] | None = None,
    mark_unselected_skipped: bool = True,
) -> MaterializeResult:
    """Fail-closed: materialize planned widths for selected assets."""
    resolved = app_cfg or get_config()
    if not resolved.pipeline.deferred_derivatives:
        return MaterializeResult()
    planned = tuple(int(w) for w in resolved.ingest.webp_widths)
    t0 = time.monotonic()
    jobs, result = collect_materialize_jobs(
        trip,
        trip_dir,
        app_cfg=resolved,
        asset_ids=asset_ids,
        mark_unselected_skipped=mark_unselected_skipped,
    )
    from travelogue.media.ingest_parallel import median_int

    edges = [
        max(int(a.get("width") or 0), int(a.get("height") or 0))
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and a.get("type", "image") == "image"
    ]
    workers = resolve_materialize_workers(
        asset_count=len(jobs),
        median_long_edge_px=median_int(edges),
    )
    outcomes = run_materialize_jobs(jobs, trip_dir=trip_dir, workers=workers)
    result = apply_materialize_worker_results(
        trip, trip_dir, outcomes, planned_widths=planned, seed=result
    )
    result.workers = workers
    result.elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
    if jobs:
        _write_materialize_timings(
            trip,
            workers=workers,
            assets=result.materialized_assets,
            decode_ms=result.decode_ms,
            encode_ms=result.encode_ms,
        )
    return result


def ensure_derivatives_before_export(
    trip: dict,
    trip_dir: Path,
    *,
    app_cfg: AppConfig | None = None,
) -> MaterializeResult:
    """D6 · sync materialize on export click; never leave export greyed out."""
    result = ensure_derivatives_for_trip(trip, trip_dir, app_cfg=app_cfg)
    pipe = trip.setdefault("pipeline", {})
    if not result.errors:
        pipe["derivativesStatus"] = "ready"
    elif not pipe.get("derivativesStatus"):
        pipe["derivativesStatus"] = "preview"
    return result


class DerivativeMaterializer:
    """Background pool after structure lock; merge on the joining thread."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._result: MaterializeResult | None = None
        self._error: BaseException | None = None
        self._lock = threading.Lock()
        self._trip: dict | None = None
        self._trip_dir: Path | None = None
        self._planned: tuple[int, ...] = ()
        self._pending: list[dict[str, Any]] = []
        self._seed: MaterializeResult | None = None
        self._workers: int = 1
        self._t0: float = 0.0

    def start(self, trip: dict, trip_dir: Path, *, app_cfg: AppConfig) -> None:
        if not app_cfg.pipeline.deferred_derivatives:
            return
        self._trip = trip
        self._trip_dir = trip_dir
        self._planned = tuple(int(w) for w in app_cfg.ingest.webp_widths)
        jobs, seed = collect_materialize_jobs(trip, trip_dir, app_cfg=app_cfg)
        self._seed = seed
        from travelogue.media.ingest_parallel import median_int

        edges = [
            max(int(a.get("width") or 0), int(a.get("height") or 0))
            for a in (trip.get("assets") or [])
            if isinstance(a, dict) and a.get("type", "image") == "image"
        ]
        self._workers = resolve_materialize_workers(
            asset_count=len(jobs),
            median_long_edge_px=median_int(edges),
        )
        self._t0 = time.monotonic()

        def _run() -> None:
            try:
                self._pending = run_materialize_jobs(
                    jobs, trip_dir=trip_dir, workers=self._workers
                )
            except BaseException as exc:  # noqa: BLE001
                self._error = exc

        self._thread = threading.Thread(
            target=_run, name="derivative-materialize", daemon=True
        )
        self._thread.start()

    def join(self, *, timeout: float | None = None) -> MaterializeResult | None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        with self._lock:
            if self._error is not None:
                raise self._error
            if self._trip is None or self._trip_dir is None:
                return self._result
            result = apply_materialize_worker_results(
                self._trip,
                self._trip_dir,
                self._pending,
                planned_widths=self._planned,
                seed=self._seed,
            )
            result.workers = self._workers
            result.elapsed_ms = round((time.monotonic() - self._t0) * 1000.0, 2)
            _write_materialize_timings(
                self._trip,
                workers=self._workers,
                assets=result.materialized_assets,
                decode_ms=result.decode_ms,
                encode_ms=result.encode_ms,
            )
            self._result = result
            return result
