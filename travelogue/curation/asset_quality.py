"""Drop obvious low-resolution outliers from layout/cover selection (curation re-exports)."""

from __future__ import annotations

from travelogue.layout_contract.quality import normalized_sharpness
from travelogue.media.quality import (
    apply_layout_eligibility_marks,
    asset_long_edge,
    asset_megapixels,
    asset_sharpness,
    asset_short_edge,
    backfill_native_dimensions,
    partition_low_resolution_assets,
)

__all__ = [
    "apply_layout_eligibility_marks",
    "asset_long_edge",
    "asset_megapixels",
    "asset_sharpness",
    "asset_short_edge",
    "backfill_native_dimensions",
    "normalized_sharpness",
    "partition_low_resolution_assets",
]
