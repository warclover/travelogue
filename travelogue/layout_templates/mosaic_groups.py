"""Auto mosaic unified groups by photoCount (P19 R-P19-104)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from travelogue.layout_templates.registry import LayoutTemplateEngine

_UNIFIED_WINDOW_SIZES: tuple[int, ...] = (3, 4, 5, 6, 8, 9)


def build_mosaic_unified_groups(
    engine: LayoutTemplateEngine,
    *,
    window_sizes: tuple[int, ...] = _UNIFIED_WINDOW_SIZES,
) -> dict[str, tuple[str, ...]]:
    """Group active LTE templates into MOSAIC_N_PATTERN_IDS buckets."""
    from travelogue.curation.mosaic.pattern_catalog import LEGACY_MOSAIC_REGISTRY_IDS

    out: dict[str, tuple[str, ...]] = {}
    for n in window_sizes:
        ids = sorted(
            {
                t.id
                for t in engine.list_active(window_size=n, enforce_quotas=False)
                if t.id in LEGACY_MOSAIC_REGISTRY_IDS
            }
        )
        if ids:
            out[f"MOSAIC_{n}_PATTERN_IDS"] = tuple(ids)
    return out
