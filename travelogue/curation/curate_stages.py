"""Curate pipeline stages (AAD-10).

Keep this module free of ``layout_engine`` imports so splitting does not inflate
curation→layout_engine cross-import edges (ADR-015 / AAD-11). Bucket/preflight
helpers that touch LSE stay in ``curate.py`` until adapter thin-out (M3).
"""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig


def stage_refresh_cull_cohort(
    trip: dict,
    *,
    trip_dir: Path | None,
    cfg: AppConfig | None,
    curate_scope: str,
    refresh_algorithms: bool | None,
) -> dict | None:
    """Refresh cull profile and optional cohort face tags."""
    from travelogue.curation.algorithm_profile import maybe_refresh_cull

    maybe_refresh_cull(
        trip,
        trip_dir=trip_dir,
        app_cfg=cfg,
        refresh_algorithms=(
            False if curate_scope == "tier" and refresh_algorithms is None else refresh_algorithms
        ),
    )
    if trip_dir is None:
        return None
    from travelogue.curation.cohort_faces import apply_cohort_tags

    return apply_cohort_tags(trip, trip_dir=trip_dir, cfg=cfg)
