"""WindowContext for usage rule evaluation (layout kernel)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.layout_contract.orientations import AspectKind

DEFAULT_FEATURED_WEIGHT = 1.35


@dataclass(frozen=True)
class WindowContext:
    window_asset_ids: tuple[str, ...]
    aspects: dict[str, AspectKind]
    assets_map: dict[str, dict]
    layout_state: object | None
    median_sharp: float | None = None
    featured_weight: float = DEFAULT_FEATURED_WEIGHT


def build_window_context(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    layout_state: object | None = None,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
) -> WindowContext:
    return WindowContext(
        window_asset_ids=tuple(asset_ids),
        aspects=aspects,
        assets_map=assets_map,
        layout_state=layout_state,
        median_sharp=median_sharp,
        featured_weight=featured_weight,
    )
