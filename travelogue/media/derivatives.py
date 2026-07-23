"""Deferred WebP derivative materialization (PRD-PIPELINE-PERF-V1 · R2.1/R2.2).

``srcset`` only lists files on disk. Planned widths live in ``asset.derivedPlan``.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, IngestConfig, get_config
from travelogue.media.image_ops import export_webp_variants, focal_from_asset
from travelogue.media.ingest import IngestError, _load_photo

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
    full = tuple(int(w) for w in (cfg.webp_widths or (800, 1600)))
    if not deferred:
        return full
    ingest = tuple(int(w) for w in (cfg.webp_ingest_widths or (800, 1600)))
    allowed = set(full)
    filtered = tuple(w for w in sorted(ingest) if w in allowed)
    return filtered or full[: min(2, len(full))]


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
    cfg = resolved.ingest
    if not resolved.pipeline.deferred_derivatives:
        return MaterializeResult()
    planned = tuple(int(w) for w in cfg.webp_widths)
    selected = asset_ids if asset_ids is not None else selected_asset_ids(trip)
    t0 = time.monotonic()
    result = MaterializeResult()
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
            written = materialize_asset_widths(
                asset,
                trip_dir,
                widths=missing,
                cfg=cfg,
                planned_widths=planned,
            )
            result.materialized_assets += 1
            result.widths_written += len(written)
        except Exception as exc:  # noqa: BLE001 — collect; caller may fail-closed
            result.errors.append(f"{aid}:{type(exc).__name__}:{exc}")
    result.elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
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
    """Background materialize after structure lock; join before render."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._result: MaterializeResult | None = None
        self._error: BaseException | None = None
        self._lock = threading.Lock()

    def start(self, trip: dict, trip_dir: Path, *, app_cfg: AppConfig) -> None:
        if not app_cfg.pipeline.deferred_derivatives:
            return

        def _run() -> None:
            try:
                self._result = ensure_derivatives_for_trip(
                    trip, trip_dir, app_cfg=app_cfg
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
            return self._result
