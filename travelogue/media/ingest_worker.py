"""ProcessPool worker for parallel ingest (Pipeline Throughput · Phase A).

Top-level pickle-safe entrypoint. Must not import services / web / orchestrator /
vision. May lazy-import ``curation.aesthetic_score.compute_aesthetic_signals``
(pure PIL, R3.2). Worker writes provisional Blobs only — never trip.json or
final assetId assignment.
"""

from __future__ import annotations

import hashlib
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkerIngestConfig:
    """Pickle-safe subset of IngestConfig for worker processes."""

    webp_widths: tuple[int, ...] = (800, 1600, 2400, 3200)
    webp_quality: int = 82
    webp_method: int = 2
    shared_color_thumb_px: int = 32
    generate_crops: bool = False
    detect_faces: bool = True
    face_min_size_px: int = 48
    face_detect_max_edge: int = 1024
    sharpness_version: str = "v2"
    exif_camera: bool = True
    portrait_analyze: bool = True
    face_min_size_for_portrait: int = 48
    copy_source_files: bool = True
    webp_pyramid: bool = False
    aesthetic_enabled: bool = True
    aesthetic_thumb_px: int = 32

    @classmethod
    def from_ingest_config(
        cls,
        cfg: Any,
        *,
        portrait_enabled: bool = True,
        force_materialize: bool = False,
        deferred_derivatives: bool = True,
        aesthetic_cfg: Any | None = None,
    ) -> WorkerIngestConfig:
        copy = bool(getattr(cfg, "copy_source_files", True)) or bool(force_materialize)
        from travelogue.media.derivatives import effective_ingest_widths

        widths = effective_ingest_widths(cfg, deferred=bool(deferred_derivatives))
        ae = aesthetic_cfg
        return cls(
            webp_widths=widths,
            webp_quality=int(cfg.webp_quality),
            webp_method=int(cfg.webp_method),
            shared_color_thumb_px=int(cfg.shared_color_thumb_px),
            generate_crops=bool(cfg.generate_crops),
            detect_faces=bool(cfg.detect_faces),
            face_min_size_px=int(cfg.face_min_size_px),
            face_detect_max_edge=int(getattr(cfg, "face_detect_max_edge", 1024) or 0),
            sharpness_version=str(getattr(cfg, "sharpness_version", "v2") or "v2"),
            exif_camera=bool(getattr(cfg, "exif_camera", True)),
            portrait_analyze=bool(getattr(cfg, "portrait_analyze", True)) and portrait_enabled,
            face_min_size_for_portrait=int(cfg.face_min_size_px),
            copy_source_files=copy,
            webp_pyramid=bool(getattr(cfg, "webp_pyramid", False)),
            aesthetic_enabled=bool(getattr(ae, "enabled", True)) if ae is not None else True,
            aesthetic_thumb_px=int(getattr(ae, "thumb_px", 32) or 32) if ae is not None else 32,
        )


@dataclass
class WorkerResult:
    """Pickle-safe per-photo result. No PIL Image; no final assetId."""

    index: int
    source_path: str
    user_tier: str
    provisional_id: str
    error: str | None = None
    content_sig: str | None = None
    taken_at_iso: str | None = None
    taken_at_ts: float | None = None
    date_source: str | None = None
    had_exif_orientation: bool = False
    width: int = 0
    height: int = 0
    dhash: str | None = None
    sharpness: float = 0.0
    sharpness_v2: float | None = None
    focal_x: float = 0.5
    focal_y: float = 0.45
    has_face: bool = False
    face_count: int = 0
    faces: tuple[tuple[int, int, int, int], ...] = ()
    faces_norm: tuple[dict[str, float], ...] = ()
    salient_box: dict[str, float] | None = None
    protect_box: dict[str, float] | None = None
    subject_tags: tuple[str, ...] = ()
    mean_luma: float = 0.0
    dominant_tone: str | None = None
    aspect_kind: str | None = None
    geo_lat: float | None = None
    geo_lon: float | None = None
    exif: dict[str, Any] | None = None
    portrait_quality: dict[str, Any] | None = None
    provisional_source: str | None = None
    provisional_dir: str | None = None
    display_rel: str | None = None
    srcset: list[dict[str, Any]] = field(default_factory=list)
    out_w: int = 0
    out_h: int = 0
    crop_mobile_rel: str | None = None
    crop_web_rel: str | None = None
    provisional_files: list[str] = field(default_factory=list)
    media_class: str | None = None
    aesthetic_signals: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _file_signature(path: Path) -> str:
    st = path.stat()
    digest = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return f"{st.st_size}:{digest.hexdigest()}"


