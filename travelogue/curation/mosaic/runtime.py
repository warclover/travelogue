"""Mosaic runtime helpers (window sizes, router version)."""

from __future__ import annotations

from travelogue.config import MosaicConfig

MOSAIC_ROUTER_VERSION = "p15-mcs-1"

_mosaic_cfg_override: MosaicConfig | None = None

_ALLOWED_SIZES = frozenset({3, 4, 5, 6, 8, 9})


def set_mosaic_config_override(cfg: MosaicConfig | None) -> None:
    """Thread-local style override for curate chapter planning (cohort weights)."""
    global _mosaic_cfg_override
    _mosaic_cfg_override = cfg


def reset_mosaic_config_override() -> None:
    set_mosaic_config_override(None)


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


def effective_mosaic_window_sizes(cfg: MosaicConfig) -> tuple[int, ...]:
    """DESIGN §12.1 · unified_mode=false limits MCS to 5-slot windows only."""
    if not cfg.enabled:
        return ()
    sizes = tuple(s for s in cfg.enabled_window_sizes if s in _ALLOWED_SIZES)
    if cfg.unified_mode:
        return sizes
    return tuple(s for s in sizes if s == 5)
