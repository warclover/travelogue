"""MTSO · template lifecycle admission (PR-A).

TPC ``template_contract`` only evaluates mix/eligibility.
Experimental visibility requires ``mosaic.template_experiments`` triple:
enabled ∧ allowlist hit ∧ trip in cohort (empty cohort ⇒ nobody).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from travelogue.config import AppConfig, get_config
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)

if TYPE_CHECKING:
    from travelogue.config.mosaic import MosaicConfig

# LTE-off hard denylist (retired SKUs that must never emit).
_LTE_OFF_HARD_DENY = frozenset(
    {
        PATTERN_MOSAIC_5_2P3L_EQUAL,
        PATTERN_MOSAIC_5_2P_3L_BALANCED,
        PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
        "screen-mosaic-5-3portrait-2land-balanced",
        "screen-portrait-6",
        "screen-landscape-6",
        "screen-portrait-9",
        "screen-landscape-9",
        "screen-portrait-grid-8",
    }
)

_SIX_HERO_FAMILY = frozenset(
    {
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    }
)
SIX_HERO_FAMILY_CANONICAL = PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5


@dataclass(frozen=True)
class AdmitResult:
    ok: bool
    reason: str = ""

    @property
    def disabled(self) -> bool:
        return not self.ok


def six_hero_family_id(pattern_id: str) -> str | None:
    """Return canonical family id for twin six-hero mosaics; else None."""
    pid = str(pattern_id or "")
    if pid in _SIX_HERO_FAMILY:
        return SIX_HERO_FAMILY_CANONICAL
    return None


def _read_templates_from_lte(cfg_app: AppConfig) -> bool:
    """Inline LTE switch — avoid circular import with lte_adapter."""
    te = getattr(getattr(cfg_app, "layout", None), "template_engine", None)
    if te is None or not getattr(te, "enabled", True):
        return False
    return bool(getattr(te, "read_templates_from_lte", False))


def _experiments_admit(
    pattern_id: str,
    *,
    mosaic_cfg: MosaicConfig,
    trip_id: str | None,
) -> AdmitResult:
    te = getattr(mosaic_cfg, "template_experiments", None)
    if te is None or not getattr(te, "enabled", False):
        return AdmitResult(False, "lifecycle_experimental_gated")
    allow = tuple(getattr(te, "allowlist", ()) or ())
    if pattern_id not in allow:
        return AdmitResult(False, "lifecycle_allowlist_miss")
    cohort = tuple(getattr(te, "cohort_trip_ids", ()) or ())
    # SUP-08 · empty cohort ⇒ nobody
    if not cohort:
        return AdmitResult(False, "lifecycle_cohort_miss")
    tid = str(trip_id or "").strip()
    if not tid or tid not in cohort:
        return AdmitResult(False, "lifecycle_cohort_miss")
    return AdmitResult(True, "")


def _rollout_percent(template: object) -> int:
    rollout = getattr(template, "rollout", None) or {}
    if not isinstance(rollout, dict):
        return 100
    try:
        return int(rollout.get("percent", 100))
    except (TypeError, ValueError):
        return 100


def lifecycle_admit(
    pattern_id: str,
    *,
    app: AppConfig | None = None,
    mosaic_cfg: MosaicConfig | None = None,
    trip_id: str | None = None,
) -> AdmitResult:
    """Single admission gate for MCS registry / disabled / legacy emit paths."""
    from travelogue.layout_engine.mosaic.runtime import get_mosaic_disabled_patterns

    pid = str(pattern_id or "").strip()
    if not pid:
        return AdmitResult(False, "lifecycle_empty_id")

    cfg_app = app or get_config()
    mcfg = mosaic_cfg if mosaic_cfg is not None else getattr(cfg_app, "mosaic", None)

    te = getattr(getattr(cfg_app, "layout", None), "template_engine", None)
    if te is not None:
        disabled = getattr(te, "overrides_disable", ()) or ()
        if pid in disabled:
            return AdmitResult(False, "lifecycle_overrides_disable")

    if pid in get_mosaic_disabled_patterns():
        return AdmitResult(False, "lifecycle_runtime_disabled")

    if not _read_templates_from_lte(cfg_app):
        if pid in _LTE_OFF_HARD_DENY:
            return AdmitResult(False, "lifecycle_deprecated")
        return AdmitResult(True, "")

    try:
        from travelogue.layout_templates.registry import get_engine

        tpl = get_engine().get(pid)
    except KeyError:
        # Unknown to LTE: allow size/window gates elsewhere to decide.
        return AdmitResult(True, "")

    status = str(getattr(tpl, "status", "") or "")
    if status in ("deprecated", "disabled"):
        return AdmitResult(False, "lifecycle_deprecated")

    if status == "experimental":
        if mcfg is None:
            return AdmitResult(False, "lifecycle_experimental_gated")
        return _experiments_admit(pid, mosaic_cfg=mcfg, trip_id=trip_id)

    if _rollout_percent(tpl) <= 0:
        return AdmitResult(False, "lifecycle_rollout_zero")
    return AdmitResult(True, "")