def _register_heif() -> None:
    try:
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def process_ingest_photo_worker(
    *,
    index: int,
    source_path: str,
    user_tier: str,
    provisional_id: str,
    temp_dir: str,
    worker_cfg: WorkerIngestConfig,
) -> WorkerResult:
    """Decode + features + provisional WebP. Never touches trip.json / final assetId."""
    result = WorkerResult(
        index=index,
        source_path=source_path,
        user_tier=user_tier,
        provisional_id=provisional_id,
    )
    try:
        from travelogue.media.color_metrics import color_metrics_from_thumb
        from travelogue.media.image_ops import (
            classify_aspect,
            export_webp_variants,
            load_image_normalized,
            save_jpeg_without_exif,
        )
        from travelogue.media.phash import dhash_hex
        from travelogue.media.sharpness import sharpness_score, sharpness_score_v2
        from travelogue.media.subject_detect import analyze_subject

        _register_heif()
        photo = Path(source_path)
        temp_root = Path(temp_dir)
        prov_dir = temp_root / provisional_id
        source_out_dir = prov_dir / "source"
        assets_out_dir = prov_dir / "assets"
        source_out_dir.mkdir(parents=True, exist_ok=True)
        assets_out_dir.mkdir(parents=True, exist_ok=True)

        result.content_sig = _file_signature(photo)
        loaded = load_image_normalized(photo)
        img = loaded.image
        result.taken_at_iso = loaded.taken_at.replace(tzinfo=None).isoformat() + "Z"
        result.taken_at_ts = float(loaded.taken_at.timestamp())
        result.date_source = str(loaded.date_source)
        result.had_exif_orientation = bool(loaded.had_exif_orientation)
        result.width = int(img.width)
        result.height = int(img.height)
        result.aspect_kind = str(classify_aspect(img.width, img.height))

        result.sharpness = float(sharpness_score(img))
        result.dhash = dhash_hex(img)

        subj = analyze_subject(
            img,
            min_face_size=worker_cfg.face_min_size_px,
            face_detect_max_edge=worker_cfg.face_detect_max_edge,
            enabled=worker_cfg.detect_faces,
        )
        result.has_face = bool(subj.has_face)
        result.face_count = int(subj.face_count)
        result.faces = tuple(subj.faces)
        result.faces_norm = tuple(dict(f) for f in (subj.faces_norm or ()))
        result.salient_box = dict(subj.salient_box) if subj.salient_box else None
        result.protect_box = dict(subj.protect_box) if subj.protect_box else None
        result.subject_tags = tuple(subj.tags)
        result.focal_x = float(subj.focal[0])
        result.focal_y = float(subj.focal[1])

        if worker_cfg.sharpness_version.lower() == "v2":
            roi = subj.salient_box if subj.salient_box else None
            result.sharpness_v2 = float(sharpness_score_v2(img, roi=roi))

        luma, tone = color_metrics_from_thumb(img, thumb_px=worker_cfg.shared_color_thumb_px)
        result.mean_luma = float(luma)
        result.dominant_tone = str(tone)

        if loaded.geo is not None:
            result.geo_lat = float(loaded.geo.lat)
            result.geo_lon = float(loaded.geo.lon)

        if worker_cfg.exif_camera:
            from travelogue.media.exif_camera import read_camera_exif

            exif_obj = read_camera_exif(photo, img)
            if exif_obj:
                result.exif = dict(exif_obj)

        if worker_cfg.portrait_analyze and subj.faces:
            from travelogue.config.portrait import PortraitConfig
            from travelogue.media.portrait_analyze import analyze_portrait

            portrait_cfg = PortraitConfig()
            if portrait_cfg.enabled:
                portrait = analyze_portrait(
                    img,
                    list(subj.faces),
                    cfg=portrait_cfg,
                    min_face_px=worker_cfg.face_min_size_for_portrait,
                )
                result.portrait_quality = portrait.to_quality_dict(cfg=portrait_cfg)

        copy_source = bool(worker_cfg.copy_source_files)
        dest_source = source_out_dir / f"{provisional_id}.jpg"
        if copy_source:
            save_jpeg_without_exif(img, dest_source)
            result.provisional_source = str(dest_source)
        else:
            result.provisional_source = None

        display_rel, srcset_rel, out_w, out_h, crop_m, crop_w = export_webp_variants(
            img,
            assets_out_dir,
            provisional_id,
            widths=worker_cfg.webp_widths,
            quality=worker_cfg.webp_quality,
            webp_method=worker_cfg.webp_method,
            generate_crops=worker_cfg.generate_crops,
            focal=(result.focal_x, result.focal_y),
            pyramid=bool(worker_cfg.webp_pyramid),
        )
        result.display_rel = display_rel
        result.srcset = list(srcset_rel)
        result.out_w = int(out_w)
        result.out_h = int(out_h)
        result.crop_mobile_rel = crop_m
        result.crop_web_rel = crop_w
        result.provisional_dir = str(prov_dir)

        # R3.2 · mediaClass + aesthetic signals on the already-decoded image
        provisional_asset: dict[str, Any] = {
            "id": provisional_id,
            "width": result.width,
            "height": result.height,
            "quality": {
                "meanLuma": result.mean_luma,
                "hasFace": result.has_face,
                "faceCount": result.face_count,
            },
            "salientBox": result.salient_box,
            "protectBox": result.protect_box,
            "faces": list(result.faces_norm) if result.faces_norm else [],
        }
        from travelogue.media.media_classify import classify_media_class

        result.media_class = classify_media_class(
            path=photo,
            img=img,
            date_source=result.date_source or "mtime",
            asset=provisional_asset,
        )
        if worker_cfg.aesthetic_enabled:
            from travelogue.config import AestheticConfig
            from travelogue.curation.aesthetic_score import compute_aesthetic_signals

            ae_cfg = AestheticConfig(thumb_px=int(worker_cfg.aesthetic_thumb_px))
            signals = compute_aesthetic_signals(img, provisional_asset, cfg=ae_cfg)
            result.aesthetic_signals = {str(k): float(v) for k, v in signals.items()}

        files: list[str] = []
        if copy_source:
            files.append(str(dest_source))
        for entry in srcset_rel:
            rel = entry.get("file") if isinstance(entry, dict) else None
            if isinstance(rel, str) and rel.startswith("assets/"):
                files.append(str(assets_out_dir / Path(rel).name))
        if crop_m and crop_m.startswith("assets/"):
            files.append(str(assets_out_dir / Path(crop_m).name))
        if crop_w and crop_w.startswith("assets/"):
            files.append(str(assets_out_dir / Path(crop_w).name))
        result.provisional_files = files
    except Exception as exc:  # noqa: BLE001 — worker must always return pickle-safe result
        result.error = f"{type(exc).__name__}: {exc}"
        result.provisional_files = list(result.provisional_files)
        # Keep traceback out of hot path logs; tests can inspect error string.
        _ = traceback.format_exc()
    return result


def process_ingest_photo_worker_star(args: tuple[Any, ...]) -> WorkerResult:
    """Star-args wrapper for ProcessPoolExecutor.map / submit."""
    index, source_path, user_tier, provisional_id, temp_dir, worker_cfg = args
    return process_ingest_photo_worker(
        index=int(index),
        source_path=str(source_path),
        user_tier=str(user_tier),
        provisional_id=str(provisional_id),
        temp_dir=str(temp_dir),
        worker_cfg=worker_cfg,
    )


def cleanup_provisional_files(result: WorkerResult) -> None:
    """Delete provisional blobs for discarded / failed worker outputs."""
    for path_str in list(result.provisional_files or []):
        path = Path(path_str)
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass
    if result.provisional_dir:
        prov = Path(result.provisional_dir)
        for sub in ("assets", "source"):
            d = prov / sub
            if d.is_dir():
                for child in d.iterdir():
                    try:
                        if child.is_file():
                            child.unlink()
                    except OSError:
                        pass
                try:
                    d.rmdir()
                except OSError:
                    pass
        try:
            if prov.is_dir():
                prov.rmdir()
        except OSError:
            pass
