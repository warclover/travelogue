"""Agent 0 · Media Lab — import photos into trip workspace."""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from travelogue.config import AppConfig, IngestConfig, get_config
from travelogue.errors import CodeError
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso
from travelogue.curation.asset_quality import apply_layout_eligibility_marks, asset_sharpness
from travelogue.curation.media_classify import (
    classify_media_class,
    date_confidence_for_source,
    refine_archive_media_class,
    summarize_media_classes,
)
from travelogue.media import ingest_checkpoint as icp
from travelogue.media.color_metrics import color_metrics_from_thumb, dominant_tone_hex, mean_luma
from travelogue.media.heuristic_tags import build_heuristic_tags
from travelogue.media.ingest_preview import preview_multi_journey
from travelogue.media.subject_detect import analyze_subject
from travelogue.media.trip_dates import apply_meta_dates_from_assets
from travelogue.vision.cache import append_pending_assets, is_pipeline_locked
from travelogue.media.image_ops import (
    classify_aspect,
    export_webp_variants,
    load_image_normalized,
    min_dimension_ok,
    save_jpeg_without_exif,
)
from travelogue.media.phash import dhash_hex, is_near_duplicate
from travelogue.media.sharpness import sharpness_score

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
HEIC_SUFFIXES = {".heic", ".heif"}
MIN_EDGE_PX = 320
INGEST_PROGRESS_EVERY_N = 5
INGEST_MIN_ASSETS_DEFAULT = 4

RAW_UNSUPPORTED_MESSAGE = (
    "检测到 RAW 原片格式（如 .CR3/.NEF/.ARW）。当前版本不支持 RAW，请先转换为 JPG 后重试。"
)


def _normalize_raw_suffix(suffix: str) -> str:
    s = suffix.lower().strip()
    return s if s.startswith(".") else f".{s}"


def find_raw_files_in_directory(
    directory: Path,
    *,
    blocklist: tuple[str, ...],
    recursive: bool = True,
) -> list[Path]:
    """Return RAW paths under *directory* matching *blocklist* (P7-RAW-GATE)."""
    normalized = frozenset(_normalize_raw_suffix(s) for s in blocklist)
    root = directory.resolve()
    hits: list[Path] = []
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    for path in iterator:
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root)
        except (ValueError, OSError):
            continue
        if _normalize_raw_suffix(path.suffix) in normalized:
            hits.append(path)
    return hits


def _raise_raw_unsupported(raw_files: list[Path], *, sample_limit: int = 5) -> None:
    samples = [p.name for p in raw_files[: max(1, sample_limit)]]
    suffixes = sorted({p.suffix.lower() for p in raw_files})
    detail = f"发现 {len(raw_files)} 个 RAW 文件"
    if suffixes:
        detail += f"（{', '.join(suffixes)}）"
    if samples:
        detail += f"；示例：{', '.join(samples)}"
    raise IngestError("E_INGEST_RAW_UNSUPPORTED", f"{RAW_UNSUPPORTED_MESSAGE} {detail}")


def guard_raw_in_directory(
    directory: Path,
    cfg: IngestConfig,
    *,
    recursive: bool = True,
) -> dict[str, Any]:
    """Scan for RAW files and raise when reject_raw is enabled."""
    stats: dict[str, Any] = {"rawRejectedCount": 0, "rawRejectedSuffixes": []}
    if not cfg.reject_raw:
        return stats
    raw_files = find_raw_files_in_directory(
        directory,
        blocklist=cfg.raw_blocklist_suffixes,
        recursive=recursive,
    )
    if not raw_files:
        return stats
    stats["rawRejectedCount"] = len(raw_files)
    stats["rawRejectedSuffixes"] = sorted({p.suffix.lower() for p in raw_files})
    stats["rawRejectedSamples"] = [p.name for p in raw_files[: cfg.raw_detect_sample_limit]]
    _raise_raw_unsupported(raw_files, sample_limit=cfg.raw_detect_sample_limit)
    return stats


class IngestError(CodeError):
    pass


@dataclass
class IngestAssetBuildContext:
    """Shared ingest pipeline state for building one asset entry."""

    cfg: IngestConfig
    assets_dir: Path
    source_dir: Path
    trip_dir: Path
    ingest_stats: dict
    batch: str
    generate_crops: bool
    max_tags: int
    geocode_enabled: bool
    dual_ingest: bool = False
    elapsed_acc: dict[str, float] | None = None


