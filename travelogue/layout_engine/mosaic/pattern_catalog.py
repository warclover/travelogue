"""Mosaic pattern catalog (M3) — LTE-generated re-export (Phase 16)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    PATTERN_LANDSCAPE_3,
    PATTERN_LANDSCAPE_4,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_4,
)

# Stable id set for parity export (R-P16-02); YAML is authority for field values.
# LTN C3 · active MCS set (deprecated 6/8/9 flats omitted; kept in YAML for old trips).
LEGACY_MOSAIC_REGISTRY_IDS: frozenset[str] = frozenset(
    {
        PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
        PATTERN_MOSAIC_5_3P_2L_BALANCED,
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        "screen-mosaic-4-hero-70-sidebar",
        PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
        PATTERN_PORTRAIT_3,
        PATTERN_LANDSCAPE_3,
        PATTERN_PORTRAIT_1_LANDSCAPE_2,
        PATTERN_PORTRAIT_2_LANDSCAPE_2,
        PATTERN_PORTRAIT_4,
        PATTERN_LANDSCAPE_4,
    }
)


@dataclass(frozen=True)
class AspectProfile:
    min_portrait: int = 0
    min_landscape: int = 0
    max_portrait: int = 9
    max_landscape: int = 9


@dataclass(frozen=True)
class MosaicPattern:
    pattern_id: str
    slot_count: int
    grid_class: str
    roles: tuple[str, ...]
    accepts: AspectProfile
    css_verified: bool = True


def default_registry() -> dict[str, MosaicPattern]:
    """Build MosaicPattern map from LTE YAML (replaces handwritten registry)."""
    from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    out: dict[str, MosaicPattern] = {}
    for tid in sorted(LEGACY_MOSAIC_REGISTRY_IDS):
        try:
            out[tid] = export_mosaic_pattern(engine.get(tid))
        except KeyError:
            continue
    return out


_BY_SIZE: dict[int, tuple[str, ...]] = {
    3: MOSAIC_3_PATTERN_IDS,
    4: MOSAIC_4_PATTERN_IDS,
    5: MOSAIC_5_PATTERN_IDS,
    6: MOSAIC_6_PATTERN_IDS,
    8: MOSAIC_8_PATTERN_IDS,
    9: MOSAIC_9_PATTERN_IDS,
}


def patterns_for_window_size(size: int, registry: dict[str, MosaicPattern] | None = None) -> list[MosaicPattern]:
    from travelogue.layout_engine.mosaic.lte_adapter import lte_rollout_eligible

    reg = registry or default_registry()
    ids = _BY_SIZE.get(size)
    if ids:
        ordered = [reg[pid] for pid in ids if pid in reg]
        seen = {p.pattern_id for p in ordered}
        extras = sorted(
            (
                p
                for p in reg.values()
                if p.slot_count == size
                and p.pattern_id not in seen
                and lte_rollout_eligible(p.pattern_id)
            ),
            key=lambda p: p.pattern_id,
        )
        return ordered + extras
    return sorted(
        (
            p
            for p in reg.values()
            if p.slot_count == size and lte_rollout_eligible(p.pattern_id)
        ),
        key=lambda p: p.pattern_id,
    )
