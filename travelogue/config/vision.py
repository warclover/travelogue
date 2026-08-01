"""Vision / CLIP tagging configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config._common import TriState, normalize_tri_state
from travelogue.config_helpers import cfg_bool, cfg_float, cfg_get, cfg_int


@dataclass
class VisionConfig:
    enabled: TriState = "false"
    auto_min_photos: int = 80
    auto_min_eligible_ratio: float = 0.60
    # ALG-V3 OQ-02 · option C: empty = nobody; tripId list or "*" (dogfood only).
    # Never flips the default TriState off → auto/true for all trips.
    cohort_trip_ids: tuple[str, ...] = ()
    provider: str = "none"
    model: str = "ViT-B/32"
    max_tags_per_asset: int = 5
    subject_prompts: tuple[str, ...] = ()
    batch_size: int = 16
    session_singleton: bool = True
    prefer_web_derivative: bool = True
    preload_on_folder_pick: bool = True
    batch_auto_tune: bool = True
    batch_auto_tune_samples: int = 8
    dynamic_backoff: bool = True
    prefetch: bool = True
    web_derivative_cosine_max: float = 0.02


def _str_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    out: list[str] = []
    for item in raw:
        s = str(item).strip()
        if s:
            out.append(s)
    return tuple(out)


def vision_cohort_allows(trip_id: str | None, cohort: tuple[str, ...] | list[str] | None) -> bool:
    """True when ``trip_id`` is in the vision cohort (or cohort contains ``*``)."""
    ids = tuple(cohort or ())
    if not ids:
        return False
    if "*" in ids:
        return True
    tid = str(trip_id or "").strip()
    return bool(tid) and tid in ids


def vision_from_dict(raw: dict[str, Any]) -> VisionConfig:
    enabled_raw = raw.get("enabled", False)
    if isinstance(enabled_raw, bool):
        enabled = "true" if enabled_raw else "false"
    else:
        enabled = normalize_tri_state(enabled_raw, default="false")
    prompts_raw = cfg_get(raw, "subject_prompts", "subjectPrompts", ())
    prompts = tuple(str(p).strip() for p in prompts_raw if str(p).strip()) if isinstance(prompts_raw, list) else ()
    cohort_raw = raw.get("cohort_trip_ids", raw.get("cohortTripIds"))
    return VisionConfig(
        enabled=enabled,
        auto_min_photos=cfg_int(raw, "auto_min_photos", "autoMinPhotos", 80),
        auto_min_eligible_ratio=cfg_float(raw, "auto_min_eligible_ratio", "autoMinEligibleRatio", 0.60),
        cohort_trip_ids=_str_tuple(cohort_raw) if cohort_raw is not None else (),
        provider=str(raw.get("provider", "none")),
        model=str(raw.get("model", "ViT-B/32")),
        max_tags_per_asset=int(raw.get("max_tags_per_asset", 5)),
        subject_prompts=prompts,
        batch_size=cfg_int(raw, "batch_size", "batchSize", 16),
        session_singleton=cfg_bool(raw, "session_singleton", "sessionSingleton", True),
        prefer_web_derivative=cfg_bool(raw, "prefer_web_derivative", "preferWebDerivative", True),
        preload_on_folder_pick=cfg_bool(raw, "preload_on_folder_pick", "preloadOnFolderPick", True),
        batch_auto_tune=cfg_bool(raw, "batch_auto_tune", "batchAutoTune", True),
        batch_auto_tune_samples=cfg_int(raw, "batch_auto_tune_samples", "batchAutoTuneSamples", 8),
        dynamic_backoff=cfg_bool(raw, "dynamic_backoff", "dynamicBackoff", True),
        prefetch=bool(raw.get("prefetch", True)),
        web_derivative_cosine_max=cfg_float(
            raw, "web_derivative_cosine_max", "webDerivativeCosineMax", 0.02
        ),
    )
