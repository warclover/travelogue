"""Mosaic runtime helpers (window sizes, router version)."""

from __future__ import annotations

from contextvars import ContextVar

from travelogue.config import MosaicConfig

MOSAIC_ROUTER_VERSION = "p15-mcs-1"

_mosaic_cfg_override_var: ContextVar[MosaicConfig | None] = ContextVar(
    "mosaic_cfg_override", default=None
)
_disabled_pattern_ids_var: ContextVar[tuple[str, ...]] = ContextVar(
    "mosaic_disabled_patterns", default=()
)

_ALLOWED_SIZES = frozenset({3, 4, 5, 6, 8, 9})


def set_mosaic_config_override(cfg: MosaicConfig | None) -> None:
    """Context-local override for curate chapter planning (cohort weights)."""
    _mosaic_cfg_override_var.set(cfg)


def reset_mosaic_config_override() -> None:
    _mosaic_cfg_override_var.set(None)


def set_mosaic_disabled_patterns(pattern_ids: tuple[str, ...] | list[str]) -> None:
    _disabled_pattern_ids_var.set(tuple(str(x) for x in pattern_ids if x))


def reset_mosaic_disabled_patterns() -> None:
    _disabled_pattern_ids_var.set(())


def get_mosaic_disabled_patterns() -> tuple[str, ...]:
    return _disabled_pattern_ids_var.get()


def get_effective_mosaic_config() -> MosaicConfig:
    override = _mosaic_cfg_override_var.get()
    if override is not None:
        return override
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


# LTN C1 · size=3 aux pack removed from MCS window order (parity/tiler keep explicit 3).
_DENSITY_AUX_PACK_SIZE = 3


def planner_mosaic_window_sizes(
    cfg: MosaicConfig,
    *,
    density: str = "balanced",
) -> tuple[int, ...]:
    """Layout-density-aware MCS sizes (no silent size=3 aux · LTN C1)."""
    sizes = effective_mosaic_window_sizes(cfg)
    if not sizes:
        return ()
    if density == "collage_first":
        return tuple(sorted(sizes, reverse=True))
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
