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
from travelogue.layout_engine.editorial_series.fill import (
    FULFILL_MIN,
    fill_groups_from_assets,
    fulfillment_ratio,
    is_sparse_collection,
)
from travelogue.layout_engine.editorial_series.match import (
    groups_from_assets,
    select_series,
    series_capacity,
    snap_user_page_count,
)
from travelogue.layout_engine.editorial_series.place import (
    PlaceResult,
    attach_screens_to_chapters,
    place_groups,
)
from travelogue.layout_engine.editorial_series.slot_match import collect_asset_aspects


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

    sparse = is_sparse_collection(assets)
    if sparse:
        groups = groups_from_assets(assets, buckets=buckets)
    else:
        groups = fill_groups_from_assets(assets, trip=trip, buckets=buckets)
    kept_n = sum(len(g["asset_ids"]) for g in groups)
    if kept_n <= 0:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    pipe = portfolio_pipeline_config(app_cfg)
    max_pages = int(pipe.max_pages or 48)
    page_count, page_count_source = _page_request(trip)
    requested_pages = page_count
    snap_hint = None
    if page_count_source == "user" and page_count:
        page_count, snap_hint = snap_user_page_count(
            page_count,
            catalog,
            max_pages=max_pages,
        )
    choice = select_series(
        catalog,
        kept_n=kept_n,
        page_count=page_count,
        page_count_source=page_count_source,
        max_pages=max_pages,
    )
    if choice is None:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    aspect_kinds, aspect_ratios = collect_asset_aspects(assets)
    placed = _place_choice(
        groups, choice, aspect_kinds, aspect_ratios, buckets=buckets
    )
    fulfill_hint = None
    if (
        not sparse
        and page_count_source == "auto"
        and _fulfillment(placed, choice) < FULFILL_MIN
    ):
        better = _better_fulfilling_choice(
            catalog,
            groups,
            kept_n=kept_n,
            max_pages=max_pages,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
            current=choice,
            buckets=buckets,
        )
        if better is not None:
            alt_placed = _place_choice(
                groups, better, aspect_kinds, aspect_ratios, buckets=buckets
            )
            if alt_placed.pages:
                fulfill_hint = f"你的照片更适合 {int(better.series.get('pageCount') or 0)} 页"
                choice = better
                placed = alt_placed
    elif (
        not sparse
        and page_count_source == "user"
        and _fulfillment(placed, choice) < FULFILL_MIN
    ):
        auto = select_series(
            catalog, kept_n=kept_n, page_count_source="auto", max_pages=max_pages
        )
        if auto is not None and auto.series.get("id") != choice.series.get("id"):
            hollow = max(0, int(choice.series.get("pageCount") or 0) - placed.fulfilled_pages)
            fulfill_hint = (
                f"有 {hollow} 页没排满，换 "
                f"{int(auto.series.get('pageCount') or 0)} 页会更饱满"
            )
    if sparse and not fulfill_hint:
        fulfill_hint = "这些照片间隔较大，预设编排排不饱满"
    if not placed.pages:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)

    attach_screens_to_chapters(chapters, placed.pages, buckets=buckets)
    from travelogue.layout_contract.chapter_items import compact_chapter_items_for_screens

    compact_chapter_items_for_screens(chapters)
    _clear_items_on_empty_portfolio_chapters(chapters)

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
            "pageCountHint": snap_hint or fulfill_hint,
        },
        fulfillment=_sequence_fulfillment(placed, choice, photos_placed),
        sparse=sparse,
    )
    replan_meta = {
        "editorialSeries": True,
        "seriesId": choice.series.get("id"),
        "photosPlaced": photos_placed,
        "photosKept": kept_n,
        "overflow": overflow,
        "sequenceFulfillment": _sequence_fulfillment(placed, choice, photos_placed),
        "sparseCollection": sparse,
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


def _place_choice(
    groups: Sequence[Mapping[str, Any]],
    choice: Any,
    aspect_kinds: Mapping[str, str],
    aspect_ratios: Mapping[str, float] | None = None,
    buckets: Sequence[Sequence[str]] | None = None,
) -> PlaceResult:
    sequence = choice.series.get("sequence") or []
    if _should_split_across_chapters(buckets):
        return _place_across_chapter_buckets(
            groups,
            sequence,
            buckets=buckets,
            cap=choice.cap,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
    return place_groups(
        groups,
        sequence,
        cap=choice.cap,
        aspect_kinds=aspect_kinds,
        aspect_ratios=aspect_ratios,
    )


def _should_split_across_chapters(buckets: Sequence[Sequence[str]] | None) -> bool:
    if not buckets:
        return False
    return sum(1 for b in buckets if b) >= 2


def _place_across_chapter_buckets(
    groups: Sequence[Mapping[str, Any]],
    sequence: Sequence[Mapping[str, Any]],
    *,
    buckets: Sequence[Sequence[str]],
    cap: int | None,
    aspect_kinds: Mapping[str, str],
    aspect_ratios: Mapping[str, float] | None,
) -> PlaceResult:
    """Keep the official sequence continuous, but do not let chapter 1 eat it.

    D-PFM-14 · pages stay in series order and attach to existing chapters.
    A global cap otherwise consumes early-day photos only; later chapters
    then render leftover journal ``items`` (web long-image).
    """
    owner: dict[str, int] = {}
    for i, bucket in enumerate(buckets):
        for aid in bucket:
            if aid:
                owner.setdefault(str(aid), i)
    by_ch: list[list[dict[str, Any]]] = [[] for _ in buckets]
    unowned: list[dict[str, Any]] = []
    for raw in groups:
        g = {
            "id": raw.get("id"),
            "kind": raw.get("kind") or "scene",
            "asset_ids": [str(a) for a in (raw.get("asset_ids") or []) if a],
        }
        if not g["asset_ids"]:
            continue
        idx = next((owner[a] for a in g["asset_ids"] if a in owner), None)
        if idx is None or idx < 0 or idx >= len(by_ch):
            unowned.append(g)
        else:
            by_ch[idx].append(g)
    if unowned and by_ch:
        by_ch[0] = unowned + by_ch[0]

    sizes = [sum(len(g.get("asset_ids") or []) for g in gs) for gs in by_ch]
    shares = _page_shares(len(sequence), sizes)
    remaining_cap = cap
    result = PlaceResult()
    offset = 0
    for i, gs in enumerate(by_ch):
        take = shares[i]
        slice_seq = list(sequence[offset : offset + take])
        offset += take
        if not gs or not slice_seq:
            for g in gs:
                result.leftover_ids.extend(g.get("asset_ids") or [])
            continue
        part = place_groups(
            gs,
            slice_seq,
            cap=remaining_cap,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
        result.pages.extend(part.pages)
        result.leftover_ids.extend(part.leftover_ids)
        result.dropped_roles.extend(part.dropped_roles)
        result.used_roles.extend(part.used_roles)
        result.demoted_pages += part.demoted_pages
        result.fulfilled_pages += part.fulfilled_pages
        if remaining_cap is not None:
            used = sum(len(p.asset_ids) for p in part.pages)
            remaining_cap = max(0, int(remaining_cap) - used)
    return result


def _page_shares(n_pages: int, sizes: Sequence[int]) -> list[int]:
    """Min 1 page per nonempty chapter; leftover pages by photo count (Hamilton)."""
    n = len(sizes)
    shares = [0] * n
    active = [i for i, s in enumerate(sizes) if s > 0]
    if not active or n_pages <= 0:
        return shares
    if n_pages <= len(active):
        for i in active[:n_pages]:
            shares[i] = 1
        return shares
    for i in active:
        shares[i] = 1
    rest = n_pages - len(active)
    total = sum(sizes[i] for i in active)
    if rest <= 0 or total <= 0:
        return shares
    floors = {i: (rest * sizes[i]) // total for i in active}
    rem = rest - sum(floors.values())
    order = sorted(
        active,
        key=lambda i: ((rest * sizes[i]) % total, sizes[i], -i),
        reverse=True,
    )
    for i in order[:rem]:
        floors[i] += 1
    for i in active:
        shares[i] += floors[i]
    return shares


def _clear_items_on_empty_portfolio_chapters(chapters: list[dict[str, Any]]) -> None:
    """D-PFM-27 · empty screens must not keep journal media-row/card leftovers."""
    for ch in chapters:
        if ch.get("screens"):
            continue
        ch["items"] = []
        ch.setdefault("curation", {})["layoutStub"] = True


def _fulfillment(placed: PlaceResult, choice: Any) -> float:
    planned = len(choice.series.get("sequence") or [])
    return fulfillment_ratio(
        fulfilled_pages=placed.fulfilled_pages, planned_pages=planned
    )


def _sequence_fulfillment(
    placed: PlaceResult,
    choice: Any,
    photos_placed: int,
) -> dict[str, Any]:
    planned = len(choice.series.get("sequence") or [])
    cap = series_capacity(choice.series) or 1
    return {
        "plannedPages": planned,
        "renderedPages": len(placed.pages),
        "fillRatio": round(photos_placed / cap, 4),
        "demotedPages": placed.demoted_pages,
        "droppedRoles": list(placed.dropped_roles),
    }


def _better_fulfilling_choice(
    catalog: Sequence[Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
    *,
    kept_n: int,
    max_pages: int,
    aspect_kinds: Mapping[str, str],
    current: Any,
    aspect_ratios: Mapping[str, float] | None = None,
    buckets: Sequence[Sequence[str]] | None = None,
) -> Any:
    current_density = str(current.series.get("density") or "standard").strip().lower()
    viable: list[dict[str, Any]] = []
    for row in catalog:
        if str(row.get("id") or "") == str(current.series.get("id") or ""):
            continue
        row_density = str(row.get("density") or "standard").strip().lower()
        if row_density != current_density:
            continue
        trial = select_series(
            [row],
            kept_n=kept_n,
            page_count=int(row.get("pageCount") or 0),
            page_count_source="user",
            max_pages=max_pages,
        )
        if trial is None:
            continue
        placed = _place_choice(
            groups, trial, aspect_kinds, aspect_ratios, buckets=buckets
        )
        if _fulfillment(placed, trial) >= FULFILL_MIN:
            viable.append(dict(row))
    if not viable:
        return None
    return select_series(
        viable, kept_n=kept_n, page_count_source="auto", max_pages=max_pages
    )


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
    fulfillment: dict[str, Any] | None = None,
    sparse: bool = False,
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
    if fulfillment:
        block["sequenceFulfillment"] = fulfillment
    else:
        block.pop("sequenceFulfillment", None)
    if sparse:
        block["sparseCollection"] = True
    else:
        block.pop("sparseCollection", None)
