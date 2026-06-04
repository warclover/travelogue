"""Window-level candidate generation (M4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.registry import MosaicPattern, default_registry, patterns_for_window_size
from travelogue.curation.mosaic.features import feature_summary_for_window
from travelogue.curation.mosaic.runtime import effective_mosaic_window_sizes


@dataclass
class ScreenCandidate:
    pattern_id: str
    ordered_asset_ids: list[str]
    screen: dict
    feature_summary: dict[str, Any] = field(default_factory=dict)
    hard_valid: bool = True


def generate_window_candidates(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    registry: dict[str, MosaicPattern] | None = None,
) -> list[ScreenCandidate]:
    if len(asset_ids) not in effective_mosaic_window_sizes(cfg):
        return []
    reg = registry or default_registry()
    patterns = patterns_for_window_size(len(asset_ids), reg)
    summary = feature_summary_for_window(asset_ids, assets_map)
    out: list[ScreenCandidate] = []
    for pat in patterns:
        ordered = try_order_for_pattern(
            pat.pattern_id,
            asset_ids,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )
        if not ordered:
            continue
        screen = build_screen(pat, ordered, assets_map=assets_map)
        out.append(
            ScreenCandidate(
                pattern_id=pat.pattern_id,
                ordered_asset_ids=ordered,
                screen=screen,
                feature_summary={**summary, "patternId": pat.pattern_id},
                hard_valid=True,
            )
        )
    if cfg.deterministic_strict:
        out.sort(key=lambda c: (c.pattern_id, tuple(c.ordered_asset_ids)))
    return out


def generate_five_candidates(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    **kwargs,
) -> list[ScreenCandidate]:
    """PRD §4.2 alias · five-slot window candidates."""
    if len(asset_ids) != 5:
        return []
    return generate_window_candidates(asset_ids, aspects, assets_map, **kwargs)
