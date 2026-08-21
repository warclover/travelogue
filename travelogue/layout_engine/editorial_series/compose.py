"""Assemble a portfolio trip: series match → screens[].

Production catalog is ``editorial_series/series/`` (P0 ``magazine-16-standard``).
Tests may pass ``series`` or ``series_dir`` (never ``docs/templates/reserve/``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from travelogue.config.edition import (
    PORTFOLIO_UNAVAILABLE_MESSAGE,
    PortfolioUnavailableError,
    portfolio_pipeline_config,
)
from travelogue.layout_engine.editorial_series.catalog import (
    assert_not_reserve_path,
    load_official_series,
)
from travelogue.layout_engine.editorial_series.match import (
    groups_from_assets,
    select_series,
    snap_user_page_count,
)
from travelogue.layout_engine.editorial_series.place import (
    attach_screens_to_chapters,
    place_groups,
)


def compose_portfolio_trip(
    chapters: list[dict[str, Any]],
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return ``(chapters, replan_meta)`` or raise ``PortfolioUnavailableError``.

    Extra kwargs (``series``, ``series_dir``) are test-only. Runtime curate
    omits them so production uses the official catalog. Empty catalog still
    hard-fails.
    """
    series_override = kwargs.get("series")
    series_dir = kwargs.get("series_dir")
    assets = kwargs.get("assets")
    buckets = kwargs.get("buckets") or []
    trip = kwargs.get("trip")
    app_cfg = kwargs.get("app_cfg")

    catalog = _load_catalog(series_override, series_dir)
    if not catalog:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    groups = groups_from_assets(assets, buckets=buckets)
    kept_n = sum(len(g["asset_ids"]) for g in groups)
    if kept_n <= 0:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    pipe = portfolio_pipeline_config(app_cfg)
    page_count, page_count_source = _page_request(trip)
    requested_pages = page_count
    snap_hint = None
    if page_count_source == "user" and page_count:
        page_count, snap_hint = snap_user_page_count(
            page_count,
            catalog,
            max_pages=int(pipe.max_pages or 32),
        )
    choice = select_series(
        catalog,
        kept_n=kept_n,
        page_count=page_count,
        page_count_source=page_count_source,
        max_pages=int(pipe.max_pages or 32),
    )
    if choice is None:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    placed = place_groups(
        groups,
        choice.series.get("sequence") or [],
        cap=choice.cap,
    )
    if not placed.pages:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    attach_screens_to_chapters(chapters, placed.pages, buckets=buckets)
    from travelogue.layout_contract.chapter_items import compact_chapter_items_for_screens

    compact_chapter_items_for_screens(chapters)

    photos_placed = sum(len(p.asset_ids) for p in placed.pages)
    leftover = list(placed.leftover_ids)
    overflow: dict[str, Any] | None = None
    if photos_placed < kept_n:
        overflow = {
            "count": kept_n - photos_placed,
            "resolution": choice.overflow_resolution or "capped",
            "assetIds": leftover,
        }
    _stamp_portfolio(
        trip,
        series_id=str(choice.series.get("id") or ""),
        page_count=int(choice.series.get("pageCount") or len(placed.pages)),
        page_count_source=page_count_source,
        density=str(choice.series.get("density") or "standard"),
        photos_placed=photos_placed,
        photos_kept=kept_n,
        overflow=overflow,
        match={
            "flexUsed": list(placed.used_roles),
            "droppedRoles": list(placed.dropped_roles),
            "nearMiss": "photo_span" if (choice.upgraded or choice.capped) else None,
            "pageCountRequested": requested_pages if page_count_source == "user" else None,
            "pageCountHint": snap_hint,
        },
    )
    replan_meta = {
        "editorialSeries": True,
        "seriesId": choice.series.get("id"),
        "photosPlaced": photos_placed,
        "photosKept": kept_n,
        "overflow": overflow,
    }
    return chapters, replan_meta


def _load_catalog(
    series_override: Sequence[Mapping[str, Any]] | None,
    series_dir: Path | str | None,
) -> list[dict[str, Any]]:
    if series_override is not None:
        return [dict(s) for s in series_override]
    path = Path(series_dir) if series_dir is not None else None
    if path is not None:
        assert_not_reserve_path(path)
    return load_official_series(series_dir=path)


def _page_request(trip: Mapping[str, Any] | None) -> tuple[int | None, str]:
    if not isinstance(trip, Mapping):
        return None, "auto"
    studio = trip.get("studio")
    if not isinstance(studio, Mapping):
        return None, "auto"
    block = studio.get("portfolio")
    if not isinstance(block, Mapping):
        return None, "auto"
    source = str(block.get("pageCountSource") or "auto").strip().lower() or "auto"
    raw = block.get("pageCount")
    page_count = int(raw) if raw not in (None, "") else None
    return page_count, source


def _stamp_portfolio(
    trip: dict[str, Any] | None,
    *,
    series_id: str,
    page_count: int,
    page_count_source: str,
    density: str,
    photos_placed: int,
    photos_kept: int,
    overflow: dict[str, Any] | None,
    match: dict[str, Any],
) -> None:
    if not isinstance(trip, dict):
        return
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        studio = {}
        trip["studio"] = studio
    block = studio.get("portfolio")
    if not isinstance(block, dict):
        block = {}
        studio["portfolio"] = block
    block["seriesId"] = series_id
    block["pageCount"] = page_count
    block["pageCountSource"] = page_count_source
    block["density"] = density
    block["photosPlaced"] = photos_placed
    block["photosKept"] = photos_kept
    if overflow:
        block["overflow"] = overflow
    else:
        block.pop("overflow", None)
    block["match"] = match
