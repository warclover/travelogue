"""Dual-folder ingest · userTier (PRD-EXPERIENCE appendix A · E5)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from travelogue.config import IngestConfig
from travelogue.media.image_ops import min_edge_ok
from travelogue.media.ingest import (
    HEIC_SUFFIXES,
    IMAGE_SUFFIXES,
    IngestError,
    _peek_photo,
)

TIER_FEATURED = "featured"
TIER_MATERIAL = "material"
TIER_SOURCE_INGEST = "ingest"
TIER_SOURCE_USER = "user"
IMPORT_SOURCE_FEATURED = "featured"
IMPORT_SOURCE_MATERIAL = "material"
IMPORT_SOURCE_LEGACY = "legacy"
DEFAULT_FEATURED_DIR_NAMES = ("主图上传", "精选", "featured", "hero")
DEFAULT_MATERIAL_DIR_NAMES = ("素材上传", "素材", "material", "extras")


def _norm_names(names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(str(n).strip() for n in names if str(n).strip())


def find_tier_subdir(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.is_dir():
            return candidate
    return None


def resolve_dual_folders(
    root: Path,
    cfg: IngestConfig,
    *,
    featured_dir: Path | None = None,
    material_dir: Path | None = None,
) -> tuple[Path | None, Path | None, str]:
    """Return (featured, material, mode) where mode is explicit|auto|single."""
    if featured_dir or material_dir:
        feat = featured_dir.resolve() if featured_dir else None
        mat = material_dir.resolve() if material_dir else None
        if feat and not feat.is_dir():
            raise IngestError("E_INGEST_NOT_DIR", f"not a directory: {feat}")
        if mat and not mat.is_dir():
            raise IngestError("E_INGEST_NOT_DIR", f"not a directory: {mat}")
        return feat, mat, "explicit"

    featured_names = _norm_names(
        getattr(cfg, "featured_dir_names", None) or DEFAULT_FEATURED_DIR_NAMES
    )
    material_names = _norm_names(
        getattr(cfg, "material_dir_names", None) or DEFAULT_MATERIAL_DIR_NAMES
    )
    feat = find_tier_subdir(root, featured_names)
    mat = find_tier_subdir(root, material_names)
    if feat or mat:
        return feat, mat, "auto"
    return None, None, "single"


def _scan_one_dir(
    directory: Path,
    *,
    tier: str,
    max_count: int,
    recursive: bool,
    min_edge_px: int,
    stats: dict,
) -> list[tuple[datetime, str, Path, str]]:
    if max_count <= 0:
        return []
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

    stats[f"scanned_{tier}"] = len(candidates)
    accepted: list[tuple[datetime, str, Path, str]] = []
    for path in candidates:
        if len(accepted) >= max_count:
            break
        try:
            meta = _peek_photo(path)
        except IngestError:
            stats["skipped_open"] = stats.get("skipped_open", 0) + 1
            continue
        if not min_edge_ok(meta.width, meta.height, min_edge_px):
            stats["skipped_small"] = stats.get("skipped_small", 0) + 1
            continue
        accepted.append((meta.taken_at, str(path).lower(), path, tier))

    accepted.sort(key=lambda x: (x[0], x[1]))
    stats[f"used_{tier}"] = len(accepted)
    return accepted


def scan_tiered_image_paths(
    *,
    featured_dir: Path | None,
    material_dir: Path | None,
    single_dir: Path | None,
    max_photos: int,
    recursive: bool = True,
    min_edge_px: int = 320,
) -> tuple[list[tuple[Path, str]], dict]:
    """Scan featured first, then material; single_dir → all material."""
    stats: dict = {"mode": "single"}
    merged: list[tuple[datetime, str, Path, str]] = []

    if featured_dir or material_dir:
        stats["mode"] = "dual"
        remaining = max_photos
        if featured_dir:
            chunk = _scan_one_dir(
                featured_dir,
                tier=TIER_FEATURED,
                max_count=remaining,
                recursive=recursive,
                min_edge_px=min_edge_px,
                stats=stats,
            )
            merged.extend(chunk)
            remaining = max(0, max_photos - len(merged))
        if material_dir:
            chunk = _scan_one_dir(
                material_dir,
                tier=TIER_MATERIAL,
                max_count=remaining,
                recursive=recursive,
                min_edge_px=min_edge_px,
                stats=stats,
            )
            merged.extend(chunk)
    elif single_dir:
        chunk = _scan_one_dir(
            single_dir,
            tier=TIER_MATERIAL,
            max_count=max_photos,
            recursive=recursive,
            min_edge_px=min_edge_px,
            stats=stats,
        )
        merged.extend(chunk)
    else:
        raise IngestError("E_INGEST_EMPTY", "no ingest directory")

    if not merged:
        raise IngestError("E_INGEST_EMPTY", "no images after tier scan")

    merged.sort(key=lambda x: (x[0], x[1]))
    if len(merged) > max_photos:
        merged = merged[:max_photos]

    stats["scanned"] = stats.get("scanned_featured", 0) + stats.get("scanned_material", 0)
    stats["used"] = len(merged)
    stats["featured_count"] = sum(1 for *_, tier in merged if tier == TIER_FEATURED)
    stats["material_count"] = sum(1 for *_, tier in merged if tier == TIER_MATERIAL)
    files = [(path, tier) for _, _, path, tier in merged]
    return files, stats


def resolve_import_source(*, tier: str, dual_ingest: bool) -> str:
    """Map ingest folder tier to appendix A importSource."""
    if not dual_ingest:
        return IMPORT_SOURCE_LEGACY
    return IMPORT_SOURCE_FEATURED if tier == TIER_FEATURED else IMPORT_SOURCE_MATERIAL


def apply_user_tier_fields(
    entry: dict,
    *,
    tier: str,
    dual_ingest: bool = False,
    import_source: str | None = None,
) -> None:
    entry["userTier"] = TIER_FEATURED if tier == TIER_FEATURED else TIER_MATERIAL
    entry["userTierSource"] = TIER_SOURCE_INGEST
    entry["importSource"] = import_source or resolve_import_source(
        tier=tier, dual_ingest=dual_ingest
    )


def build_content_sig_index(assets: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for idx, asset in enumerate(assets):
        sig = asset.get("contentSig")
        if isinstance(sig, str) and sig:
            out[sig] = idx
    return out


def preserve_user_tier_on_replace(old_asset: dict, incoming_tier: str) -> str:
    """Burst/phash replace: featured on replaced asset is never downgraded."""
    if old_asset.get("userTier") == TIER_FEATURED:
        return TIER_FEATURED
    if incoming_tier == TIER_FEATURED:
        return TIER_FEATURED
    return TIER_MATERIAL


def preserve_user_tier_source_on_replace(old_asset: dict, resolved_tier: str) -> str | None:
    """Keep userTierSource when featured tier survives a replace."""
    if resolved_tier != TIER_FEATURED:
        return None
    if old_asset.get("userTier") == TIER_FEATURED:
        source = old_asset.get("userTierSource")
        if source in (TIER_SOURCE_INGEST, TIER_SOURCE_USER):
            return str(source)
    return None


def upgrade_asset_tier(assets: list[dict], content_sig: str, *, tier: str) -> bool:
    """Cross-folder dedupe: same contentSig → keep featured tier."""
    if tier != TIER_FEATURED:
        return False
    idx_map = build_content_sig_index(assets)
    idx = idx_map.get(content_sig)
    if idx is None:
        return False
    asset = assets[idx]
    if asset.get("userTier") == TIER_FEATURED:
        return False
    asset["userTier"] = TIER_FEATURED
    asset["userTierSource"] = TIER_SOURCE_INGEST
    return True


def preserve_material_import_source_on_dedupe(
    assets: list[dict], content_sig: str, *, tier: str
) -> bool:
    """Cross-folder dedupe: 素材 duplicate after 精选 keeps importSource=material (AC-DF)."""
    if tier != TIER_MATERIAL:
        return False
    idx = build_content_sig_index(assets).get(content_sig)
    if idx is None:
        return False
    asset = assets[idx]
    if asset.get("importSource") == IMPORT_SOURCE_MATERIAL:
        return False
    asset["importSource"] = IMPORT_SOURCE_MATERIAL
    return True


def count_user_tiers(assets: list[dict]) -> dict[str, int]:
    featured = material = 0
    for asset in assets:
        tier = asset.get("userTier")
        if tier == TIER_FEATURED:
            featured += 1
        else:
            material += 1
    return {"featured": featured, "material": material, "total": featured + material}


def sync_user_tier_summary(trip: dict) -> None:
    """Refresh curation.userTierSummary counts after tier edits (G2 serve)."""
    counts = count_user_tiers(trip.get("assets") or [])
    curation = trip.setdefault("curation", {})
    if counts["featured"] == 0:
        curation.pop("userTierSummary", None)
        return
    prev = curation.get("userTierSummary") or {}
    curation["userTierSummary"] = {
        "featured": counts["featured"],
        "material": counts["material"],
        "featuredInLayout": prev.get("featuredInLayout", counts["featured"]),
    }


def promote_asset_to_featured(trip: dict, asset_id: str) -> bool:
    """G2 serve: user elevates material → featured (appendix A · P5)."""
    asset_id = str(asset_id or "").strip()
    if not asset_id:
        return False
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict) or asset.get("id") != asset_id:
            continue
        if asset.get("userTier") == TIER_FEATURED and asset.get("userTierSource") == TIER_SOURCE_USER:
            return False
        asset["userTier"] = TIER_FEATURED
        asset["userTierSource"] = TIER_SOURCE_USER
        sync_user_tier_summary(trip)
        return True
    return False


def promote_assets_to_featured(trip: dict, asset_ids: list[str]) -> list[str]:
    promoted: list[str] = []
    for asset_id in asset_ids:
        if promote_asset_to_featured(trip, asset_id):
            promoted.append(asset_id)
    return promoted


def demote_asset_from_featured(trip: dict, asset_id: str) -> bool:
    """Studio · cancel featured → material (PRD-REFINE-FEEDBACK-LOOP D-FEED-05 / OQ-FEED-02)."""
    asset_id = str(asset_id or "").strip()
    if not asset_id:
        return False
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict) or asset.get("id") != asset_id:
            continue
        if asset.get("userTier") != TIER_FEATURED:
            return False
        asset["userTier"] = TIER_MATERIAL
        asset["userTierSource"] = TIER_SOURCE_USER
        sync_user_tier_summary(trip)
        return True
    return False


def demote_assets_from_featured(trip: dict, asset_ids: list[str]) -> list[str]:
    demoted: list[str] = []
    for asset_id in asset_ids:
        if demote_asset_from_featured(trip, asset_id):
            demoted.append(asset_id)
    return demoted
