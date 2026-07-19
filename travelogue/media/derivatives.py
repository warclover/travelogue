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
    """Assets that appear in cover / moment / chapters / screens."""
    ids: set[str] = set()
    for key in ("coverAssetId", "momentAssetId"):
        raw = trip.get(key)
        if isinstance(raw, str) and raw.strip():
            ids.add(raw.strip())
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
