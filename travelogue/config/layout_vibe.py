"""LVP · Layout Vibe Picker — vibe → mosaic profile (M1).

Maps user-facing vibe ids to the three mosaic parent switches (MTSO / MEGC / MSA).
Does not touch SSG look or LSE capability flags.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from travelogue.config.app import AppConfig
from travelogue.config.mosaic import (
    EqualGridContractConfig,
    MosaicConfig,
    SelectionOptimizationConfig,
    SlotAdaptationConfig,
)

# vibe ids (D-LVP-01)
VIBE_MAGAZINE_DEFAULT = "magazine_default"
VIBE_FIT_PHOTO_EXPERIMENTAL = "fit_photo_experimental"

KNOWN_VIBES: frozenset[str] = frozenset(
    {VIBE_MAGAZINE_DEFAULT, VIBE_FIT_PHOTO_EXPERIMENTAL}
)

# GA stack (D-LVP-02 / F-01～03): MTSO on · MEGC on · MSA off
GA_SELECTION_OPTIMIZATION = True
GA_EQUAL_GRID_CONTRACT = True
GA_SLOT_ADAPTATION = False


@dataclass(frozen=True)
class MosaicVibeProfile:
    """Three mosaic parent switches driven by a vibe."""

    selection_optimization: bool
    equal_grid_contract: bool
    slot_adaptation: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "selection_optimization": self.selection_optimization,
            "equal_grid_contract": self.equal_grid_contract,
            "slot_adaptation": self.slot_adaptation,
        }


PROFILE_MAGAZINE_DEFAULT = MosaicVibeProfile(
    selection_optimization=GA_SELECTION_OPTIMIZATION,
    equal_grid_contract=GA_EQUAL_GRID_CONTRACT,
    slot_adaptation=GA_SLOT_ADAPTATION,
)

PROFILE_FIT_PHOTO_EXPERIMENTAL = MosaicVibeProfile(
    selection_optimization=GA_SELECTION_OPTIMIZATION,
    equal_grid_contract=GA_EQUAL_GRID_CONTRACT,
    slot_adaptation=True,
)

_PROFILES: dict[str, MosaicVibeProfile] = {
    VIBE_MAGAZINE_DEFAULT: PROFILE_MAGAZINE_DEFAULT,
    VIBE_FIT_PHOTO_EXPERIMENTAL: PROFILE_FIT_PHOTO_EXPERIMENTAL,
}


def mosaic_profile_for_vibe(vibe_id: str | None) -> MosaicVibeProfile:
    """Return mosaic profile for *vibe_id*; unknown/empty → magazine_default (fail-open)."""
    key = str(vibe_id or "").strip()
    if key in _PROFILES:
        return _PROFILES[key]
    return PROFILE_MAGAZINE_DEFAULT


def read_trip_layout_vibe(trip: Mapping[str, Any] | None) -> str | None:
    """Read raw ``trip.studio.layoutVibe`` (None when missing/blank)."""
    if not isinstance(trip, Mapping):
        return None
    studio = trip.get("studio")
    if not isinstance(studio, Mapping):
        return None
    raw = studio.get("layoutVibe", studio.get("layout_vibe"))
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def set_trip_layout_vibe(trip: dict[str, Any], vibe_id: str | None) -> dict[str, Any]:
    """Persist or clear ``trip.studio.layoutVibe``.

    Passing ``None`` / empty clears the field (AC-LVP-08 rollback).
    """
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        studio = {}
        trip["studio"] = studio
    else:
        studio = dict(studio)
        trip["studio"] = studio
    text = str(vibe_id).strip() if vibe_id is not None else ""
    if not text:
        studio.pop("layoutVibe", None)
        studio.pop("layout_vibe", None)
        if not studio:
            trip.pop("studio", None)
        return trip
    studio["layoutVibe"] = text
    studio.pop("layout_vibe", None)
    return trip


def resolve_layout_vibe(
    trip: Mapping[str, Any] | None,
    cfg: AppConfig | None = None,
) -> str:
    """Priority: ``trip.studio.layoutVibe`` > fail-open ``magazine_default`` (D-LVP-07/09).

    Process mosaic overlay is applied *after* resolve via :func:`apply_layout_vibe_to_config`;
    when trip vibe is absent/invalid, resolved id is ``magazine_default`` so effective
    switches ≡ GA (AC-LVP-08), not a hostile local YAML MSA-on overlay.
    """
    _ = cfg  # process-level vibe key not shipped in V1
    raw = read_trip_layout_vibe(trip)
    if raw and raw in KNOWN_VIBES:
        return raw
    return VIBE_MAGAZINE_DEFAULT


def apply_mosaic_vibe_profile(
    mosaic: MosaicConfig,
    profile: MosaicVibeProfile,
) -> MosaicConfig:
    """Overlay the three parent switches; preserve nested knobs."""
    so = mosaic.selection_optimization or SelectionOptimizationConfig()
    egc = mosaic.equal_grid_contract or EqualGridContractConfig()
    sa = mosaic.slot_adaptation or SlotAdaptationConfig()
    return replace(
        mosaic,
        selection_optimization=replace(so, enabled=bool(profile.selection_optimization)),
        equal_grid_contract=replace(egc, enabled=bool(profile.equal_grid_contract)),
        slot_adaptation=replace(sa, enabled=bool(profile.slot_adaptation)),
    )


def apply_layout_vibe_to_config(
    trip: Mapping[str, Any] | None,
    cfg: AppConfig,
    *,
    vibe_id: str | None = None,
) -> AppConfig:
    """Return *cfg* with mosaic three switches set from resolved vibe.

    Does not mutate SSG look / LSE capability fields (AC-LVP-07).
    """
    resolved = vibe_id if vibe_id in KNOWN_VIBES else resolve_layout_vibe(trip, cfg)
    profile = mosaic_profile_for_vibe(resolved)
    return replace(cfg, mosaic=apply_mosaic_vibe_profile(cfg.mosaic, profile))


def mosaic_switches(cfg: AppConfig | MosaicConfig) -> dict[str, bool]:
    """Snapshot the three LVP-mapped switches (for tests / observability)."""
    mosaic = cfg if isinstance(cfg, MosaicConfig) else cfg.mosaic
    so = mosaic.selection_optimization
    egc = mosaic.equal_grid_contract
    sa = mosaic.slot_adaptation
    return {
        "selection_optimization": bool(so is not None and so.enabled),
        "equal_grid_contract": bool(egc is not None and egc.enabled),
        "slot_adaptation": bool(sa is not None and sa.enabled),
    }