@dataclass
class IngestPhotoPayload:
    """Per-photo inputs for ``_build_asset_entry``."""

    asset_id: str
    photo: Path
    loaded: Any
    img: Image.Image
    dhash: str
    sharpness: float
    burst_group_id: str | None = None
    content_sig: str | None = None
    user_tier: str = "material"
    import_source: str | None = None


@dataclass
class IngestResult:
    added: int = 0
    skipped: int = 0
    batch_id: str = ""
    stats: dict = field(default_factory=dict)


def _register_heif() -> None:
    try:
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def _load_photo(path: Path):
    _register_heif()
    try:
        return load_image_normalized(path)
    except Exception as exc:
        if path.suffix.lower() in HEIC_SUFFIXES:
            raise IngestError(
                "E_INGEST_HEIC",
                f"HEIC requires pillow-heif: pip install pillow-heif ({path.name})",
            ) from exc
        raise IngestError("E_INGEST_IMAGE", f"cannot open {path.name}: {exc}") from exc


def _file_signature(path: Path) -> str:
    """Content fingerprint for dedupe (size + MD5). Not for security/crypto use."""
    st = path.stat()
    digest = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return f"{st.st_size}:{digest.hexdigest()}"


def scan_image_paths(
    directory: Path,
    *,
    max_photos: int = 250,
    recursive: bool = True,
    min_edge_px: int = MIN_EDGE_PX,
    reject_raw: bool = True,
    raw_blocklist_suffixes: tuple[str, ...] | None = None,
    raw_detect_sample_limit: int = 5,
) -> tuple[list[Path], dict]:
    if not directory.is_dir():
        raise IngestError("E_INGEST_NOT_DIR", f"not a directory: {directory}")

    from travelogue.config import IngestConfig

    raw_cfg = IngestConfig(
        reject_raw=reject_raw,
        raw_blocklist_suffixes=raw_blocklist_suffixes or IngestConfig().raw_blocklist_suffixes,
        raw_detect_sample_limit=raw_detect_sample_limit,
    )
    raw_stats = guard_raw_in_directory(directory, raw_cfg, recursive=recursive)

    candidates: list[Path] = []
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    for path in iterator:
        if not path.is_file():
            continue
        suf = path.suffix.lower()
        if suf in IMAGE_SUFFIXES or suf in HEIC_SUFFIXES:
            candidates.append(path)

    if not candidates:
        raise IngestError("E_INGEST_EMPTY", f"no images in {directory}")

    stats = {"skipped_small": 0, "skipped_open": 0, **raw_stats}
    accepted: list[tuple[datetime, str, Path]] = []

    for path in candidates:
        try:
            loaded = _load_photo(path)
        except IngestError:
            stats["skipped_open"] += 1
            continue
        if not min_dimension_ok(loaded.image, min_edge_px):
            stats["skipped_small"] += 1
            continue
        accepted.append((loaded.taken_at, str(path).lower(), path))

    accepted.sort(key=lambda x: (x[0], x[1]))
    files = [p for _, _, p in accepted[:max_photos]]
    stats["scanned"] = len(candidates)
    stats["used"] = len(files)
    return files, stats


