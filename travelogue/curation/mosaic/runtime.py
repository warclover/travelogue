"""Mosaic runtime helpers (window sizes, router version)."""

from __future__ import annotations

from travelogue.config import MosaicConfig

MOSAIC_ROUTER_VERSION = "p15-mcs-1"

_mosaic_cfg_override: MosaicConfig | None = None
_disabled_pattern_ids: tuple[str, ...] = ()

_ALLOWED_SIZES = frozenset({3, 4, 5, 6, 8, 9})


def set_mosaic_config_override(cfg: MosaicConfig | None) -> None:
    """Thread-local style override for curate chapter planning (cohort weights)."""
    global _mosaic_cfg_override
    _mosaic_cfg_override = cfg


def reset_mosaic_config_override() -> None:
    set_mosaic_config_override(None)


def set_mosaic_disabled_patterns(pattern_ids: tuple[str, ...] | list[str]) -> None:
    global _disabled_pattern_ids
    _disabled_pattern_ids = tuple(str(x) for x in pattern_ids if x)


def reset_mosaic_disabled_patterns() -> None:
    set_mosaic_disabled_patterns(())


def get_mosaic_disabled_patterns() -> tuple[str, ...]:
    return _disabled_pattern_ids


def get_effective_mosaic_config() -> MosaicConfig:
    if _mosaic_cfg_override is not None:
        return _mosaic_cfg_override
    from travelogue.config import get_config

    return get_config().mosaic


def cohort_mosaic_override(app_cfg) -> MosaicConfig | None:
    """Build mosaic config with cohort_coherence weight when cohort tagging is active."""
    cohort = app_cfg.cohort
    if not cohort.enabled or cohort.mosaic_weight <= 1e-9:
        return None
    from dataclasses import replace

    mw = dict(app_cfg.mosaic.weights)
    if float(mw.get("cohort_coherence") or 0.0) <= 1e-9:
        mw["cohort_coherence"] = cohort.mosaic_weight
    return replace(app_cfg.mosaic, weights=mw)


def mosaic_window_size_enabled(size: int, cfg: MosaicConfig | None = None) -> bool:
    """True when MCS or legacy may emit mosaic screens for this window size."""
    cfg = cfg or get_effective_mosaic_config()
    return size in cfg.enabled_window_sizes


def five_slot_mosaic_enabled(cfg: MosaicConfig | None = None) -> bool:
    """True when MCS or legacy may emit 5-photo mosaic screens."""
    return mosaic_window_size_enabled(5, cfg)


def six_slot_layout_enabled(cfg: MosaicConfig | None = None) -> bool:
    """True when MCS or legacy homogeneous / hero grids may use six slots."""
    return mosaic_window_size_enabled(6, cfg)


def _max_mosaic_slots() -> int:
    from travelogue.config import get_config

    te = getattr(get_config().layout, "template_engine", None)
    if te is None:
        return 9
    return int(getattr(te, "max_mosaic_slots", 9) or 9)


def mosaic_window_size_order(cfg: MosaicConfig | None = None) -> tuple[int, ...]:
    """P21 · balanced MCS window attempt order (PRD §5.3)."""
    cfg = cfg or get_effective_mosaic_config()
    return cfg.density_budget.window_order


def ordered_mosaic_window_sizes(
    cfg: MosaicConfig,
    *,
    density: str = "balanced",
) -> tuple[int, ...]:
    """Return enabled window sizes in balanced P21 attempt order."""
    sizes = effective_mosaic_window_sizes(cfg)
    if not sizes:
        return ()
    if not cfg.density_budget.enabled or density != "balanced":
        return tuple(sorted(sizes, reverse=True))
    order = cfg.density_budget.window_order
    head = [s for s in order if s in sizes]
    tail = [s for s in sorted(sizes) if s not in head]
    return tuple(head + tail)


# Slot-3 legacy grids pack without consuming P21 dense collage budget (min_slots=4).
_DENSITY_AUX_PACK_SIZE = 3


def planner_mosaic_window_sizes(
    cfg: MosaicConfig,
    *,
    density: str = "balanced",
) -> tuple[int, ...]:
    """Layout-density-aware MCS sizes (balanced/collage may append aux slot-3)."""
    sizes = effective_mosaic_window_sizes(cfg)
    if not sizes:
        return ()
    pack_aux = (
        cfg.density_budget.enabled
        and density in ("balanced", "collage_first")
        and _DENSITY_AUX_PACK_SIZE in _ALLOWED_SIZES
        and _DENSITY_AUX_PACK_SIZE not in sizes
    )
    if density == "collage_first":
        head = tuple(sorted(sizes, reverse=True))
        return head + (_DENSITY_AUX_PACK_SIZE,) if pack_aux else head
    if density == "balanced" and cfg.density_budget.enabled:
        ordered = ordered_mosaic_window_sizes(cfg, density="balanced")
        return ordered + (_DENSITY_AUX_PACK_SIZE,) if pack_aux else ordered
    if density == "balanced":
        return ordered_mosaic_window_sizes(cfg, density="balanced")
    return tuple(sorted(sizes, reverse=True))


def effective_mosaic_window_sizes(cfg: MosaicConfig) -> tuple[int, ...]:
    """DESIGN §12.1 · unified_mode=false limits MCS to 5-slot windows only."""
    if not cfg.enabled:
        return ()
    max_slots = _max_mosaic_slots()
    sizes = tuple(
        s for s in cfg.enabled_window_sizes if s in _ALLOWED_SIZES and s <= max_slots
    )
    if cfg.unified_mode:
        return sizes
    return tuple(s for s in sizes if s == 5)
