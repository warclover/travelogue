"""Per-trip purpose pilot profiles (cover/hero weight + stratum scope)."""

from __future__ import annotations

import json
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any

from travelogue.config import AestheticConfig, get_config
from travelogue.config.aesthetic_stratified import (
    apply_stratum_preference_overlay,
    landscape_pilot_config,
)
from travelogue.curation.aesthetic_purpose_calibrate import weights_with_dim_emphasis

DEFAULT_PROFILES_PATH = Path("docs/acceptance-records/aesthetic-purpose-profiles.v4.json")


def _as_tuple(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


@lru_cache(maxsize=4)
def _load_profiles_json(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    if not path.is_file():
        return {"version": "1", "trips": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def load_purpose_profiles(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    resolved = path or (root / DEFAULT_PROFILES_PATH)
    if not resolved.is_absolute():
        resolved = root / resolved
    return _load_profiles_json(str(resolved.resolve()))


def purpose_profile_for_trip(
    trip: dict | None,
    *,
    profiles_doc: dict[str, Any] | None = None,
    trip_id: str | None = None,
) -> dict[str, Any] | None:
    if trip:
        stored = (trip.get("curation") or {}).get("purposePilotProfile")
        if isinstance(stored, dict) and stored:
            return dict(stored)
        trip_id = trip_id or str(trip.get("tripId") or "")
    if not trip_id:
        return None
    doc = profiles_doc if profiles_doc is not None else load_purpose_profiles()
    raw = (doc.get("trips") or {}).get(trip_id)
    return dict(raw) if isinstance(raw, dict) else None


def apply_purpose_pilot_overlay(cfg: AestheticConfig, profile: dict[str, Any]) -> AestheticConfig:
    """Merge pilot profile onto base aesthetic config (weights + stratum scope)."""
    pref = str(profile.get("stratumPreference") or "auto").strip().lower()
    from travelogue.config.aesthetic_stratified import STRATUM_PREFERENCE_PRESETS

    overlay = STRATUM_PREFERENCE_PRESETS.get(pref)
    if overlay:
        out = replace(cfg, **overlay)
    elif pref != "auto":
        out = apply_stratum_preference_overlay(cfg, pref)
    else:
        out = cfg

    blend_only = _as_tuple(profile.get("stratumBlendOnly"))
    if blend_only:
        out = replace(out, stratum_blend_only=blend_only)

    by_purpose = dict(out.stratum_blend_only_by_purpose or {})
    hero_strata = _as_tuple(profile.get("heroStrata"))
    cover_strata = _as_tuple(profile.get("coverStrata"))
    if hero_strata:
        by_purpose["hero"] = hero_strata
    if cover_strata:
        by_purpose["cover"] = cover_strata
    if by_purpose:
        out = replace(out, stratum_blend_only_by_purpose=by_purpose)

    cover_w = out.presets.cover
    if profile.get("coverSubjectClarity") is not None:
        cover_w = weights_with_dim_emphasis(
            cover_w,
            dim="subjectClarity",
            emphasis=float(profile["coverSubjectClarity"]),
        )
    elif profile.get("coverComposition") is not None:
        cover_w = weights_with_dim_emphasis(
            cover_w,
            dim="composition",
            emphasis=float(profile["coverComposition"]),
        )

    hero_w = out.presets.hero
    if profile.get("heroComposition") is not None:
        hero_w = weights_with_dim_emphasis(
            hero_w,
            dim="composition",
            emphasis=float(profile["heroComposition"]),
        )
    elif profile.get("heroSubjectClarity") is not None:
        hero_w = weights_with_dim_emphasis(
            hero_w,
            dim="subjectClarity",
            emphasis=float(profile["heroSubjectClarity"]),
        )
    elif profile.get("heroColor") is not None:
        hero_w = weights_with_dim_emphasis(
            hero_w,
            dim="color",
            emphasis=float(profile["heroColor"]),
        )

    presets = replace(out.presets, cover=cover_w, hero=hero_w)
    kwargs: dict[str, Any] = {"presets": presets}
    if profile.get("albumRelativePercentile") is not None:
        kwargs["album_relative_percentile"] = float(profile["albumRelativePercentile"])
    return replace(out, **kwargs)


def build_pilot_aligned_cfg(
    calibration_path: Path,
    profile: dict[str, Any],
) -> AestheticConfig:
    app = get_config()
    blend_only = _as_tuple(profile.get("stratumBlendOnly")) or ("landscape", "person", "group")
    base = landscape_pilot_config(
        calibration_path,
        use_album_relative=True,
        stratum_blend_only=blend_only,
    )
    base = replace(
        base,
        mllm=app.aesthetic.mllm,
        portrait_lite_enabled=app.aesthetic.portrait_lite_enabled,
    )
    return apply_purpose_pilot_overlay(base, profile)


def profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "stratumPreference",
        "stratumBlendOnly",
        "heroStrata",
        "coverStrata",
        "coverSubjectClarity",
        "coverComposition",
        "heroComposition",
        "heroSubjectClarity",
        "heroColor",
        "albumRelativePercentile",
    )
    return {k: profile[k] for k in keys if k in profile and profile[k] is not None}
