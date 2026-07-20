"""LTN C7 · curated / archive / quick_share mosaic track params.

Tracks are parameter overlays on the shared MCS path (not separate planners).

LTN E4 · ``dense_collage_max_cap`` is a hard ceiling only. Soft opportunity
floors live in ``asymmetric_quota.dense_opportunity_min_for`` and never force emit.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from travelogue.config import MosaicConfig

MosaicTrack = Literal["curated", "archive", "quick_share"]


@dataclass(frozen=True)
class MosaicTrackParams:
    track: MosaicTrack
    min_candidate_score: float
    beat_profile: str
    enable_size3_aux: bool
    # Cap dense collage max after P21/density; None = no extra cap.
    dense_collage_max_cap: int | None


# PRD §11 defaults (documentation + runtime overlay).
DEFAULT_TRACK_TABLE: dict[MosaicTrack, MosaicTrackParams] = {
    "curated": MosaicTrackParams(
        track="curated",
        min_candidate_score=0.35,
        beat_profile="classic_magazine",
        enable_size3_aux=False,
        dense_collage_max_cap=2,
    ),
    "archive": MosaicTrackParams(
        track="archive",
        min_candidate_score=0.35,
        beat_profile="classic_magazine",
        enable_size3_aux=False,
        dense_collage_max_cap=None,
    ),
    "quick_share": MosaicTrackParams(
        track="quick_share",
        min_candidate_score=0.40,
        beat_profile="flat",
        enable_size3_aux=False,
        dense_collage_max_cap=1,
    ),
}


def resolve_mosaic_track(
    *,
    kept_count: int,
    intent_mode: str | None = None,
) -> MosaicTrack:
    """Resolve product track from import intent + kept size (PRD §11)."""
    mode = str(intent_mode or "").strip().lower().replace("-", "_")
    if mode in ("quick_share", "quickshare", "quick"):
        return "quick_share"
    if int(kept_count) >= 100:
        return "archive"
    return "curated"


def track_params_for(
    track: MosaicTrack,
    *,
    table: dict[MosaicTrack, MosaicTrackParams] | None = None,
) -> MosaicTrackParams:
    tbl = table or DEFAULT_TRACK_TABLE
    return tbl.get(track) or DEFAULT_TRACK_TABLE["curated"]


def apply_mosaic_track(
    cfg: MosaicConfig,
    params: MosaicTrackParams,
) -> MosaicConfig:
    """Overlay track knobs onto a MosaicConfig (shared MCS path)."""
    return replace(
        cfg,
        min_candidate_score=float(params.min_candidate_score),
        lse_beat_profile=str(params.beat_profile),
        enable_size3_aux=bool(params.enable_size3_aux),
        track_id=str(params.track),
        track_dense_collage_cap=params.dense_collage_max_cap,
    )


def resolve_and_apply_mosaic_track(
    cfg: MosaicConfig,
    *,
    kept_count: int,
    intent_mode: str | None = None,
) -> tuple[MosaicConfig, MosaicTrackParams]:
    track = resolve_mosaic_track(kept_count=kept_count, intent_mode=intent_mode)
    params = track_params_for(track)
    return apply_mosaic_track(cfg, params), params
