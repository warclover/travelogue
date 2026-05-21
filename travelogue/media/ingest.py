"""Agent 0 · Media Lab — import photos into trip workspace."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from travelogue.config import IngestConfig, get_config
from travelogue.media.image_ops import (
    classify_aspect,
    export_webp_variants,
    filter_trip_dates,
    load_image_normalized,
    min_dimension_ok,
    save_jpeg_without_exif,
)
from travelogue.media.phash import dhash_hex, is_near_duplicate

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
    max_photos: int = 50,
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
        gid = a.get("dedupeGroupId") or ""
        if gid.startswith("md5:"):
            sigs.add(gid[4:])
        elif gid and ":" not in gid:
            sigs.add(gid)
    return sigs


def _existing_dhashes(trip: dict) -> list[str]:
    out: list[str] = []
    for a in trip.get("assets") or []:
        gid = a.get("dedupeGroupId") or ""
        if gid.startswith("dhash:"):
            out.append(gid[6:])
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
    cfg = cfg or get_config().ingest
    max_photos = max_photos if max_photos is not None else cfg.max_photos
    if generate_crops is None:
        generate_crops = cfg.generate_crops

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
    known_dhashes = _existing_dhashes(trip) if dedupe else []
    assets: list[dict] = list(trip.get("assets") or [])
    dates: list[date] = []
    date_sources: list[str] = []
    ingest_stats = {
        "exif_dates": 0,
        "filename_dates": 0,
        "mtime_dates": 0,
        "exif_rotations": 0,
        "deduped": 0,
        "deduped_phash": 0,
        "deduped_burst": 0,
    }
    added = 0
    skipped = 0
    last_burst: tuple[float, int, int] | None = None

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
        use_burst = dedupe and cfg.dedupe_burst
        use_phash = dedupe and cfg.dedupe_phash
        if use_burst and _is_burst_duplicate(
            loaded, last=last_burst, burst_seconds=cfg.burst_seconds
        ):
            ingest_stats["deduped_burst"] += 1
            skipped += 1
            continue

        dhash = dhash_hex(img)
        degenerate = dhash == "0000000000000000"
        if (
            use_phash
            and not degenerate
            and any(is_near_duplicate(dhash, h, threshold=cfg.phash_threshold) for h in known_dhashes)
        ):
            ingest_stats["deduped_phash"] += 1
            skipped += 1
            continue

        known_md5.add(sig)
        known_dhashes.append(dhash)
        last_burst = (loaded.taken_at.timestamp(), img.width, img.height)

        asset_id = _next_asset_id(assets)
        aspect_kind = classify_aspect(img.width, img.height)
        focal = (0.5, 0.45)

        dest_source = source_dir / f"{asset_id}.jpg"
        if photo.resolve() != dest_source.resolve():
            save_jpeg_without_exif(img, dest_source)
        elif not dest_source.is_file():
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

        entry: dict = {
            "id": asset_id,
            "type": "image",
            "sourceFile": f"source/{dest_source.name}",
            "displayFile": display_rel,
            "srcset": srcset_rel,
            "width": out_w,
            "height": out_h,
            "aspectKind": aspect_kind,
            "takenAt": loaded.taken_at.replace(tzinfo=None).isoformat() + "Z",
            "ingestBatchId": batch,
            "dedupeGroupId": f"dhash:{dhash}",
            "focalPoint": {"x": focal[0], "y": focal[1]},
        }
        if crop_m:
            entry["cropMobile"] = crop_m
        if crop_w:
            entry["cropWeb"] = crop_w

        assets.append(entry)
        added += 1
        dates.append(loaded.taken_at.date())
        date_sources.append(loaded.date_source)
        ingest_stats[f"{loaded.date_source}_dates"] = (
            ingest_stats.get(f"{loaded.date_source}_dates", 0) + 1
        )
        if loaded.had_exif_orientation:
            ingest_stats["exif_rotations"] += 1

    if added == 0 and len(assets) < 4:
        raise IngestError(
            "E_INGEST_TOO_FEW",
            f"need at least 4 assets in trip after ingest (have {len(assets)})",
        )

    trip["assets"] = assets
    meta = trip.setdefault("meta", {})
    if dates:
        dates = filter_trip_dates(dates, sources=date_sources)
        dates.sort()
        meta["dateStart"] = dates[0].isoformat()
        meta["dateEnd"] = dates[-1].isoformat()

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
    if not trip.get("coverAssetId") and assets:
        trip["coverAssetId"] = assets[0]["id"]

    return IngestResult(
        added=added,
        skipped=skipped,
        batch_id=batch,
        stats={**scan_stats, **ingest_stats, "total_assets": len(assets)},
    )
