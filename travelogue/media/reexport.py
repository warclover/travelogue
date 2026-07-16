"""Re-export WebP variants from source/ without re-importing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config import AppConfig, IngestConfig, get_config
from travelogue.media.asset_slots import asset_display_slots
from travelogue.media.image_ops import (
    classify_aspect,
    export_webp_variants,
    focal_from_asset,
)
from travelogue.media.ingest import IngestError, _load_photo
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso


@dataclass
class ReexportResult:
    updated: int = 0
    failed: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def reexport_asset(
    asset: dict,
    trip_dir: Path,
    *,
    slot: str = "media",
    cfg: IngestConfig | None = None,
    app_cfg: AppConfig | None = None,
) -> None:
    """Regenerate displayFile, srcset, cropMobile/cropWeb from source JPEG."""
    resolved = app_cfg or get_config()
    cfg = cfg or resolved.ingest
    from travelogue.media.source_resolve import MediaSourceMissingError, resolve_source_path

    assets_dir = trip_dir / "assets"
    try:
        source_path = resolve_source_path(asset, trip_dir, raise_on_missing=True)
    except MediaSourceMissingError as exc:
        raise IngestError("E_MEDIA_SOURCE_MISSING", str(exc)) from exc
    if source_path is None:
        raise IngestError("E_MEDIA_SOURCE_MISSING", "missing source after resolve")

    loaded = _load_photo(source_path)
    img = loaded.image
    focal = focal_from_asset(asset)
    kind = asset.get("aspectKind") or classify_aspect(img.width, img.height)
    asset["aspectKind"] = kind

    display_rel, srcset_rel, out_w, out_h, crop_m, crop_w = export_webp_variants(
        img,
        assets_dir,
        asset["id"],
        widths=cfg.webp_widths,
        quality=cfg.webp_quality,
        generate_crops=cfg.generate_crops,
        focal=focal,
    )
    asset["displayFile"] = display_rel
    asset["srcset"] = srcset_rel
    asset["nativeWidth"] = img.width
    asset["nativeHeight"] = img.height
    asset["width"] = out_w
    asset["height"] = out_h
    if crop_m:
        asset["cropMobile"] = crop_m
    elif "cropMobile" in asset:
        del asset["cropMobile"]
    if crop_w:
        asset["cropWeb"] = crop_w
    elif "cropWeb" in asset:
        del asset["cropWeb"]


def reexport_trip_assets(
    trip: dict,
    trip_dir: Path,
    *,
    asset_ids: list[str] | None = None,
    cfg: IngestConfig | None = None,
    app_cfg: AppConfig | None = None,
) -> ReexportResult:
    """Re-export some or all image assets (pixels only; chapters unchanged)."""
    resolved = app_cfg or get_config()
    cfg = cfg or resolved.ingest
    slots = asset_display_slots(trip)
    assets = trip.get("assets") or []
    by_id = {a["id"]: a for a in assets if a.get("type") == "image"}
    targets = asset_ids or list(by_id.keys())

    updated = 0
    failed: list[str] = []
    for aid in targets:
        asset = by_id.get(aid)
        if not asset:
            failed.append(f"{aid}:not_found")
            continue
        try:
            reexport_asset(asset, trip_dir, slot=slots.get(aid, "media"), cfg=cfg)
            updated += 1
        except (IngestError, OSError) as exc:
            failed.append(f"{aid}:{exc}")

    trip["updatedAt"] = _utc_now_iso()
    return ReexportResult(updated=updated, failed=failed, stats={"requested": len(targets)})
