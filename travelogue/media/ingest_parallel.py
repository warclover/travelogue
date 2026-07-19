"""Parallel ingest orchestration (main process). Imported only from ingest.py."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.config import AppConfig, IngestConfig
from travelogue.media.heuristic_tags import build_heuristic_tags
from travelogue.media.ingest_worker import (
    WorkerIngestConfig,
    WorkerResult,
    cleanup_provisional_files,
    process_ingest_photo_worker_star,
)
from travelogue.media.media_classify import classify_media_class, date_confidence_for_source


def workers_memory_cap(*, median_long_edge_px: int | None = None) -> int:
    """Cap parallel ingest workers by typical album resolution (PRD · D5 / MF-05).

    Peak RAM scales with decoded pixels; 36MP × many workers can OOM. Thresholds
    use long-edge (max(w, h)) medians in pixels.
    """
    if median_long_edge_px is None or median_long_edge_px <= 0:
        return 10
    edge = int(median_long_edge_px)
    if edge >= 7000:
        return 4
    if edge >= 5000:
        return 6
    if edge >= 3500:
        return 8
    return 10


def resolve_auto_ingest_workers(*, median_long_edge_px: int | None = None) -> tuple[int, bool]:
    """Return ``(workers, downscaled)`` for ``parallel_ingest_workers=0``.

    Auto formula (PRD-PIPELINE-PERF-V1 · R1.2): ``max(2, min(cpu//2, 10))``,
    then apply :func:`workers_memory_cap`.
    """
    cpu = os.cpu_count() or 2
    uncapped = max(2, min(cpu // 2, 10))
    capped = min(uncapped, workers_memory_cap(median_long_edge_px=median_long_edge_px))
    return max(1, capped), capped < uncapped


def resolve_parallel_ingest_plan(
    app_cfg: AppConfig,
    *,
    photo_count: int,
    median_long_edge_px: int | None = None,
) -> tuple[bool, int, bool, bool]:
    """Return ``(use_parallel, workers, fallback_serial, workers_downscaled)``.

    ``workers=1`` or ``photo_count < min_photos`` → serial short-circuit.
    """
    pipe = app_cfg.pipeline
    if not pipe.parallel_ingest:
        return False, 1, False, False
    min_photos = max(1, int(pipe.parallel_ingest_min_photos))
    if photo_count < min_photos:
        return False, 1, True, False
    configured = int(pipe.parallel_ingest_workers)
    if configured == 1:
        return False, 1, False, False
    downscaled = False
    if configured <= 0:
        workers, downscaled = resolve_auto_ingest_workers(
            median_long_edge_px=median_long_edge_px
        )
    else:
        workers = max(1, configured)
        mem_cap = workers_memory_cap(median_long_edge_px=median_long_edge_px)
        if workers > mem_cap:
            workers = mem_cap
            downscaled = True
    if workers <= 1:
        return False, 1, False, False
    return True, workers, False, downscaled


def _rewrite_asset_rel(rel: str | None, *, provisional_id: str, asset_id: str) -> str | None:
    if not rel:
        return None
    return rel.replace(provisional_id, asset_id)


def _commit_provisional_blobs(
    result: WorkerResult,
    *,
    asset_id: str,
    source_dir: Path,
    assets_dir: Path,
    copy_source_files: bool = True,
) -> tuple[str, list[dict], str | None, str | None]:
    """Rename provisional files to final assetId paths; return updated rel paths."""
    prov_id = result.provisional_id
    if copy_source_files:
        if not result.provisional_source:
            raise RuntimeError("missing provisional source")
        dest_source = source_dir / f"{asset_id}.jpg"
        dest_source.parent.mkdir(parents=True, exist_ok=True)
        src_source = Path(result.provisional_source)
        if src_source.is_file():
            if dest_source.exists():
                dest_source.unlink()
            shutil.move(str(src_source), str(dest_source))

    assets_dir.mkdir(parents=True, exist_ok=True)
    prov_assets = Path(result.provisional_dir) / "assets" if result.provisional_dir else None

    def _move_asset_file(rel: str | None) -> str | None:
        if not rel or not rel.startswith("assets/"):
            return _rewrite_asset_rel(rel, provisional_id=prov_id, asset_id=asset_id)
        name = Path(rel).name.replace(prov_id, asset_id)
        final_rel = f"assets/{name}"
        if prov_assets is not None:
            src = prov_assets / Path(rel).name
            dst = assets_dir / name
            if src.is_file():
                if dst.exists():
                    dst.unlink()
                shutil.move(str(src), str(dst))
        return final_rel

    display = _move_asset_file(result.display_rel)
    srcset: list[dict] = []
    for entry in result.srcset or []:
        if not isinstance(entry, dict):
            continue
        new_file = _move_asset_file(str(entry.get("file") or ""))
        item = dict(entry)
        if new_file:
            item["file"] = new_file
        srcset.append(item)
    crop_m = _move_asset_file(result.crop_mobile_rel)
    crop_w = _move_asset_file(result.crop_web_rel)
    cleanup_provisional_files(result)
    return display or f"assets/{asset_id}-w{max(1, result.out_w)}.webp", srcset, crop_m, crop_w


def _resolve_place_city_main(
    *,
    geo_lat: float | None,
    geo_lon: float | None,
    trip_dir: Path,
    geocode_enabled: bool,
) -> tuple[dict | None, dict | None]:
    if geo_lat is None or geo_lon is None:
        return None, None
    geo_obj = {"lat": round(geo_lat, 6), "lon": round(geo_lon, 6)}
    place = None
    if geocode_enabled:
        from travelogue.media.geocode import reverse_geocode_city

        cache_path = trip_dir.parent / ".geocode-cache.json"
        city = reverse_geocode_city(geo_lat, geo_lon, cache_path=cache_path, enabled=True)
        if city:
            place = {"city": city}
    return geo_obj, place


def _build_entry_from_worker_result(
    *,
    result: WorkerResult,
    asset_id: str,
    build_ctx: Any,
    burst_group_id: str | None,
    user_tier: str,
    import_source: str | None,
    display_rel: str,
    srcset: list[dict],
    crop_m: str | None,
    crop_w: str | None,
) -> dict:
    """Assemble trip asset entry on main process (geocode + aesthetic; no worker CLIP)."""
    from travelogue.media.ingest import (
        IngestAssetBuildContext,
        IngestPhotoPayload,
        _attach_aesthetic,
    )
    from travelogue.media.user_tier import apply_user_tier_fields

    if not isinstance(build_ctx, IngestAssetBuildContext):
        raise TypeError(
            f"build_ctx must be IngestAssetBuildContext, got {type(build_ctx)!r}"
        )
    cfg = build_ctx.cfg
    geo_obj, place = _resolve_place_city_main(
        geo_lat=result.geo_lat,
        geo_lon=result.geo_lon,
        trip_dir=build_ctx.trip_dir,
        geocode_enabled=build_ctx.geocode_enabled,
    )
    if geo_obj:
        build_ctx.ingest_stats["gps_assets"] = build_ctx.ingest_stats.get("gps_assets", 0) + 1

    taken_at = datetime.now()
    if result.taken_at_iso:
        raw = result.taken_at_iso.rstrip("Z")
        try:
            taken_at = datetime.fromisoformat(raw)
        except ValueError:
            taken_at = datetime.now()
    tags = build_heuristic_tags(
        taken_at=taken_at,
        aspect_kind=result.aspect_kind or "landscape",
        subject_tags=result.subject_tags,
        place_city=(place or {}).get("city") if place else None,
        max_tags=build_ctx.max_tags,
    )

    sharp_out = result.sharpness
    quality: dict[str, Any] = {
        "sharpness": round(sharp_out, 2),
        "meanLuma": round(result.mean_luma, 4),
    }
    sharp_ver = str(cfg.sharpness_version or "v2").lower()
    if sharp_ver == "v2" and result.sharpness_v2 is not None:
        quality["sharpness"] = round(result.sharpness_v2, 2)
        quality["sharpnessVersion"] = "v2"
        quality["sharpnessLegacy"] = round(result.sharpness, 2)
    else:
        quality["sharpnessVersion"] = "v1"

    if result.face_count > 0:
        quality["faceCount"] = int(result.face_count)
        if result.salient_box:
            face_ratio = float(result.salient_box.get("w", 0.0)) * float(
                result.salient_box.get("h", 0.0)
            )
            quality["faceRatio"] = round(max(0.0, min(1.0, face_ratio)), 4)
        build_ctx.ingest_stats["faces_detected"] = (
            build_ctx.ingest_stats.get("faces_detected", 0) + 1
        )
    if result.portrait_quality:
        quality["portrait"] = result.portrait_quality
        build_ctx.ingest_stats["portrait_analyzed"] = (
            build_ctx.ingest_stats.get("portrait_analyzed", 0) + 1
        )

    from travelogue.media.source_resolve import build_source_ref

    copy_source = bool(getattr(build_ctx, "copy_source_files", True)) or bool(
        getattr(build_ctx, "force_materialize", False)
    )
    entry: dict = {
        "id": asset_id,
        "type": "image",
        "displayFile": display_rel,
        "srcset": srcset,
        "nativeWidth": result.width,
        "nativeHeight": result.height,
        "width": result.out_w,
        "height": result.out_h,
        "aspectKind": result.aspect_kind,
        "takenAt": result.taken_at_iso,
        "dateSource": result.date_source,
        "dateConfidence": date_confidence_for_source(result.date_source or "mtime"),
        "ingestBatchId": build_ctx.batch,
        "dedupeGroupId": f"dhash:{result.dhash}",
        "focalPoint": {"x": result.focal_x, "y": result.focal_y},
        "quality": quality,
        "dominantTone": result.dominant_tone,
        "layoutEligible": True,
    }
    if copy_source:
        entry["sourceFile"] = f"source/{asset_id}.jpg"
    entry["sourceRef"] = build_source_ref(
        album_root=getattr(build_ctx, "album_root", None),
        source_path=Path(result.source_path),
    )
    if result.content_sig:
        entry["contentSig"] = result.content_sig
    if result.salient_box:
        entry["salientBox"] = result.salient_box
    if tags:
        entry["tags"] = tags
        entry["tagsSource"] = "heuristic"
    from travelogue.layout_contract.subject_tagging import semantic_category_for_asset

    entry["semanticTag"] = {"category": semantic_category_for_asset(entry)}
    if result.exif:
        entry["exif"] = result.exif
    if crop_m:
        entry["cropMobile"] = crop_m
    if crop_w:
        entry["cropWeb"] = crop_w
    if geo_obj:
        entry["geo"] = geo_obj
    if place:
        entry["place"] = place
    if burst_group_id:
        entry["burstGroupId"] = burst_group_id

    # mediaClass + aesthetic need pixels — prefer committed jpeg, else original album path
    img = None
    open_candidates = [
        build_ctx.source_dir / f"{asset_id}.jpg",
        Path(result.source_path),
    ]
    for candidate in open_candidates:
        if not candidate.is_file():
            continue
        try:
            img = Image.open(candidate)
            img.load()
            break
        except OSError:
            img = None
    if img is not None:
        entry["mediaClass"] = classify_media_class(
            path=Path(result.source_path),
            img=img,
            date_source=result.date_source or "mtime",
            asset=entry,
        )
        photo_payload = IngestPhotoPayload(
            asset_id=asset_id,
            photo=Path(result.source_path),
            loaded=None,
            img=img,
            dhash=result.dhash or "",
            sharpness=result.sharpness,
            burst_group_id=burst_group_id,
            content_sig=result.content_sig,
            user_tier=user_tier,
            import_source=import_source,
        )
        _attach_aesthetic(build_ctx, entry, photo_payload)
        img.close()
    else:
        entry["mediaClass"] = "photo"
        entry["referenceDecodeSkipped"] = True

    apply_user_tier_fields(
        entry,
        tier=user_tier,
        dual_ingest=build_ctx.dual_ingest,
        import_source=import_source,
    )
    from travelogue.media.derivatives import sync_derived_plan_from_srcset

    sync_derived_plan_from_srcset(entry, planned_widths=cfg.webp_widths)
    return entry


def merge_one_worker_result(
    *,
    result: WorkerResult,
    state: Any,
    build_ctx: Any,
    cfg: IngestConfig,
    dedupe: bool,
    from_dir: Path | None,
    album_root: Path,
    trip_dir: Path,
    resume_ingest: bool,
    processed: int,
    total_photos: int,
    on_persist: Callable[[], None] | None,
    on_asset_added: Callable[[dict], None] | None,
    emit_progress: Callable[..., None],
    persist_every_n: int,
    kept_since_persist: list[int],
) -> None:
    """Replay serial dedupe state machine for one WorkerResult (input order)."""
    from travelogue.media import ingest_checkpoint as icp
    from travelogue.media.ingest import (
        _find_phash_asset_index,
        _ingest_progress_tick,
        _is_burst_duplicate,
        _next_asset_id,
        _upsert_asset,
    )
    from travelogue.media.quality import asset_sharpness
    from travelogue.media.user_tier import (
        preserve_material_import_source_on_dedupe,
        preserve_user_tier_on_replace,
        preserve_user_tier_source_on_replace,
        upgrade_asset_tier,
    )

    if result.error:
        cleanup_provisional_files(result)
        state.skipped += 1
        if _ingest_progress_tick(processed, total_photos):
            emit_progress(processed)
        return

    photo = Path(result.source_path)
    user_tier = result.user_tier
    sig = result.content_sig or ""

    if dedupe and sig and sig in state.known_md5:
        if upgrade_asset_tier(state.assets, sig, tier=user_tier):
            state.ingest_stats["tier_upgraded"] = state.ingest_stats.get("tier_upgraded", 0) + 1
        elif preserve_material_import_source_on_dedupe(state.assets, sig, tier=user_tier):
            state.ingest_stats["import_source_material_preserved"] = (
                state.ingest_stats.get("import_source_material_preserved", 0) + 1
            )
        cleanup_provisional_files(result)
        state.ingest_stats["deduped"] += 1
        state.skipped += 1
        if _ingest_progress_tick(processed, total_photos):
            emit_progress(processed)
        return

    # Minimal loaded-like object for burst time/size check
    class _Img:
        width = int(result.width)
        height = int(result.height)

    class _Loaded:
        def __init__(self) -> None:
            self.taken_at = datetime.fromtimestamp(result.taken_at_ts or 0.0)
            self.image = _Img()

    loaded = _Loaded()
    sharp = float(result.sharpness)
    use_burst = dedupe and cfg.dedupe_burst
    use_phash = dedupe and cfg.dedupe_phash
    replace_index: int | None = None

    if use_burst and _is_burst_duplicate(
        loaded, last=state.last_burst, burst_seconds=cfg.burst_seconds
    ):
        if state.assets:
            prev_sharp = asset_sharpness(state.assets[-1])
            if sharp > prev_sharp:
                replace_index = len(state.assets) - 1
                state.ingest_stats["deduped_burst_replaced"] += 1
            else:
                cleanup_provisional_files(result)
                state.ingest_stats["deduped_burst"] += 1
                state.skipped += 1
                if _ingest_progress_tick(processed, total_photos):
                    emit_progress(processed)
                return
        else:
            cleanup_provisional_files(result)
            state.ingest_stats["deduped_burst"] += 1
            state.skipped += 1
            if _ingest_progress_tick(processed, total_photos):
                emit_progress(processed)
            return

    dhash = result.dhash or ""
    degenerate = dhash == "0000000000000000"
    if use_phash and not degenerate and replace_index is None:
        match_idx = _find_phash_asset_index(
            dhash, state.dhash_refs, threshold=cfg.phash_threshold
        )
        if match_idx is not None:
            prev_sharp = asset_sharpness(state.assets[match_idx])
            if sharp > prev_sharp:
                replace_index = match_idx
                state.ingest_stats["deduped_phash_replaced"] += 1
            else:
                cleanup_provisional_files(result)
                state.ingest_stats["deduped_phash"] += 1
                state.skipped += 1
                if _ingest_progress_tick(processed, total_photos):
                    emit_progress(processed)
                return

    if replace_index is None:
        if sig:
            state.known_md5.add(sig)
        state.dhash_refs.append((dhash, len(state.assets)))
        asset_id = _next_asset_id(state.assets)
    else:
        if sig:
            state.known_md5.add(sig)
        asset_id = state.assets[replace_index]["id"]
        for i, (dh, idx) in enumerate(state.dhash_refs):
            if idx == replace_index:
                state.dhash_refs[i] = (dhash, replace_index)
                break

    ts = float(result.taken_at_ts or 0.0)
    if state.last_kept_ts is None or abs(ts - state.last_kept_ts) > cfg.burst_seconds:
        state.burst_counter += 1
        state.current_burst_group = f"burst-{state.burst_counter:03d}"
    state.last_kept_ts = ts

    replace_import_source = None
    replace_tier_source = None
    tier_for_entry = user_tier
    if replace_index is not None:
        old_asset = state.assets[replace_index]
        replace_import_source = old_asset.get("importSource")
        tier_for_entry = preserve_user_tier_on_replace(old_asset, user_tier)
        replace_tier_source = preserve_user_tier_source_on_replace(old_asset, tier_for_entry)

    copy_source = bool(getattr(build_ctx, "copy_source_files", True)) or bool(
        getattr(build_ctx, "force_materialize", False)
    )
    display_rel, srcset, crop_m, crop_w = _commit_provisional_blobs(
        result,
        asset_id=asset_id,
        source_dir=build_ctx.source_dir,
        assets_dir=build_ctx.assets_dir,
        copy_source_files=copy_source,
    )
    entry = _build_entry_from_worker_result(
        result=result,
        asset_id=asset_id,
        build_ctx=build_ctx,
        burst_group_id=state.current_burst_group,
        user_tier=tier_for_entry,
        import_source=replace_import_source,
        display_rel=display_rel,
        srcset=srcset,
        crop_m=crop_m,
        crop_w=crop_w,
    )
    if replace_tier_source:
        entry["userTierSource"] = replace_tier_source

    _upsert_asset(assets=state.assets, replace_index=replace_index, entry=entry)
    state.last_burst = (ts, result.width, result.height)
    short_edge = min(result.width, result.height) if result.width and result.height else 0
    if short_edge and short_edge < cfg.min_short_edge_layout_px:
        state.ingest_stats.setdefault("suspected_thumbnail_ids", []).append(asset_id)
    if replace_index is None:
        state.added += 1
    if on_asset_added is not None:
        on_asset_added(entry)
    if result.date_source:
        state.ingest_stats[f"{result.date_source}_dates"] = (
            state.ingest_stats.get(f"{result.date_source}_dates", 0) + 1
        )
    if result.had_exif_orientation:
        state.ingest_stats["exif_rotations"] += 1

    if from_dir and resume_ingest:
        rel_key = icp.source_key(photo, album_root)
        state.checkpoint_keys.add(rel_key)
        if _ingest_progress_tick(processed, total_photos):
            icp.save_ingest_checkpoint(
                trip_dir,
                source_root=str(album_root),
                processed_rel_paths=sorted(state.checkpoint_keys),
                total=total_photos,
            )

    kept_since_persist[0] += 1
    if on_persist and persist_every_n > 0 and kept_since_persist[0] >= persist_every_n:
        on_persist()
        kept_since_persist[0] = 0
    elif on_persist and from_dir and resume_ingest and _ingest_progress_tick(processed, total_photos):
        on_persist()

    if _ingest_progress_tick(processed, total_photos):
        emit_progress(processed)


def run_parallel_ingest_loop(
    *,
    photo_tiers: list[tuple[Path, str]],
    workers: int,
    trip_dir: Path,
    batch: str,
    state: Any,
    build_ctx: Any,
    cfg: IngestConfig,
    app_cfg: AppConfig,
    dedupe: bool,
    from_dir: Path | None,
    album_root: Path,
    resume_ingest: bool,
    on_persist: Callable[[], None] | None,
    on_asset_added: Callable[[dict], None] | None,
    emit_progress: Callable[..., None],
) -> bool:
    """ProcessPool map → ordered merge/dedupe replay → per-asset offer.

    Returns False when the pool cannot start (caller should fail-open to serial).
    """
    persist_every_n = max(0, int(app_cfg.pipeline.persist_every_n))
    temp_root = trip_dir / ".ingest-partial" / batch
    if temp_root.exists():
        shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)

    portrait_enabled = True
    try:
        portrait_enabled = bool(getattr(app_cfg.cull.portrait, "enabled", True))
    except Exception:
        portrait_enabled = True
    worker_cfg = WorkerIngestConfig.from_ingest_config(
        cfg,
        portrait_enabled=portrait_enabled,
        force_materialize=bool(getattr(build_ctx, "force_materialize", False)),
        deferred_derivatives=bool(app_cfg.pipeline.deferred_derivatives),
    )

    jobs: list[tuple[Any, ...]] = []
    for index, (photo, user_tier) in enumerate(photo_tiers):
        provisional_id = f"prov-{index:05d}"
        jobs.append(
            (
                index,
                str(photo),
                user_tier,
                provisional_id,
                str(temp_root),
                worker_cfg,
            )
        )

    results_by_index: dict[int, WorkerResult] = {}
    total_photos = len(photo_tiers)
    try:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(process_ingest_photo_worker_star, job): int(job[0]) for job in jobs
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results_by_index[idx] = fut.result()
                except Exception as exc:  # noqa: BLE001
                    results_by_index[idx] = WorkerResult(
                        index=idx,
                        source_path=str(photo_tiers[idx][0]),
                        user_tier=photo_tiers[idx][1],
                        provisional_id=f"prov-{idx:05d}",
                        error=f"pool:{type(exc).__name__}: {exc}",
                    )
    except Exception:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
        return False

    kept_since_persist = [0]
    for index in range(total_photos):
        result = results_by_index.get(index)
        if result is None:
            result = WorkerResult(
                index=index,
                source_path=str(photo_tiers[index][0]),
                user_tier=photo_tiers[index][1],
                provisional_id=f"prov-{index:05d}",
                error="missing worker result",
            )
        merge_one_worker_result(
            result=result,
            state=state,
            build_ctx=build_ctx,
            cfg=cfg,
            dedupe=dedupe,
            from_dir=from_dir,
            album_root=album_root,
            trip_dir=trip_dir,
            resume_ingest=resume_ingest,
            processed=index + 1,
            total_photos=total_photos,
            on_persist=on_persist,
            on_asset_added=on_asset_added,
            emit_progress=emit_progress,
            persist_every_n=persist_every_n,
            kept_since_persist=kept_since_persist,
        )

    if on_persist and kept_since_persist[0] > 0:
        on_persist()

    if temp_root.exists():
        shutil.rmtree(temp_root, ignore_errors=True)
    return True
