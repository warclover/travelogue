"""Journal folio: foreword, trip-index, featured-grid."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.render.context_types import (
    FeaturedGridCardContext,
    ForewordSpreadContext,
    TripIndexEntryContext,
)
from travelogue.render.surface import SurfaceContext


@dataclass
class JournalFolioState:
    folio_plan: dict
    grid_exclude: frozenset[str]
    foreword_spread: ForewordSpreadContext | None
    has_foreword_spread: bool


def resolve_journal_folio_plan(
    trip: dict,
    surface: SurfaceContext,
    *,
    hook: str,
) -> JournalFolioState:
    folio_plan: dict = {}
    grid_exclude: frozenset[str] = frozenset()
    if surface.folio_full:
        from travelogue.curation.folio_plan import resolve_folio_plan

        layout_eligible = [a for a in trip.get("assets", []) if a.get("layoutEligible", True)]
        folio_plan = resolve_folio_plan(trip, trip.get("chapters") or [], layout_eligible)
        if folio_plan.get("featuredGrid"):
            grid_exclude = frozenset(folio_plan.get("featuredGridAssetIds") or [])

    foreword_spread: ForewordSpreadContext | None = None
    has_foreword_spread = False
    if surface.folio_full and folio_plan.get("foreword"):
        from travelogue.render.context import build_foreword_spread

        chapters_raw = trip.get("chapters") or []
        if chapters_raw:
            first_lead = (chapters_raw[0].get("lead") or "").strip()
            if first_lead and not surface.strip_narrative_copy:
                foreword_spread = build_foreword_spread(chapters_raw[0], trip_hook=hook)
                has_foreword_spread = foreword_spread is not None

    return JournalFolioState(
        folio_plan=folio_plan,
        grid_exclude=grid_exclude,
        foreword_spread=foreword_spread,
        has_foreword_spread=has_foreword_spread,
    )


def build_journal_folio_extras(
    trip: dict,
    surface: SurfaceContext,
    folio: JournalFolioState,
    chapters_out: list,
    *,
    meta_title: str,
):
    from travelogue.render.context import (
        build_featured_grid_cards,
        build_trip_index_entries,
    )
    from travelogue.render.journal_chapters import ChaptersRenderBundle

    trip_index_entries: list[TripIndexEntryContext] = []
    featured_grid_cards: list[FeaturedGridCardContext] = []
    has_trip_index = False
    has_featured_grid = False
    if surface.folio_full and folio.folio_plan.get("index"):
        trip_index_entries = build_trip_index_entries(trip.get("chapters") or [])
        has_trip_index = bool(trip_index_entries)
    if surface.folio_full and folio.folio_plan.get("featuredGrid"):
        featured_grid_cards = build_featured_grid_cards(
            list(folio.folio_plan.get("featuredGridAssetIds") or []),
            surface.assets,
            meta_title=meta_title,
            export_layout=surface.image_layout,
        )
        has_featured_grid = len(featured_grid_cards) >= 4

    return ChaptersRenderBundle(
        chapters_out=chapters_out,
        foreword_spread=folio.foreword_spread,
        has_foreword_spread=folio.has_foreword_spread,
        trip_index_entries=trip_index_entries,
        has_trip_index=has_trip_index,
        featured_grid_cards=featured_grid_cards,
        has_featured_grid=has_featured_grid,
    )
