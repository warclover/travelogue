"""Runtime legacy grid spec resolution — LTE export when enabled (PRD R-P16-02)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _lte_legacy_export() -> dict[str, Any] | None:
    try:
        from travelogue.layout_engine.mosaic.lte_adapter import read_templates_from_lte

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
    from travelogue.layout_engine.mosaic._legacy_generated import EXPLICIT_GRID_SPECS

    return EXPLICIT_GRID_SPECS


def auto_flow_grids() -> dict[str, tuple[int, int, int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["auto_flow_grids"]
    from travelogue.layout_engine.mosaic._legacy_generated import AUTO_FLOW_GRIDS

    return AUTO_FLOW_GRIDS


def portrait_forbidden_wide() -> dict[str, frozenset[int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["portrait_forbidden_wide"]
    from travelogue.layout_engine.mosaic._legacy_generated import _PORTRAIT_FORBIDDEN_WIDE

    return _PORTRAIT_FORBIDDEN_WIDE


def landscape_forbidden_tall() -> dict[str, frozenset[int]]:
    exported = _lte_legacy_export()
    if exported is not None:
        return exported["landscape_forbidden_tall"]
    from travelogue.layout_engine.mosaic._legacy_generated import _LANDSCAPE_FORBIDDEN_TALL

    return _LANDSCAPE_FORBIDDEN_TALL
