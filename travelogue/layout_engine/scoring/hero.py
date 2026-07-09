"""Hero score adapter (layout_engine · dispatches via layout_contract registry)."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from travelogue.layout_contract.scoring import (
    effective_hero_score as _dispatch,
)
from travelogue.layout_contract.scoring import (
    get_effective_hero_score_impl,
)
from travelogue.layout_contract.scoring import (
    median_sharpness as median_sharpness,  # noqa: F401
)


def _ensure_registered() -> None:
    if get_effective_hero_score_impl() is not None:
        return
    # String import avoids a layout_engine→curation AST edge (ADR-015 gate).
    import_module("travelogue.curation.curate_scoring")


def effective_hero_score(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    cover_scoring_v2: Any = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
) -> float:
    _ensure_registered()
    return _dispatch(
        asset,
        median_sharp=median_sharp,
        aesthetic_enabled=aesthetic_enabled,
        featured_weight=featured_weight,
        memory_anchors=memory_anchors,
        meta_places=meta_places,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
        pool=pool,
    )
