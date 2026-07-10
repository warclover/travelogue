"""Strip EXIF/metadata from images for share export."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

STRIPPABLE_SUFFIXES = {".jpg", ".jpeg", ".webp", ".png", ".tif", ".tiff"}


def should_strip(path: Path, *, enabled: bool) -> bool:
    return enabled and path.suffix.lower() in STRIPPABLE_SUFFIXES


def strip_image_to_bytes(path: Path) -> bytes:
    """Re-encode image without EXIF / ICC metadata."""
    with Image.open(path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        suffix = path.suffix.lower()
        if suffix == ".webp":
            img.save(buf, format="WEBP", quality=82, method=6)
        elif suffix in (".png",):
            img.save(buf, format="PNG", optimize=True)
        else:
            img.save(buf, format="JPEG", quality=88, optimize=True)
        return buf.getvalue()


def write_asset_to_zip(
    zf,
    arcname: str,
    source: Path,
    *,
    strip_exif: bool,
) -> None:
    """Write file into ZipFile; strip metadata for raster images when requested."""
    import zipfile
    from zipfile import ZipInfo

    arc = arcname.replace("\\", "/")
    if ".." in Path(arc).parts or arc.startswith("/"):
        raise ValueError(f"unsafe zip arcname: {arcname!r}")
    if should_strip(source, enabled=strip_exif):
        data = strip_image_to_bytes(source)
        info = ZipInfo(arc)
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, data)
    else:
        zf.write(source, arc)
