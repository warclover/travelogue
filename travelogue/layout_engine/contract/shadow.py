"""TPC W1 · mix-index shadow vs live try_order candidate sets (AC-TPC-12).

Shadow never changes selection. It only records diffs for sign-off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Mapping

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_engine.contract.mix_index import (
    MixKey,
    build_mix_inverted_index,
    format_mix_key,
    mix_key_from_aspects,
)
from travelogue.layout_engine.mosaic.builders import try_order_for_pattern
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.pattern_catalog import patterns_for_window_size


@dataclass
class MixShadowDiff:
    window_mix: str
    live_pattern_ids: list[str]
    index_pattern_ids: list[str]
    only_in_live: list[str] = field(default_factory=list)
    only_in_index: list[str] = field(default_factory=list)

    @property
    def has_diff(self) -> bool:
        return bool(self.only_in_live or self.only_in_index)

    def to_dict(self) -> dict[str, Any]:
        return {
            "windowMix": self.window_mix,
            "livePatternIds": list(self.live_pattern_ids),
            "indexPatternIds": list(self.index_pattern_ids),
            "onlyInLive": list(self.only_in_live),
            "onlyInIndex": list(self.only_in_index),
            "hasDiff": self.has_diff,
        }


@lru_cache(maxsize=1)
def _cached_mix_index() -> dict[MixKey, tuple[str, ...]]:
    from travelogue.layout_templates.registry import get_engine

    templates = {t.id: t for t in get_engine().list_active(enforce_quotas=False)}
    index = build_mix_inverted_index(templates)
    return {k: tuple(v) for k, v in index.items()}


def reset_mix_index_cache_for_tests() -> None:
    _cached_mix_index.cache_clear()


def index_pattern_ids_for_mix(
    key: MixKey,
    *,
    mosaic_only: bool = True,
) -> list[str]:
    """Active LTE template ids registered under ``key`` (stable sorted).

    When ``mosaic_only`` (default), intersect with the MCS mosaic registry so
    AC-TPC-12 diffs compare like-for-like candidate universes.
    """
    ids = [str(x) for x in (_cached_mix_index().get(key) or ())]
    if mosaic_only:
        mosaic_ids = set(mosaic_registry().keys())
        ids = [tid for tid in ids if tid in mosaic_ids]
    return sorted(ids)


def live_orderable_pattern_ids(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    assets_map: Mapping[str, dict],
    *,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Patterns for which ``try_order_for_pattern`` returns a non-empty order."""
    reg = registry or mosaic_registry()
    ids: list[str] = []
    for pat in patterns_for_window_size(len(asset_ids), reg):
        ordered = try_order_for_pattern(
            pat.pattern_id,
            list(asset_ids),
            dict(aspects),
            dict(assets_map),
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )
        if ordered:
            ids.append(pat.pattern_id)
    return sorted(ids)


def compute_mix_shadow_diff(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    assets_map: Mapping[str, dict],
    *,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    registry: dict | None = None,
    mix_index: Mapping[MixKey, list[str] | tuple[str, ...]] | None = None,
) -> MixShadowDiff:
    key = mix_key_from_aspects(list(asset_ids), aspects)
    mix_label = format_mix_key(key)
    if mix_index is not None:
        index_ids = sorted(str(x) for x in (mix_index.get(key) or ()))
    else:
        index_ids = index_pattern_ids_for_mix(key, mosaic_only=True)
    live_ids = live_orderable_pattern_ids(
        list(asset_ids),
        aspects,
        assets_map,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        registry=registry,
    )
    live_set = set(live_ids)
    index_set = set(index_ids)
    return MixShadowDiff(
        window_mix=mix_label,
        live_pattern_ids=live_ids,
        index_pattern_ids=index_ids,
        only_in_live=sorted(live_set - index_set),
        only_in_index=sorted(index_set - live_set),
    )
