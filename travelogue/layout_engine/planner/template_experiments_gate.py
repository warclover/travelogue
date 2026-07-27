"""Shared template_experiments visibility gate for soft-rotation pickers."""

from __future__ import annotations

from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig


def experimental_members_visible(
    *,
    mosaic_cfg: MosaicConfig | None,
    trip_id: str | None,
    allowlist_intersect: frozenset[str],
    stable_order: dict[str, int] | None = None,
    parked: frozenset[str] | None = None,
) -> list[str]:
    """Picker-side experiments gate. Empty cohort ⇒ nobody; ``*`` ⇒ all trips."""
    if mosaic_cfg is None:
        return []
    te: TemplateExperimentsConfig | None = getattr(
        mosaic_cfg, "template_experiments", None
    )
    if te is None or not getattr(te, "enabled", False):
        return []
    allow = tuple(getattr(te, "allowlist", ()) or ())
    cohort = tuple(getattr(te, "cohort_trip_ids", ()) or ())
    if not cohort:
        return []
    tid = str(trip_id or "").strip()
    if "*" not in cohort and (not tid or tid not in cohort):
        return []
    parked_ids = parked or frozenset()
    out = [
        pid
        for pid in allow
        if pid in allowlist_intersect and pid not in parked_ids
    ]
    order = stable_order or {}
    return sorted(out, key=lambda p: order.get(p, 99))


def disabled_template_ids(cfg) -> set[str]:
    te = getattr(getattr(cfg, "layout", None), "template_engine", None) if cfg else None
    raw = getattr(te, "overrides_disable", ()) if te is not None else ()
    return {str(x) for x in (raw or ()) if x}


__all__ = [
    "disabled_template_ids",
    "experimental_members_visible",
]
