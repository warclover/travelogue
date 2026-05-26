"""Agent 0 · Media Lab — import photos into trip workspace."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from travelogue.config import IngestConfig, get_config
from travelogue.curation.asset_quality import apply_layout_eligibility_marks, asset_sharpness
from travelogue.media.heuristic_tags import build_heuristic_tags
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


class IngestError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class IngestResult:
    added: int = 0
    skipped: int = 0
    batch_id: str = ""
    stats: dict = field(default_factory=dict)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
) -> tuple[list[Path], dict]:
    if not directory.is_dir():
        raise IngestError("E_INGEST_NOT_DIR", f"not a directory: {directory}")

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

    stats = {"skipped_small": 0, "skipped_open": 0}
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


def _build_asset_entry(
    *,
    asset_id: str,
    photo: Path,
    loaded,
    img: Image.Image,
    batch: str,
    dhash: str,
    cfg: IngestConfig,
    assets_dir: Path,
    source_dir: Path,
    generate_crops: bool,
    burst_group_id: str | None,
    sharpness: float,
    max_tags: int,
    geocode_enabled: bool,
    trip_dir: Path,
    ingest_stats: dict,
    content_sig: str | None = None,
) -> dict:
    from travelogue.media.color_metrics import dominant_tone_hex, mean_luma
    from travelogue.curation.media_classify import classify_media_class, date_confidence_for_source
    from travelogue.media.subject_detect import analyze_subject

    aspect_kind = classify_aspect(img.width, img.height)
    focal = (0.5, 0.45)
    subj = analyze_subject(img, min_face_size=cfg.face_min_size_px, enabled=cfg.detect_faces)
    if subj.has_face:
        focal = subj.focal
        ingest_stats["faces_detected"] = ingest_stats.get("faces_detected", 0) + 1

    dest_source = source_dir / f"{asset_id}.jpg"
    if photo.resolve() != dest_source.resolve() or not dest_source.is_file():
        save_jpeg_without_exif(img, dest_source)

    display_rel, srcset_rel, out_w, out_h, crop_m, crop_w = export_webp_variants(
        img,
        assets_dir,
        asset_id,
        widths=cfg.webp_widths,
        quality=cfg.webp_quality,
        generate_crops=generate_crops,
        focal=focal,
    )

    geo_obj, place = _resolve_place_city(loaded, trip_dir=trip_dir, geocode_enabled=geocode_enabled)
    if geo_obj:
        ingest_stats["gps_assets"] = ingest_stats.get("gps_assets", 0) + 1

    tags = build_heuristic_tags(
        taken_at=loaded.taken_at,
        aspect_kind=aspect_kind,
        subject_tags=subj.tags,
        place_city=(place or {}).get("city") if place else None,
        max_tags=max_tags,
    )

    entry: dict = {
        "id": asset_id,
        "type": "image",
        "sourceFile": f"source/{dest_source.name}",
        "displayFile": display_rel,
        "srcset": srcset_rel,
        "nativeWidth": img.width,
        "nativeHeight": img.height,
        "width": out_w,
        "height": out_h,
        "aspectKind": aspect_kind,
        "takenAt": loaded.taken_at.replace(tzinfo=None).isoformat() + "Z",
        "dateSource": loaded.date_source,
        "dateConfidence": date_confidence_for_source(loaded.date_source),
        "ingestBatchId": batch,
        "dedupeGroupId": f"dhash:{dhash}",
        "focalPoint": {"x": focal[0], "y": focal[1]},
        "quality": {
            "sharpness": round(sharpness, 2),
            "meanLuma": round(mean_luma(img), 4),
        },
        "dominantTone": dominant_tone_hex(img),
        "layoutEligible": True,
    }
    if content_sig:
        entry["contentSig"] = content_sig
    entry["mediaClass"] = classify_media_class(
        path=photo,
        img=img,
        date_source=loaded.date_source,
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
    if burst_group_id:
        entry["burstGroupId"] = burst_group_id
    if subj.salient_box:
        entry["salientBox"] = subj.salient_box
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
) -> IngestResult:
    """
    Import images into trip_dir/source + assets; append trip.assets[].

    Does not assign chapters (run curate after).
    """
    app_cfg = get_config()
    cfg = cfg or app_cfg.ingest
    max_photos = max_photos if max_photos is not None else cfg.max_photos
    if generate_crops is None:
        generate_crops = cfg.generate_crops
    geocode_enabled = app_cfg.geocode.enabled
    max_tags = app_cfg.vision.max_tags_per_asset if app_cfg.vision.enabled else 5

    source_dir = trip_dir / "source"
    assets_dir = trip_dir / "assets"
    source_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    scan_root = from_dir or source_dir
    if from_dir:
        photos, scan_stats = scan_image_paths(
            from_dir, max_photos=max_photos, recursive=recursive, min_edge_px=cfg.min_edge_px
        )
    else:
        photos, scan_stats = scan_image_paths(
            scan_root, max_photos=max_photos, recursive=recursive, min_edge_px=cfg.min_edge_px
        )

    pipe = trip.setdefault("pipeline", {})
    if incremental:
        pending = set(pipe.get("pendingAssets") or [])
        if pending:
            assets_by_id = {a["id"]: a for a in trip.get("assets") or []}
            photos = []
            for aid in sorted(pending):
                a = assets_by_id.get(aid)
                if not a:
                    continue
                src_name = Path(a.get("sourceFile", "")).name
                p = source_dir / src_name
                if p.is_file():
                    photos.append(p)

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
    }
    added = 0
    skipped = 0
    last_burst: tuple[float, int, int] | None = None
    last_kept_ts: float | None = None
    burst_counter = 0
    current_burst_group: str | None = None

    for photo in photos:
        sig = _file_signature(photo)
        if dedupe and sig in known_md5:
            ingest_stats["deduped"] += 1
            skipped += 1
            continue

        try:
            loaded = _load_photo(photo)
        except IngestError:
            skipped += 1
            continue

        img = loaded.image
        sharp = sharpness_score(img)
        use_burst = dedupe and cfg.dedupe_burst
        use_phash = dedupe and cfg.dedupe_phash
        replace_index: int | None = None

        if use_burst and _is_burst_duplicate(
            loaded, last=last_burst, burst_seconds=cfg.burst_seconds
        ):
            if assets:
                prev_sharp = asset_sharpness(assets[-1])
                if sharp > prev_sharp:
                    replace_index = len(assets) - 1
                    ingest_stats["deduped_burst_replaced"] += 1
                else:
                    ingest_stats["deduped_burst"] += 1
                    skipped += 1
                    continue
            else:
                ingest_stats["deduped_burst"] += 1
                skipped += 1
                continue

        dhash = dhash_hex(img)
        degenerate = dhash == "0000000000000000"
        if use_phash and not degenerate and replace_index is None:
            match_idx = _find_phash_asset_index(
                dhash, dhash_refs, threshold=cfg.phash_threshold
            )
            if match_idx is not None:
                prev_sharp = asset_sharpness(assets[match_idx])
                if sharp > prev_sharp:
                    replace_index = match_idx
                    ingest_stats["deduped_phash_replaced"] += 1
                else:
                    ingest_stats["deduped_phash"] += 1
                    skipped += 1
                    continue

        if replace_index is None:
            known_md5.add(sig)
            dhash_refs.append((dhash, len(assets)))
            asset_id = _next_asset_id(assets)
        else:
            known_md5.add(sig)
            asset_id = assets[replace_index]["id"]
            for i, (dh, idx) in enumerate(dhash_refs):
                if idx == replace_index:
                    dhash_refs[i] = (dhash, replace_index)
                    break

        ts = loaded.taken_at.timestamp()
        if last_kept_ts is None or abs(ts - last_kept_ts) > cfg.burst_seconds:
            burst_counter += 1
            current_burst_group = f"burst-{burst_counter:03d}"
        last_kept_ts = ts

        entry = _build_asset_entry(
            asset_id=asset_id,
            photo=photo,
            loaded=loaded,
            img=img,
            batch=batch,
            dhash=dhash,
            cfg=cfg,
            assets_dir=assets_dir,
            source_dir=source_dir,
            generate_crops=generate_crops,
            burst_group_id=current_burst_group,
            sharpness=sharp,
            max_tags=max_tags,
            geocode_enabled=geocode_enabled,
            trip_dir=trip_dir,
            ingest_stats=ingest_stats,
            content_sig=sig,
        )

        _upsert_asset(
            assets=assets,
            replace_index=replace_index,
            entry=entry,
        )

        last_burst = (ts, img.width, img.height)
        short_edge = min(img.width, img.height)
        if short_edge < cfg.min_short_edge_layout_px:
            ingest_stats.setdefault("suspected_thumbnail_ids", []).append(asset_id)
        if replace_index is None:
            added += 1
        ingest_stats[f"{loaded.date_source}_dates"] = (
            ingest_stats.get(f"{loaded.date_source}_dates", 0) + 1
        )
        if loaded.had_exif_orientation:
            ingest_stats["exif_rotations"] += 1

    if len(assets) < 4:
        raise IngestError(
            "E_INGEST_TOO_FEW",
            f"need at least 4 assets in trip after ingest (have {len(assets)})",
        )

    missing_derivatives = _missing_derivative_paths(trip_dir, assets)
    if missing_derivatives:
        aid, rel = missing_derivatives[0]
        raise IngestError(
            "E_INGEST_DERIVATIVE_MISSING",
            f"{aid}: missing {rel}",
        )

    from travelogue.curation.media_classify import refine_archive_media_class, summarize_media_classes
    from travelogue.media.trip_dates import apply_meta_dates_from_assets

    refine_archive_media_class(assets)
    trip["assets"] = assets
    for w in apply_meta_dates_from_assets(trip):
        ingest_stats.setdefault("date_warnings", []).append(w)

    from travelogue.media.ingest_preview import preview_multi_journey

    place = (trip.get("meta") or {}).get("places") or ["旅途"]
    journey_hint = preview_multi_journey(assets, place=place[0] if place else "旅途")
    if journey_hint:
        ingest_stats.setdefault("journey_hints", []).append(journey_hint)

    ingest_stats["mediaClassSummary"] = summarize_media_classes(assets)

    low_res_warn = apply_layout_eligibility_marks(trip, assets, cfg=cfg)
    excluded = (trip.get("curation") or {}).get("excludedLowResAssetIds") or []
    if excluded:
        ingest_stats["low_res_excluded_ids"] = list(excluded)
        ingest_stats["low_res_excluded_count"] = len(excluded)
        if low_res_warn:
            ingest_stats["low_res_excluded_warn"] = low_res_warn

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

    return IngestResult(
        added=added,
        skipped=skipped,
        batch_id=batch,
        stats={**scan_stats, **ingest_stats, "total_assets": len(assets)},
    )
