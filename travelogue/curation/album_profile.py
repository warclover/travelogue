"""Stratified curation · album stratum composition (PRD-SC §6)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset
from travelogue.curation.curate import layout_eligible_assets
from travelogue.util.datetime_ import utc_now_iso

ReviewStratum = Literal["person", "landscape", "food", "group", "general"]
_STRATA: tuple[ReviewStratum, ...] = ("person", "group", "landscape", "food", "general")
STRATUM_PREFERENCE_VALUES: tuple[str, ...] = ("auto", "landscape", "portrait")
_PORTRAIT_PRIORITY_STRATA = frozenset({"person", "group"})
_LANDSCAPE_PRIORITY_STRATA = frozenset({"landscape"})


def compute_album_profile(trip: dict) -> dict[str, Any]:
    """Stratum share among layout-eligible images."""
    eligible = layout_eligible_assets(trip)
    counts: dict[str, int] = {s: 0 for s in _STRATA}
    for asset in eligible:
        stratum = review_stratum_for_asset(asset)
        counts[stratum] = counts.get(stratum, 0) + 1
    n = len(eligible)
    strata: dict[str, float] = {}
    for key, count in counts.items():
        if count > 0:
            strata[key] = round(count / n, 4) if n else 0.0
    dominant = "general"
    if strata:
        dominant = max(strata, key=lambda k: strata[k])
    top_share = strata.get(dominant, 0.0)
    return {
        "version": "1",
        "computedAt": utc_now_iso(),
        "eligibleImages": n,
        "strata": strata,
        "dominantStratum": dominant,
        "isSkewed": bool(n and top_share >= 0.7),
    }


def write_album_profile(trip: dict) -> dict[str, Any]:
    """Persist ``trip.curation.albumProfile``."""
    profile = compute_album_profile(trip)
    curation = trip.setdefault("curation", {})
    curation["albumProfile"] = profile
    return profile


def album_profile_for_trip(trip: dict) -> dict[str, Any]:
    """Read stored profile or compute without persisting."""
    stored = (trip.get("curation") or {}).get("albumProfile")
    if isinstance(stored, dict) and stored.get("strata"):
        return dict(stored)
    return compute_album_profile(trip)


def profile_priority_strata(profile: dict | None, *, top_n: int = 2) -> frozenset[str]:
    """Dominant + secondary strata for MLLM shortlist prioritization (PRD-SC §6.2)."""
    if not profile:
        return frozenset()
    strata = profile.get("strata")
    if isinstance(strata, dict) and strata:
        ordered = sorted(strata.items(), key=lambda kv: (-float(kv[1] or 0), kv[0]))
        return frozenset(k for k, _ in ordered[: max(1, top_n)])
    dominant = profile.get("dominantStratum")
    return frozenset({str(dominant)}) if dominant else frozenset()


def normalize_stratum_preference(value: Any) -> str:
    pref = str(value or "auto").strip().lower()
    return pref if pref in STRATUM_PREFERENCE_VALUES else "auto"


def stratum_preference_for_trip(trip: dict | None) -> str:
    if not trip:
        return "auto"
    curation = trip.get("curation") or {}
    raw = curation.get("stratumPreference", curation.get("stratumPref"))
    return normalize_stratum_preference(raw)


def apply_stratum_preference(trip: dict, preference: str) -> str:
    pref = normalize_stratum_preference(preference)
    trip.setdefault("curation", {})["stratumPreference"] = pref
    return pref


def effective_priority_strata(
    profile: dict | None,
    *,
    preference: str = "auto",
    top_n: int = 2,
) -> frozenset[str]:
    """MLLM / selection priority strata with optional user override (P4-3)."""
    pref = normalize_stratum_preference(preference)
    if pref == "landscape":
        return _LANDSCAPE_PRIORITY_STRATA
    if pref == "portrait":
        return _PORTRAIT_PRIORITY_STRATA
    return profile_priority_strata(profile, top_n=top_n)


_STRATUM_LABELS_ZH: dict[str, str] = {
    "person": "人像",
    "landscape": "风景",
    "food": "美食",
    "group": "合影",
    "general": "通用",
}


def stratum_selection_hint(
    profile: dict | None,
    *,
    preference: str = "auto",
) -> str:
    pref = normalize_stratum_preference(preference)
    if pref == "landscape":
        return "已设为更偏风景 · 封面与 MLLM 短名单优先横图/风景层"
    if pref == "portrait":
        return "已设为更偏人像 · 合影/单人优先参与 ML 校准与 MLLM 短名单"
    dominant = str((profile or {}).get("dominantStratum") or "general")
    label = _STRATUM_LABELS_ZH.get(dominant, dominant)
    return f"自动 · 本册以{label}为主，按相册组成选图"
