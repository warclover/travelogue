"""Runtime legacy grid spec resolution — LTE export when enabled (PRD R-P16-02).

``_legacy_generated.py`` is a CI/codegen snapshot only (R-P19-101); runtime reads
``get_engine().export_legacy_registry()`` when the template engine is on.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _lte_legacy_export() -> dict[str, Any] | None:
    try:
        from travelogue.curation.mosaic.lte_adapter import read_templates_from_lte

        if not read_templates_from_lte():
            return None
        from travelogue.layout_templates.registry import get_engine

        return get_engine().export_legacy_registry()
    except Exception:
        return None


def reset_legacy_specs_cache_for_tests() -> None:
    _lte_legacy_export.cache_clear()


def explicit_grid_specs() -> dict[str, list[tuple[int, int, int, int]]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["explicit_grid_specs"]
    from travelogue.curation.mosaic._legacy_generated import EXPLICIT_GRID_SPECS

    return EXPLICIT_GRID_SPECS


def explicit_grid_bounds() -> dict[str, tuple[int, int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        specs = exported["explicit_grid_specs"]
        return {
            pid: (max(spec[1] for spec in sl), max(spec[3] for spec in sl))
            for pid, sl in specs.items()
        }
    from travelogue.curation.mosaic._legacy_generated import EXPLICIT_GRID_BOUNDS

    return EXPLICIT_GRID_BOUNDS


def auto_flow_grids() -> dict[str, tuple[int, int, int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["auto_flow_grids"]
    from travelogue.curation.mosaic._legacy_generated import AUTO_FLOW_GRIDS

    return AUTO_FLOW_GRIDS


def stack_patterns() -> frozenset[str]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["stack_patterns"]
    from travelogue.curation.mosaic._legacy_generated import STACK_PATTERNS

    return STACK_PATTERNS


def pattern_grid_class() -> dict[str, str]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["pattern_grid_class"]
    from travelogue.curation.mosaic._legacy_generated import PATTERN_GRID_CLASS

    return PATTERN_GRID_CLASS


def portrait_forbidden_wide() -> dict[str, frozenset[int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["portrait_forbidden_wide"]
    from travelogue.curation.mosaic._legacy_generated import _PORTRAIT_FORBIDDEN_WIDE

    return _PORTRAIT_FORBIDDEN_WIDE


def landscape_forbidden_tall() -> dict[str, frozenset[int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["landscape_forbidden_tall"]
    from travelogue.curation.mosaic._legacy_generated import _LANDSCAPE_FORBIDDEN_TALL

    return _LANDSCAPE_FORBIDDEN_TALL


def portrait_dominant_auto_flow() -> frozenset[str]:
    exported = _lte_legacy_export()
    if exported is not None:
        try:
            from travelogue.layout_templates.registry import get_engine

            ids = [
                tid
                for tid, tpl in get_engine()._templates.items()
                if tpl.kind == "primitive" and str(tpl.stage.aspect) == "9:16"
            ]
            return frozenset(ids)
        except Exception:
            pass
    from travelogue.curation.mosaic._legacy_generated import PORTRAIT_DOMINANT_AUTO_FLOW

    return PORTRAIT_DOMINANT_AUTO_FLOW


def mosaic_pattern_id_groups() -> dict[str, tuple[str, ...]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["mosaic_pattern_id_groups"]
    from travelogue.curation.mosaic._legacy_generated import (
        MOSAIC_3_PATTERN_IDS,
        MOSAIC_4_PATTERN_IDS,
        MOSAIC_5_PATTERN_IDS,
        MOSAIC_6_PATTERN_IDS,
        MOSAIC_8_PATTERN_IDS,
        MOSAIC_9_PATTERN_IDS,
    )

    return {
        "MOSAIC_3_PATTERN_IDS": MOSAIC_3_PATTERN_IDS,
        "MOSAIC_4_PATTERN_IDS": MOSAIC_4_PATTERN_IDS,
        "MOSAIC_5_PATTERN_IDS": MOSAIC_5_PATTERN_IDS,
        "MOSAIC_6_PATTERN_IDS": MOSAIC_6_PATTERN_IDS,
        "MOSAIC_8_PATTERN_IDS": MOSAIC_8_PATTERN_IDS,
        "MOSAIC_9_PATTERN_IDS": MOSAIC_9_PATTERN_IDS,
    }


def mosaic_unified_pattern_ids() -> tuple[str, ...]:
    groups = mosaic_pattern_id_groups()
    return (
        *groups["MOSAIC_3_PATTERN_IDS"],
        *groups["MOSAIC_4_PATTERN_IDS"],
        *groups["MOSAIC_5_PATTERN_IDS"],
        *groups["MOSAIC_6_PATTERN_IDS"],
        *groups["MOSAIC_8_PATTERN_IDS"],
        *groups["MOSAIC_9_PATTERN_IDS"],
    )
