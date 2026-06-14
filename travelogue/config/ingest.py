"""Ingest pipeline configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_RAW_BLOCKLIST_SUFFIXES: tuple[str, ...] = (
    ".cr2",
    ".cr3",
    ".nef",
    ".nrw",
    ".arw",
    ".srf",
    ".sr2",
    ".dng",
    ".rw2",
    ".orf",
    ".raf",
    ".pef",
    ".x3f",
    ".kdc",
    ".erf",
    ".3fr",
    ".iiq",
)


@dataclass
class IngestConfig:
    max_photos: int = 250
    webp_widths: tuple[int, ...] = (800, 1600, 2400, 3200)
    webp_quality: int = 82
    webp_method: int = 4
    shared_color_thumb_px: int = 32
    generate_crops: bool = False
    min_edge_px: int = 320
    phash_threshold: int = 8
    burst_seconds: float = 3.0
    dedupe_phash: bool = True
    dedupe_burst: bool = True
    min_long_edge_layout_px: int = 800
    min_short_edge_layout_px: int = 600
    low_res_median_ratio: float = 0.55
    low_res_min_megapixels: float = 0.8
    low_res_mp_ratio: float = 0.45
    low_res_circuit_breaker_ratio: float = 0.25
    low_res_circuit_breaker_median_short_px: int = 1200
    detect_faces: bool = True
    face_min_size_px: int = 48
    face_detect_max_edge: int = 0
    featured_dir_names: tuple[str, ...] = ("主图上传", "精选", "featured", "hero")
    material_dir_names: tuple[str, ...] = ("素材上传", "素材", "material", "extras")
    featured_priority_on_truncation: bool = True
    warn_featured_count_above: int = 30
    reject_raw: bool = True
    raw_blocklist_suffixes: tuple[str, ...] = DEFAULT_RAW_BLOCKLIST_SUFFIXES
    raw_detect_sample_limit: int = 5
    sharpness_version: str = "v2"  # v1 | v2
    exif_camera: bool = True


def ingest_from_dict(raw: dict[str, Any]) -> IngestConfig:
    widths = raw.get("webp_widths") or [800, 1600, 2400, 3200]
    raw_suffixes = raw.get("raw_blocklist_suffixes") or raw.get("rawBlocklistSuffixes")
    if isinstance(raw_suffixes, list) and raw_suffixes:
        suffixes = tuple(str(s).lower() if str(s).startswith(".") else f".{str(s).lower()}" for s in raw_suffixes)
    else:
        suffixes = DEFAULT_RAW_BLOCKLIST_SUFFIXES
    return IngestConfig(
        max_photos=int(raw.get("max_photos", 250)),
        webp_widths=tuple(int(w) for w in widths),
        webp_quality=int(raw.get("webp_quality", 82)),
        webp_method=int(raw.get("webp_method", 4)),
        shared_color_thumb_px=int(raw.get("shared_color_thumb_px", raw.get("sharedColorThumbPx", 32))),
        generate_crops=bool(raw.get("generate_crops", False)),
        min_edge_px=int(raw.get("min_edge_px", 320)),
        phash_threshold=int(raw.get("phash_threshold", 8)),
        burst_seconds=float(raw.get("burst_seconds", 3.0)),
        dedupe_phash=bool(raw.get("dedupe_phash", True)),
        dedupe_burst=bool(raw.get("dedupe_burst", True)),
        min_long_edge_layout_px=int(raw.get("min_long_edge_layout_px", 800)),
        min_short_edge_layout_px=int(raw.get("min_short_edge_layout_px", 600)),
        low_res_median_ratio=float(raw.get("low_res_median_ratio", 0.55)),
        low_res_min_megapixels=float(raw.get("low_res_min_megapixels", 0.8)),
        low_res_mp_ratio=float(raw.get("low_res_mp_ratio", 0.45)),
        low_res_circuit_breaker_ratio=float(raw.get("low_res_circuit_breaker_ratio", 0.25)),
        low_res_circuit_breaker_median_short_px=int(
            raw.get("low_res_circuit_breaker_median_short_px", 1200)
        ),
        detect_faces=bool(raw.get("detect_faces", True)),
        face_min_size_px=int(raw.get("face_min_size_px", 48)),
        face_detect_max_edge=int(raw.get("face_detect_max_edge", raw.get("faceDetectMaxEdge", 0))),
        featured_dir_names=tuple(str(x) for x in (raw.get("featured_dir_names") or ["主图上传", "精选", "featured", "hero"])),
        material_dir_names=tuple(str(x) for x in (raw.get("material_dir_names") or ["素材上传", "素材", "material", "extras"])),
        featured_priority_on_truncation=bool(raw.get("featured_priority_on_truncation", True)),
        warn_featured_count_above=int(raw.get("warn_featured_count_above", 30)),
        reject_raw=bool(raw.get("reject_raw", raw.get("rejectRaw", True))),
        raw_blocklist_suffixes=suffixes,
        raw_detect_sample_limit=int(raw.get("raw_detect_sample_limit", raw.get("rawDetectSampleLimit", 5))),
        sharpness_version=str(
            raw.get("sharpness_version", raw.get("sharpnessVersion", "v2"))
        ).lower(),
        exif_camera=bool(raw.get("exif_camera", raw.get("exifCamera", True))),
    )