def _next_asset_id(assets: list[dict]) -> str:
    max_n = 0
    for a in assets:
        m = re.match(r"asset-(\d+)$", a.get("id", ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"asset-{max_n + 1:03d}"


def content_signature(path: Path) -> str:
    """Stable MD5 signature (size:hex) for cross-ingest dedupe."""
    return _file_signature(path)


def _existing_md5_sigs(trip: dict) -> set[str]:
    sigs: set[str] = set()
    for a in trip.get("assets") or []:
        content_sig = a.get("contentSig")
        if isinstance(content_sig, str) and content_sig:
            sigs.add(content_sig)
            continue
        gid = a.get("dedupeGroupId") or ""
        if gid.startswith("md5:"):
            sigs.add(gid[4:])
        elif gid and ":" not in gid:
            sigs.add(gid)
    return sigs


def _existing_dhash_refs(trip: dict) -> list[tuple[str, int]]:
    assets = trip.get("assets") or []
    out: list[tuple[str, int]] = []
    for idx, a in enumerate(assets):
        gid = a.get("dedupeGroupId") or ""
        if gid.startswith("dhash:"):
            out.append((gid[6:], idx))
    return out


def _is_burst_duplicate(
    loaded,
    *,
    last: tuple[float, int, int] | None,
    burst_seconds: float,
) -> bool:
    if not last:
        return False
    ts, w, h = last
    img = loaded.image
    if (img.width, img.height) != (w, h):
        return False
    return abs(loaded.taken_at.timestamp() - ts) <= burst_seconds


def _find_phash_asset_index(
    dhash: str,
    refs: list[tuple[str, int]],
    *,
    threshold: int,
) -> int | None:
    for dh, idx in refs:
        if is_near_duplicate(dhash, dh, threshold=threshold):
            return idx
    return None


def _missing_derivative_paths(trip_dir: Path, assets: list[dict]) -> list[tuple[str, str]]:
    """Return (assetId, relativePath) for display/srcset files that should exist."""
    missing: list[tuple[str, str]] = []
    seen: set[str] = set()
    for asset in assets:
        aid = asset.get("id", "")
        for rel in [asset.get("displayFile"), *[e.get("file") for e in asset.get("srcset") or []]]:
            if not rel or rel in seen:
                continue
            seen.add(rel)
            if not (trip_dir / rel).is_file():
                missing.append((aid, rel))
    return missing


def _resolve_place_city(
    loaded,
    *,
    trip_dir: Path,
    geocode_enabled: bool,
) -> tuple[dict | None, dict | None]:
    geo = loaded.geo
    if geo is None:
        return None, None
    geo_obj = {"lat": round(geo.lat, 6), "lon": round(geo.lon, 6)}
    place = None
    if geocode_enabled:
        from travelogue.media.geocode import reverse_geocode_city

        cache_path = trip_dir.parent / ".geocode-cache.json"
        city = reverse_geocode_city(geo.lat, geo.lon, cache_path=cache_path, enabled=True)
        if city:
            place = {"city": city}
    return geo_obj, place


def _build_asset_entry(ctx: IngestAssetBuildContext, photo: IngestPhotoPayload) -> dict:
    cfg = ctx.cfg
    acc = ctx.elapsed_acc
    aspect_kind = classify_aspect(photo.img.width, photo.img.height)
    focal = (0.5, 0.45)
    t_faces = time.monotonic()
    subj = analyze_subject(photo.img, min_face_size=cfg.face_min_size_px, enabled=cfg.detect_faces)
    if acc is not None:
        acc["faces"] = acc.get("faces", 0.0) + (time.monotonic() - t_faces) * 1000.0
    if subj.has_face:
        focal = subj.focal
        ctx.ingest_stats["faces_detected"] = ctx.ingest_stats.get("faces_detected", 0) + 1

    dest_source = ctx.source_dir / f"{photo.asset_id}.jpg"
    if photo.photo.resolve() != dest_source.resolve() or not dest_source.is_file():
        save_jpeg_without_exif(photo.img, dest_source)

    t_webp = time.monotonic()
    display_rel, srcset_rel, out_w, out_h, crop_m, crop_w = export_webp_variants(
        photo.img,
        ctx.assets_dir,
        photo.asset_id,
        widths=cfg.webp_widths,
        quality=cfg.webp_quality,
        webp_method=cfg.webp_method,
        generate_crops=ctx.generate_crops,
        focal=focal,
    )
    if acc is not None:
        acc["webp"] = acc.get("webp", 0.0) + (time.monotonic() - t_webp) * 1000.0

    luma_val, tone_hex = color_metrics_from_thumb(photo.img, thumb_px=cfg.shared_color_thumb_px)

    geo_obj, place = _resolve_place_city(
        photo.loaded, trip_dir=ctx.trip_dir, geocode_enabled=ctx.geocode_enabled
    )
    if geo_obj:
        ctx.ingest_stats["gps_assets"] = ctx.ingest_stats.get("gps_assets", 0) + 1

    tags = build_heuristic_tags(
        taken_at=photo.loaded.taken_at,
        aspect_kind=aspect_kind,
        subject_tags=subj.tags,
        place_city=(place or {}).get("city") if place else None,
        max_tags=ctx.max_tags,
    )

    entry: dict = {
        "id": photo.asset_id,
        "type": "image",
        "sourceFile": f"source/{dest_source.name}",
        "displayFile": display_rel,
        "srcset": srcset_rel,
        "nativeWidth": photo.img.width,
        "nativeHeight": photo.img.height,
        "width": out_w,
        "height": out_h,
        "aspectKind": aspect_kind,
        "takenAt": photo.loaded.taken_at.replace(tzinfo=None).isoformat() + "Z",
        "dateSource": photo.loaded.date_source,
        "dateConfidence": date_confidence_for_source(photo.loaded.date_source),
        "ingestBatchId": ctx.batch,
        "dedupeGroupId": f"dhash:{photo.dhash}",
        "focalPoint": {"x": focal[0], "y": focal[1]},
        "quality": {
            "sharpness": round(photo.sharpness, 2),
            "meanLuma": round(luma_val, 4),
        },
        "dominantTone": tone_hex,
        "layoutEligible": True,
    }
    if photo.content_sig:
        entry["contentSig"] = photo.content_sig
    entry["mediaClass"] = classify_media_class(
        path=photo.photo,
        img=photo.img,
        date_source=photo.loaded.date_source,
        asset=entry,
    )
    if tags:
        entry["tags"] = tags
        entry["tagsSource"] = "heuristic"
    if crop_m:
        entry["cropMobile"] = crop_m
    if crop_w:
        entry["cropWeb"] = crop_w
    if geo_obj:
        entry["geo"] = geo_obj
    if place:
        entry["place"] = place
    if photo.burst_group_id:
        entry["burstGroupId"] = photo.burst_group_id
    if subj.salient_box:
        entry["salientBox"] = subj.salient_box
    from travelogue.media.user_tier import apply_user_tier_fields

    apply_user_tier_fields(
        entry,
        tier=photo.user_tier,
        dual_ingest=ctx.dual_ingest,
        import_source=photo.import_source,
    )
    return entry


def _upsert_asset(
    *,
    assets: list[dict],
    replace_index: int | None,
    entry: dict,
) -> None:
    if replace_index is not None:
        assets[replace_index] = entry
        return
    assets.append(entry)


def _ingest_progress_tick(processed: int, total: int) -> bool:
    return (
        processed == 1
        or processed % INGEST_PROGRESS_EVERY_N == 0
        or processed == total
    )


@dataclass
class _IngestScanResult:
    photo_tiers: list[tuple[Path, str]]
    scan_stats: dict[str, Any]
    dual_ingest: bool
    album_root: Path
    checkpoint_keys: set[str]


def _scan_photos_for_ingest(
    *,
    trip: dict,
    trip_dir: Path,
    from_dir: Path | None,
    scan_root: Path,
    cfg: IngestConfig,
    max_photos: int,
    recursive: bool,
    incremental: bool,
    featured_dir: Path | None,
    material_dir: Path | None,
    resume_ingest: bool,
) -> _IngestScanResult:
    from travelogue.media.user_tier import resolve_dual_folders, scan_tiered_image_paths

    feat_dir, mat_dir, tier_mode = resolve_dual_folders(
        scan_root,
        cfg,
        featured_dir=featured_dir,
        material_dir=material_dir,
    )
    if tier_mode == "single" and from_dir:
        photo_tiers, scan_stats = scan_tiered_image_paths(
            featured_dir=None,
            material_dir=None,
            single_dir=from_dir,
            max_photos=max_photos,
            recursive=recursive,
            min_edge_px=cfg.min_edge_px,
        )
    elif from_dir and tier_mode in ("auto", "explicit"):
        photo_tiers, scan_stats = scan_tiered_image_paths(
            featured_dir=feat_dir,
            material_dir=mat_dir,
            single_dir=None,
            max_photos=max_photos,
            recursive=recursive,
            min_edge_px=cfg.min_edge_px,
        )
        scan_stats["tier_mode"] = tier_mode
    elif from_dir:
        photo_tiers, scan_stats = scan_tiered_image_paths(
            featured_dir=None,
            material_dir=None,
            single_dir=from_dir,
            max_photos=max_photos,
            recursive=recursive,
            min_edge_px=cfg.min_edge_px,
        )
    else:
        photos, scan_stats = scan_image_paths(
            scan_root, max_photos=max_photos, recursive=recursive, min_edge_px=cfg.min_edge_px
        )
        photo_tiers = [(p, "material") for p in photos]
        scan_stats.setdefault("mode", "single")

    dual_ingest = scan_stats.get("mode") == "dual"
    album_root = from_dir.resolve() if from_dir else scan_root.resolve()
    checkpoint_keys: set[str] = set()
    if from_dir and resume_ingest:
        checkpoint = icp.load_ingest_checkpoint(trip_dir)
        if checkpoint and str(checkpoint.get("sourceRoot") or "") == str(album_root):
            checkpoint_keys = set(checkpoint.get("processedRelPaths") or [])

    if incremental:
        pipe = trip.get("pipeline") or {}
        pending = set(pipe.get("pendingAssets") or [])
        if pending:
            source_dir = trip_dir / "source"
            assets_by_id = {a["id"]: a for a in trip.get("assets") or []}
            photo_tiers = []
            for aid in sorted(pending):
                a = assets_by_id.get(aid)
                if not a:
                    continue
                src_name = Path(a.get("sourceFile", "")).name
                p = source_dir / src_name
                if p.is_file():
                    tier = a.get("userTier") or "material"
                    photo_tiers.append((p, tier))

    return _IngestScanResult(
        photo_tiers=photo_tiers,
        scan_stats=scan_stats,
        dual_ingest=dual_ingest,
        album_root=album_root,
        checkpoint_keys=checkpoint_keys,
    )


def _apply_ingest_pipeline_state(
    *,
    trip: dict,
    batch: str,
    assets: list[dict],
    existing_asset_ids: set[str],
    pipeline_was_locked: bool,
    incremental: bool,
    prev_status: str,
    prev_locks: dict,
    ingest_stats: dict,
) -> None:
    pipe = trip.setdefault("pipeline", {})
    new_asset_ids = [
        str(a["id"])
        for a in assets
        if a.get("id") and str(a["id"]) not in existing_asset_ids
    ]
    if pipeline_was_locked and not incremental:
        pipe["status"] = prev_status or "structure_locked"
        if prev_locks:
            pipe["locks"] = prev_locks
        else:
            pipe.setdefault("locks", {"structure": True, "copy": False})
        pipe["lastBatchId"] = batch
        append_pending_assets(trip, new_asset_ids)
        ingest_stats["pendingAssetsAppended"] = len(new_asset_ids)
        ingest_stats["pendingAssetsTotal"] = len(pipe.get("pendingAssets") or [])
        ingest_stats["pipelineLocked"] = True
    elif pipeline_was_locked and incremental:
        pipe["status"] = prev_status or "structure_locked"
        if prev_locks:
            pipe["locks"] = prev_locks
        else:
            pipe.setdefault("locks", {"structure": True, "copy": False})
        pipe["lastBatchId"] = batch
        pipe["pendingAssets"] = []
        ingest_stats["pendingAssetsAppended"] = 0
        ingest_stats["pendingAssetsTotal"] = 0
        ingest_stats["pipelineLocked"] = True
    else:
        pipe["status"] = "ingest_ready"
        pipe["lastBatchId"] = batch
        pipe["pendingAssets"] = []
        pipe.setdefault("locks", {"structure": False, "copy": False})
    pipe.setdefault("runs", []).append(
        {
            "runId": batch,
            "agent": "media_lab",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": None,
        }
    )
    trip["updatedAt"] = _utc_now_iso()
    eligible = [a for a in assets if a.get("layoutEligible", True)]
    if not trip.get("coverAssetId") and eligible:
        trip["coverAssetId"] = eligible[0]["id"]


@dataclass
class _IngestLoopState:
    known_md5: set[str]
    dhash_refs: list[tuple[str, int]]
    assets: list[dict]
    ingest_stats: dict
    last_burst: tuple[float, int, int] | None
    last_kept_ts: float | None
    burst_counter: int
    current_burst_group: str | None
    added: int
    skipped: int
    checkpoint_keys: set[str]
    elapsed_acc: dict[str, float]


def _process_one_ingest_photo(
    *,
    photo: Path,
    user_tier: str,
    state: _IngestLoopState,
    build_ctx: IngestAssetBuildContext,
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
    emit_progress: Callable[[], None],
) -> None:
    # ADR-011: user_tier imports ingest symbols — keep lazy here.
    from travelogue.media.user_tier import (
        preserve_material_import_source_on_dedupe,
        preserve_user_tier_on_replace,
        preserve_user_tier_source_on_replace,
        upgrade_asset_tier,
    )

    sig = _file_signature(photo)
    t_dedupe = time.monotonic()
    if dedupe and sig in state.known_md5:
        state.elapsed_acc["dedupe"] = state.elapsed_acc.get("dedupe", 0.0) + (
            time.monotonic() - t_dedupe
        ) * 1000.0
        if upgrade_asset_tier(state.assets, sig, tier=user_tier):
            state.ingest_stats["tier_upgraded"] = state.ingest_stats.get("tier_upgraded", 0) + 1
        elif preserve_material_import_source_on_dedupe(
            state.assets, sig, tier=user_tier
        ):
            state.ingest_stats["import_source_material_preserved"] = (
                state.ingest_stats.get("import_source_material_preserved", 0) + 1
            )
        state.ingest_stats["deduped"] += 1
        state.skipped += 1
        if _ingest_progress_tick(processed, total_photos):
            emit_progress()
        return

    t_decode = time.monotonic()
    try:
        loaded = _load_photo(photo)
    except IngestError:
        state.elapsed_acc["decode"] = state.elapsed_acc.get("decode", 0.0) + (
            time.monotonic() - t_decode
        ) * 1000.0
        state.skipped += 1
        if _ingest_progress_tick(processed, total_photos):
            emit_progress()
        return

    state.elapsed_acc["decode"] = state.elapsed_acc.get("decode", 0.0) + (
        time.monotonic() - t_decode
    ) * 1000.0

    img = loaded.image
    sharp = sharpness_score(img)
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
                state.ingest_stats["deduped_burst"] += 1
                state.skipped += 1
                if _ingest_progress_tick(processed, total_photos):
                    emit_progress()
                return
        else:
            state.ingest_stats["deduped_burst"] += 1
            state.skipped += 1
            if _ingest_progress_tick(processed, total_photos):
                emit_progress()
            return

    dhash = dhash_hex(img)
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
                state.ingest_stats["deduped_phash"] += 1
                state.skipped += 1
                if _ingest_progress_tick(processed, total_photos):
                    emit_progress()
                return

    if replace_index is None:
        state.known_md5.add(sig)
        state.dhash_refs.append((dhash, len(state.assets)))
        asset_id = _next_asset_id(state.assets)
    else:
        state.known_md5.add(sig)
        asset_id = state.assets[replace_index]["id"]
        for i, (dh, idx) in enumerate(state.dhash_refs):
            if idx == replace_index:
                state.dhash_refs[i] = (dhash, replace_index)
                break

    ts = loaded.taken_at.timestamp()
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

    entry = _build_asset_entry(
        build_ctx,
        IngestPhotoPayload(
            asset_id=asset_id,
            photo=photo,
            loaded=loaded,
            img=img,
            dhash=dhash,
            sharpness=sharp,
            burst_group_id=state.current_burst_group,
            content_sig=sig,
            user_tier=tier_for_entry,
            import_source=replace_import_source,
        ),
    )
    if replace_tier_source:
        entry["userTierSource"] = replace_tier_source

    _upsert_asset(
        assets=state.assets,
        replace_index=replace_index,
        entry=entry,
    )

    state.last_burst = (ts, img.width, img.height)
    short_edge = min(img.width, img.height)
    if short_edge < cfg.min_short_edge_layout_px:
        state.ingest_stats.setdefault("suspected_thumbnail_ids", []).append(asset_id)
    if replace_index is None:
        state.added += 1
    if on_asset_added is not None:
        on_asset_added(entry)
    state.ingest_stats[f"{loaded.date_source}_dates"] = (
        state.ingest_stats.get(f"{loaded.date_source}_dates", 0) + 1
    )
    if loaded.had_exif_orientation:
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
            if on_persist:
                on_persist()

    if _ingest_progress_tick(processed, total_photos):
        emit_progress()


def _finalize_ingest_assets(
    *,
    trip: dict,
    trip_dir: Path,
    assets: list[dict],
    ingest_stats: dict,
    cfg: IngestConfig,
    min_assets: int,
) -> None:
    if min_assets and len(assets) < min_assets:
        raise IngestError(
            "E_INGEST_TOO_FEW",
            f"need at least {min_assets} assets in trip after ingest (have {len(assets)})",
        )

    missing_derivatives = _missing_derivative_paths(trip_dir, assets)
    if missing_derivatives:
        aid, rel = missing_derivatives[0]
        raise IngestError(
            "E_INGEST_DERIVATIVE_MISSING",
            f"{aid}: missing {rel}",
        )

    refine_archive_media_class(assets)
    trip["assets"] = assets
    for w in apply_meta_dates_from_assets(trip):
        ingest_stats.setdefault("date_warnings", []).append(w)

    from travelogue.services.copy_subject import narrative_copy_subject

    meta = trip.get("meta") or {}
    journey_place = narrative_copy_subject(
        meta,
        intent=trip.get("intent"),
        assets=assets,
    )
    journey_hint = preview_multi_journey(assets, place=journey_place)
    if journey_hint:
        ingest_stats.setdefault("journey_hints", []).append(journey_hint)

    from travelogue.media.user_tier import count_user_tiers

    ingest_stats["mediaClassSummary"] = summarize_media_classes(assets)
    ingest_stats["userTierSummary"] = count_user_tiers(assets)
    featured_n = ingest_stats["userTierSummary"].get("featured", 0)
    if featured_n > cfg.warn_featured_count_above:
        ingest_stats.setdefault("tier_warnings", []).append(
            f"精选照片 {featured_n} 张，超过建议上限 {cfg.warn_featured_count_above}（仍已导入）"
        )

    low_res_warn = apply_layout_eligibility_marks(trip, assets, cfg=cfg)
    excluded = (trip.get("curation") or {}).get("excludedLowResAssetIds") or []
    if excluded:
        ingest_stats["low_res_excluded_ids"] = list(excluded)
        ingest_stats["low_res_excluded_count"] = len(excluded)
        if low_res_warn:
            ingest_stats["low_res_excluded_warn"] = low_res_warn


def ingest_into_trip(
    trip: dict,
    trip_dir: Path,
    *,
    from_dir: Path | None = None,
    batch_id: str | None = None,
    max_photos: int | None = None,
    recursive: bool = True,
    generate_crops: bool | None = None,
    dedupe: bool = True,
    incremental: bool = False,
    cfg: IngestConfig | None = None,
    app_cfg: AppConfig | None = None,
    featured_dir: Path | None = None,
    material_dir: Path | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    resume_ingest: bool = True,
    on_persist: Callable[[], None] | None = None,
    on_asset_added: Callable[[dict], None] | None = None,
    min_assets: int = INGEST_MIN_ASSETS_DEFAULT,
) -> IngestResult:
    """
    Import images into trip_dir/source + assets; append trip.assets[].

    Does not assign chapters (run curate after).
    """
    resolved_app = app_cfg or get_config()
    cfg = cfg or resolved_app.ingest
    max_photos = max_photos if max_photos is not None else cfg.max_photos
    if generate_crops is None:
        generate_crops = cfg.generate_crops
    geocode_enabled = resolved_app.geocode.enabled
    max_tags = resolved_app.vision.max_tags_per_asset if resolved_app.vision.enabled == "true" else 5

    # F-CLU-CACHE-04: capture lock state BEFORE we touch the pipeline so we can decide
    # whether new asset ids go to pendingAssets (post-lock) or replace the batch.
    existing_asset_ids: set[str] = {
        str(a["id"]) for a in (trip.get("assets") or []) if a.get("id")
    }
    pipeline_was_locked = is_pipeline_locked(trip)
    prev_pipe_snapshot = dict(trip.get("pipeline") or {})
    prev_status = str(prev_pipe_snapshot.get("status") or "")
    prev_locks = dict(prev_pipe_snapshot.get("locks") or {})

    source_dir = trip_dir / "source"
    assets_dir = trip_dir / "assets"
    source_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    scan_root = from_dir or source_dir
    if from_dir:
        raw_stats = guard_raw_in_directory(from_dir, cfg, recursive=recursive)
    else:
        raw_stats = guard_raw_in_directory(scan_root, cfg, recursive=recursive)
    scan = _scan_photos_for_ingest(
        trip=trip,
        trip_dir=trip_dir,
        from_dir=from_dir,
        scan_root=scan_root,
        cfg=cfg,
        max_photos=max_photos,
        recursive=recursive,
        incremental=incremental,
        featured_dir=featured_dir,
        material_dir=material_dir,
        resume_ingest=resume_ingest,
    )
    photo_tiers = scan.photo_tiers
    scan_stats = scan.scan_stats
    dual_ingest = scan.dual_ingest
    album_root = scan.album_root
    checkpoint_keys = scan.checkpoint_keys

    batch = batch_id or f"batch-{datetime.now().strftime('%Y%m%d-%H%M')}"
    known_md5 = _existing_md5_sigs(trip) if dedupe else set()
    dhash_refs: list[tuple[str, int]] = _existing_dhash_refs(trip) if dedupe else []
    assets: list[dict] = list(trip.get("assets") or [])
    ingest_stats = {
        "exif_dates": 0,
        "filename_dates": 0,
        "mtime_dates": 0,
        "exif_rotations": 0,
        "deduped": 0,
        "deduped_phash": 0,
        "deduped_burst": 0,
        "deduped_phash_replaced": 0,
        "deduped_burst_replaced": 0,
        **raw_stats,
    }
    ingest_t0 = time.monotonic()
    elapsed_ms: dict[str, float] = {}
    if checkpoint_keys and from_dir:
        before = len(photo_tiers)
        photo_tiers = [
            (photo, tier)
            for photo, tier in photo_tiers
            if icp.source_key(photo, album_root) not in checkpoint_keys
        ]
        ingest_stats["ingestResumedFromCheckpoint"] = len(checkpoint_keys)
        ingest_stats["ingestSkippedCheckpoint"] = before - len(photo_tiers)
    loop_state = _IngestLoopState(
        known_md5=known_md5,
        dhash_refs=dhash_refs,
        assets=assets,
        ingest_stats=ingest_stats,
        last_burst=None,
        last_kept_ts=None,
        burst_counter=0,
        current_burst_group=None,
        added=0,
        skipped=0,
        checkpoint_keys=checkpoint_keys,
        elapsed_acc={},
    )

    build_ctx = IngestAssetBuildContext(
        cfg=cfg,
        assets_dir=assets_dir,
        source_dir=source_dir,
        trip_dir=trip_dir,
        ingest_stats=ingest_stats,
        batch=batch,
        generate_crops=generate_crops,
        max_tags=max_tags,
        geocode_enabled=geocode_enabled,
        dual_ingest=dual_ingest,
        elapsed_acc=loop_state.elapsed_acc,
    )

    total_photos = len(photo_tiers)
    processed = 0

    def _emit_progress() -> None:
        if on_progress and total_photos > 0:
            on_progress(processed, total_photos)

    for photo, user_tier in photo_tiers:
        processed += 1
        _process_one_ingest_photo(
            photo=photo,
            user_tier=user_tier,
            state=loop_state,
            build_ctx=build_ctx,
            cfg=cfg,
            dedupe=dedupe,
            from_dir=from_dir,
            album_root=album_root,
            trip_dir=trip_dir,
            resume_ingest=resume_ingest,
            processed=processed,
            total_photos=total_photos,
            on_persist=on_persist,
            on_asset_added=on_asset_added,
            emit_progress=_emit_progress,
        )

    added = loop_state.added
    skipped = loop_state.skipped
    assets = loop_state.assets
    ingest_stats = loop_state.ingest_stats

    _finalize_ingest_assets(
        trip=trip,
        trip_dir=trip_dir,
        assets=assets,
        ingest_stats=ingest_stats,
        cfg=cfg,
        min_assets=min_assets,
    )
    elapsed_ms["total"] = round((time.monotonic() - ingest_t0) * 1000.0, 2)
    for key, val in loop_state.elapsed_acc.items():
        elapsed_ms[key] = round(val, 2)
    ingest_stats["elapsedMs"] = elapsed_ms
    _apply_ingest_pipeline_state(
        trip=trip,
        batch=batch,
        assets=assets,
        existing_asset_ids=existing_asset_ids,
        pipeline_was_locked=pipeline_was_locked,
        incremental=incremental,
        prev_status=prev_status,
        prev_locks=prev_locks,
        ingest_stats=ingest_stats,
    )

    if from_dir and resume_ingest:
        icp.clear_ingest_checkpoint(trip_dir)

    return IngestResult(
        added=loop_state.added,
        skipped=loop_state.skipped,
        batch_id=batch,
        stats={**scan_stats, **loop_state.ingest_stats, "total_assets": len(loop_state.assets)},
    )
