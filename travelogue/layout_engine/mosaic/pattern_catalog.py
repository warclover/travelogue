"""Mosaic pattern catalog (M3) — LTE-generated re-export (Phase 16)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    MOSAIC_UNIFIED_PATTERN_IDS,
)

if TYPE_CHECKING:
    from travelogue.config.mosaic import MosaicConfig

# LTN E1 · no hand list — LEGACY follows policy→codegen unified groups (R-P16-02).
LEGACY_MOSAIC_REGISTRY_IDS: frozenset[str] = frozenset(MOSAIC_UNIFIED_PATTERN_IDS)


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


def patterns_for_window_size(
    size: int,
    registry: dict[str, MosaicPattern] | None = None,
    *,
    cfg: MosaicConfig | None = None,
) -> list[MosaicPattern]:
    from travelogue.config.mosaic import effective_ega_keep_equal_six
    from travelogue.layout_engine.mosaic.constants import PATTERN_LANDSCAPE_6
    from travelogue.layout_engine.mosaic.lte_adapter import lte_rollout_eligible

    reg = dict(registry or default_registry())
    # EGA PR-B · ensure landscape-6 is loadable even when pruned from MOSAIC_6 IDs.
    if size == 6 and effective_ega_keep_equal_six(cfg) and PATTERN_LANDSCAPE_6 not in reg:
        try:
            from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
            from travelogue.layout_templates.registry import get_engine

            reg[PATTERN_LANDSCAPE_6] = export_mosaic_pattern(
                get_engine().get(PATTERN_LANDSCAPE_6)
            )
        except KeyError:
            pass
    ids = _BY_SIZE.get(size)
    if ids:
        ordered_ids = list(ids)
        if (
            size == 6
            and effective_ega_keep_equal_six(cfg)
            and PATTERN_LANDSCAPE_6 not in ordered_ids
            and PATTERN_LANDSCAPE_6 in reg
        ):
            ordered_ids = [PATTERN_LANDSCAPE_6, *ordered_ids]
        ordered = [reg[pid] for pid in ordered_ids if pid in reg]
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
