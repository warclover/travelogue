"""Unified original-pixel path resolution (PRD-MEDIA-REFERENCE-STORAGE-V1 · D-MRS-09)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


class MediaSourceMissingError(Exception):
    """Original pixels cannot be resolved."""

    code = "E_MEDIA_SOURCE_MISSING"

    def __init__(self, message: str = "original source missing") -> None:
        super().__init__(message)
        self.message = message


def file_content_sig(path: Path) -> str:
    """size:md5 signature used for remount matching (same format as ingest)."""
    st = path.stat()
    digest = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return f"{st.st_size}:{digest.hexdigest()}"


@dataclass
class RemountResult:
    matched: int = 0
    missing: int = 0
    content_changed: int = 0

    @property
    def ok(self) -> bool:
        return self.matched > 0 and self.content_changed == 0

    @property
    def error_code(self) -> str | None:
        # Prefer content_changed so UI can show AC-MRS-13 copy (not generic mismatch).
        if self.content_changed:
            return "E_MEDIA_CONTENT_CHANGED"
        if self.matched == 0:
            return "E_MEDIA_REMOUNT_MISMATCH"
        return None


def build_source_ref(
    *,
    album_root: Path | None,
    source_path: Path,
) -> dict[str, str]:
    """Build a filesystem sourceRef for trip.json Document storage."""
    resolved = source_path.resolve()
    ref: dict[str, str] = {
        "kind": "filesystem",
        "path": str(resolved),
    }
    if album_root is not None:
        root = album_root.resolve()
        ref["albumRoot"] = str(root)
        try:
            ref["relativePath"] = str(resolved.relative_to(root)).replace("\\", "/")
        except ValueError:
            pass
    return ref


def source_ref_path(asset: dict[str, Any]) -> Path | None:
    ref = asset.get("sourceRef")
    if not isinstance(ref, dict):
        return None
    raw = ref.get("path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw)
    album = ref.get("albumRoot")
    rel = ref.get("relativePath")
    if isinstance(album, str) and isinstance(rel, str) and album.strip() and rel.strip():
        return Path(album) / rel
    return None


def resolve_source_path(
    asset: dict[str, Any],
    trip_dir: Path,
    *,
    raise_on_missing: bool = False,
) -> Path | None:
    """Resolve original pixels: trip sourceFile → sourceRef → None/raise.

    Does not fall back to display WebP (those are for presentation, not reexport).
    """
    source_rel = asset.get("sourceFile")
    if isinstance(source_rel, str) and source_rel.strip():
        candidate = (trip_dir / source_rel.lstrip("/\\")).resolve()
        try:
            candidate.relative_to(trip_dir.resolve())
        except ValueError:
            pass
        else:
            if candidate.is_file():
                return candidate
        # Absolute sourceFile is uncommon but tolerate if present
        abs_candidate = Path(source_rel)
        if abs_candidate.is_file():
            return abs_candidate

    ref_path = source_ref_path(asset)
    if ref_path is not None and ref_path.is_file():
        return ref_path

    if raise_on_missing:
        aid = asset.get("id") or "?"
        raise MediaSourceMissingError(f"missing source for {aid}")
    return None


def compute_storage_mode(trip: dict[str, Any], trip_dir: Path) -> str:
    """Derive trip media.storageMode from on-disk source files vs sourceRef."""
    assets = trip.get("assets") or []
    if not assets:
        return "copied"
    has_copied = False
    has_referenced = False
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") not in (None, "image"):
            continue
        source_rel = asset.get("sourceFile")
        materialized = False
        if isinstance(source_rel, str) and source_rel.strip():
            if (trip_dir / source_rel.lstrip("/\\")).is_file():
                materialized = True
        if materialized:
            has_copied = True
        elif source_ref_path(asset) is not None or asset.get("sourceRef"):
            has_referenced = True
        else:
            # legacy image with neither — treat as copied expectation
            has_copied = True
    if has_copied and has_referenced:
        return "mixed"
    if has_referenced and not has_copied:
        return "referenced"
    return "copied"


def assess_source_availability(
    trip: dict[str, Any],
    trip_dir: Path,
) -> dict[str, Any]:
    """Summarize whether original pixels are reachable (PRD §7 / AC-MRS-06)."""
    assets = trip.get("assets") or []
    total = 0
    missing = 0
    with_ref = 0
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") not in (None, "image"):
            continue
        total += 1
        if isinstance(asset.get("sourceRef"), dict):
            with_ref += 1
        if resolve_source_path(asset, trip_dir) is None:
            missing += 1
    mode = compute_storage_mode(trip, trip_dir)
    # Block export when any original is unreachable for referenced/mixed trips,
    # or when every image is missing originals (deep-cleaned without remount).
    source_missing = False
    if total > 0:
        if mode in ("referenced", "mixed") and missing > 0:
            source_missing = True
        elif missing == total and with_ref > 0:
            source_missing = True
    return {
        "sourceMissing": source_missing,
        "missingCount": missing,
        "totalImages": total,
        "storageMode": mode,
        "withSourceRef": with_ref,
    }


def ensure_media_block(trip: dict[str, Any], trip_dir: Path, *, album_root: Path | None = None) -> dict:
    """Ensure trip['media'] exists and storageMode is up to date."""
    media = trip.get("media")
    if not isinstance(media, dict):
        media = {}
        trip["media"] = media
    media["storageMode"] = compute_storage_mode(trip, trip_dir)
    if album_root is not None:
        roots = media.get("albumRoots")
        if not isinstance(roots, list):
            roots = []
        root_s = str(album_root.resolve())
        if root_s not in roots:
            roots.append(root_s)
        media["albumRoots"] = roots
    return media


def remount_album(
    trip: dict[str, Any],
    album_root: Path,
    *,
    signature_fn: Callable[[Path], str] | None = None,
) -> RemountResult:
    """Match assets to files under album_root by contentSig (AC-MRS-13).

    Mutates ``trip['assets'][*].sourceRef`` and ``trip['media'].albumRoots`` on match.
    Same-name candidates with different sig count as ``content_changed`` (never force-link).
    """
    sig_fn = signature_fn or file_content_sig
    album = album_root.resolve()
    sig_index: dict[str, Path] = {}
    for path in album.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        try:
            sig = sig_fn(path)
        except OSError:
            continue
        sig_index.setdefault(sig, path)

    result = RemountResult()
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict) or asset.get("type") not in (None, "image"):
            continue
        sig = asset.get("contentSig")
        if not isinstance(sig, str) or not sig:
            result.missing += 1
            continue
        hit = sig_index.get(sig)
        if hit is None:
            ref = asset.get("sourceRef") if isinstance(asset.get("sourceRef"), dict) else {}
            rel = ref.get("relativePath") if isinstance(ref, dict) else None
            candidate = album / rel if isinstance(rel, str) and rel else None
            if candidate is not None and candidate.is_file():
                try:
                    new_sig = sig_fn(candidate)
                except OSError:
                    new_sig = ""
                if new_sig and new_sig != sig:
                    result.content_changed += 1
                    continue
            result.missing += 1
            continue
        asset["sourceRef"] = build_source_ref(album_root=album, source_path=hit)
        result.matched += 1

    media = trip.setdefault("media", {})
    if not isinstance(media, dict):
        media = {}
        trip["media"] = media
    roots = media.get("albumRoots")
    if not isinstance(roots, list):
        roots = []
    root_s = str(album)
    if root_s not in roots:
        roots.append(root_s)
    media["albumRoots"] = roots
    return result
