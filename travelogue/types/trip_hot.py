"""Hot-path trip TypedDicts. titleArt is runtime; do not expand trip.schema.json."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict


class StudioBlock(TypedDict, total=False):
    edition: str
    portfolio: dict[str, Any]


class TitleArtPosition(TypedDict, total=False):
    x: float
    y: float


class TitleArtMeta(TypedDict, total=False):
    """Runtime only (CAL D-CAL-09). Not in trip.schema.json."""

    enabled: bool
    stale: bool
    assetPath: str
    openingStyleId: str
    coverAssetId: str
    position: TitleArtPosition


class TripMetaHot(TypedDict, total=False):
    title: str
    hook: str
    titleArt: TitleArtMeta
    coverSecondaryAssetId: str
    edited: bool


class SlotRecord(TypedDict, total=False):
    assetId: str
    role: str
    fit: str


class ScreenRecord(TypedDict, total=False):
    patternId: str
    slots: list[SlotRecord]
    tone: dict[str, Any]


class ChapterRecord(TypedDict, total=False):
    id: str
    index: int | str
    title: str
    lead: str
    screens: list[ScreenRecord]
    patternId: str
    curation: dict[str, Any]


class TripHot(TypedDict, total=False):
    tripId: str
    studio: StudioBlock
    meta: TripMetaHot
    coverAssetId: str
    chapters: list[ChapterRecord]
    assets: list[dict[str, Any]]
    epilogue: str


def read_studio_block(trip: Mapping[str, Any] | None) -> StudioBlock:
    """Missing trip / studio → empty block. Missing edition ≡ journal at the caller."""
    if not isinstance(trip, Mapping):
        return {}
    studio = trip.get("studio")
    if not isinstance(studio, Mapping):
        return {}
    return studio  # type: ignore[return-value]


def read_title_art_meta(trip: Mapping[str, Any] | None) -> TitleArtMeta | None:
    """Return the runtime titleArt object, or None when absent / not a mapping."""
    if not isinstance(trip, Mapping):
        return None
    meta = trip.get("meta") if isinstance(trip.get("meta"), Mapping) else {}
    title_art = meta.get("titleArt") if isinstance(meta, Mapping) else None
    if not isinstance(title_art, Mapping):
        return None
    return title_art  # type: ignore[return-value]
