"""Aspect classification and orientation summaries (layout kernel)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

AspectKind = Literal["portrait", "landscape", "square", "panorama", "tall"]
ExportLayout = Literal["auto", "mobile", "web"]

SQUARE_THRESHOLD = 1.08
PANORAMA_RATIO_MIN = 2.0
TALL_RATIO_MAX = 0.5


def classify_aspect(width: int, height: int) -> AspectKind:
    """Fine-grained aspect for layout + ingest crop (mirrors media.image_ops thresholds)."""
    if width <= 0 or height <= 0:
        return "square"
    ratio = width / height
    if ratio >= PANORAMA_RATIO_MIN:
        return "panorama"
    if ratio <= TALL_RATIO_MAX:
        return "tall"
    if ratio >= SQUARE_THRESHOLD:
        return "landscape"
    if ratio <= 1 / SQUARE_THRESHOLD:
        return "portrait"
    return "square"


@dataclass
class OrientationSummary:
    """Counts after ingest (display dimensions, post-crop)."""

    total: int
    landscape: int
    portrait: int
    square: int
    panorama: int
    tall: int
    export_layout: str

    @property
    def dominant(self) -> str:
        counts = {
            "landscape": self.landscape,
            "portrait": self.portrait,
            "square": self.square,
            "panorama": self.panorama,
            "tall": self.tall,
        }
        return max(counts, key=counts.get)  # type: ignore[arg-type]

    def to_dict(self) -> dict:
        return asdict(self)


def aspect_kind_for_asset(asset: dict) -> AspectKind:
    """Prefer native pixels so layout tier matches render-time aspect ratio."""
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return classify_aspect(w, h)
    stored = asset.get("aspectKind")
    if stored in ("portrait", "landscape", "square", "panorama", "tall"):
        return stored  # type: ignore[return-value]
    return "square"


def summarize_orientations(
    assets: list[dict],
    *,
    export_layout: ExportLayout = "auto",
) -> OrientationSummary:
    counts = {k: 0 for k in ("landscape", "portrait", "square", "panorama", "tall")}
    for a in assets:
        k = aspect_kind_for_asset(a)
        if k in counts:
            counts[k] += 1
    return OrientationSummary(
        total=len(assets),
        landscape=counts["landscape"],
        portrait=counts["portrait"],
        square=counts["square"],
        panorama=counts["panorama"],
        tall=counts["tall"],
        export_layout=export_layout,
    )
