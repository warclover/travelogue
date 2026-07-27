"""
Orientation-aware layout planning for visual-journal.

See docs/LAYOUT-PLANNER.md for product rules (mobile 9:16 vs web 16:9).
"""

from __future__ import annotations

from typing import Literal

from travelogue.config import AppConfig
from travelogue.curation.burst_utils import time_near_sequential
from travelogue.curation.mobile_layout_state import (
    MobilePuzzlePlannerState,
    mobile_puzzle_enabled,
)
from travelogue.layout_contract.orientations import (
    AspectKind,
    ExportLayout,
    OrientationSummary,
    aspect_kind_for_asset,
    summarize_orientations,  # noqa: F401
)
from travelogue.layout_contract.orientations import (
    effective_export_profile as _effective_profile,
)
from travelogue.layout_contract.orientations import (
    is_std_landscape as _is_std_landscape,
)
from travelogue.layout_contract.orientations import (
    is_std_portrait as _is_std_portrait,
)

RowLayout = Literal[
    "landscape-triple",
    "landscape-pair",
    "portrait-triple",
    "portrait-pair",
    "square-triple",
    "square-pair",
    "mobile-landscape-grid-8",
    "mobile-portrait-grid-4",
    "default",
]

LAYOUT_FILL = {"fill": True, "bleed": True, "overlay": True}


def _card(asset_id: str, *, slot: str | None = None) -> dict:
    layout = dict(LAYOUT_FILL)
    if slot:
        layout["slot"] = slot
    return {
        "type": "media-card",
        "assetId": asset_id,
        "layout": layout,
    }


def _row(
    asset_ids: list[str],
    row_layout: RowLayout,
    *,
    caption: str = "",
    layout_hint: str | None = None,
) -> dict:
    item: dict = {
        "type": "media-row",
        "assetIds": asset_ids,
        "rowLayout": row_layout,
    }
    if caption:
        item["caption"] = caption[:60]
    if layout_hint:
        item["layoutHint"] = layout_hint
    return item


def _scroll(asset_ids: list[str]) -> dict:
    return {"type": "media-scroll", "assetIds": asset_ids}


def _apply_gallery_layout(
    ch_items: list[dict],
    *,
    export_layout: ExportLayout = "auto",
) -> list[dict]:
    """
    Gallery chapters: merge loose media-cards into scroll (web); keep single cards (mobile).
    Preserves composed media-row blocks on web.
    """
    profile = _effective_profile(export_layout)
    if profile == "mobile":
        if any(it.get("type") == "media-scroll" for it in ch_items):
            return ch_items
        ids: list[str] = []
        for it in ch_items:
            if it.get("type") == "media-card":
                aid = it.get("assetId")
                if aid:
                    ids.append(aid)
            elif it.get("type") == "media-row":
                ids.extend(it.get("assetIds") or [])
        if len(ids) >= 3:
            return [_scroll(ids)]
        return ch_items

    if any(it.get("type") == "media-scroll" for it in ch_items):
        return ch_items

    out: list[dict] = []
    pending: list[str] = []

    def flush_pending() -> None:
        nonlocal pending
        if not pending:
            return
        if len(pending) >= 3:
            out.append(_scroll(pending[:5]))
        else:
            for aid in pending:
                out.append(_card(aid))
        pending = []

    for it in ch_items:
        if it.get("type") == "media-row":
            flush_pending()
            out.append(it)
        elif it.get("type") == "media-card":
            pending.append(it["assetId"])
        else:
            flush_pending()
            out.append(it)
    flush_pending()
    return out


def _kind(aid: str, aspects: dict[str, AspectKind]) -> AspectKind:
    return aspects.get(aid, "square")


def _can_portrait_pair(k1: AspectKind, k2: AspectKind) -> bool:
    """Web 两竖并排：标准竖版或方图；不含超长竖图。"""
    return k1 in ("portrait", "square") and k2 in ("portrait", "square")


def portrait_group_sizes(count: int) -> list[int]:
    """竖版分组优先级（pair > triple > single）下的瓦片尺寸序列。

    优先输出两列(2)，仅当剩余恰为 3 张时用一个三列(3)吃掉奇数尾巴；
    单列(1)仅在孤张时出现。例：2→[2]、3→[3]、4→[2,2]、5→[2,3]、
    7→[2,2,3]、1→[1]。
    """
    sizes: list[int] = []
    remaining = max(0, int(count))
    while remaining > 0:
        if remaining == 1:
            sizes.append(1)
            remaining -= 1
        elif remaining == 3:
            sizes.append(3)
            remaining -= 3
        else:
            sizes.append(2)
            remaining -= 2
    return sizes


def _mobile_card(aid: str, k: AspectKind) -> dict:
    """Mobile: one asset per row; special slots only for panorama/tall/square."""
    if k == "panorama":
        return _card(aid, slot="panorama")
    if k == "tall":
        return _card(aid, slot="tall")
    if k == "square":
        return _card(aid, slot="square")
    return _card(aid)


def _assets_map_from_list(
    assets: list[dict] | dict[str, dict] | None,
) -> dict[str, dict]:
    if not assets:
        return {}
    if isinstance(assets, dict):
        return assets
    return {str(a.get("id", "")): a for a in assets if a.get("id")}


def _parse_taken_ts(asset: dict) -> float | None:
    from travelogue.curation.burst_utils import parse_taken_ts

    return parse_taken_ts(asset)


def _time_near_chain(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    from travelogue.curation.burst_utils import time_near_chain

    return time_near_chain(asset_ids, assets, burst_seconds=burst_seconds)


def _time_near_sequential(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    return time_near_sequential(asset_ids, assets, burst_seconds=burst_seconds)


def _landscape_stack_sizes(count: int) -> list[int]:
    """Mobile 横版「一列纵向拼图」瓦片尺寸：三列优先，余 2 两行，余 1 单图。

    优先三张一列纵向堆叠(3)；尾巴 2 张堆成 1 列 2 行(2)；仅剩 1 张才单横卡(1)。
    例：3→[3]、4→[3,1]、5→[3,2]、6→[3,3]、7→[3,3,1]、2→[2]、1→[1]。
    """
    sizes: list[int] = []
    remaining = max(0, int(count))
    while remaining >= 3:
        sizes.append(3)
        remaining -= 3
    if remaining == 2:
        sizes.append(2)
    elif remaining == 1:
        sizes.append(1)
    return sizes


def _plan_chapter_items_mobile(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict],
    trip_photo_total: int,
    burst_seconds: float = 3.0,
    puzzle_state: MobilePuzzlePlannerState | None = None,
) -> list[dict]:
    """
    Mobile (9:16 单列扫读):

    - 竖版/方/全景/超长竖：单图卡（竖版恒单图，不做任何竖版并列拼图）。
    - 横版：连续横图按「三列优先」组成「1 列 × N 行」纵向拼图
      (`landscape-triple` / `landscape-pair`)；仅在游程尾部剩 1 张时才落单横卡，
      从而避免单张横版独占一屏。
    """
    items: list[dict] = []
    ids = list(asset_ids)
    i = 0
    while i < len(ids):
        k = _kind(ids[i], aspects)
        if k == "landscape":
            run: list[str] = []
            while i < len(ids) and _kind(ids[i], aspects) == "landscape":
                run.append(ids[i])
                i += 1
            pos = 0
            for size in _landscape_stack_sizes(len(run)):
                if size == 3:
                    items.append(_row(run[pos : pos + 3], "landscape-triple"))
                elif size == 2:
                    items.append(_row(run[pos : pos + 2], "landscape-pair"))
                else:
                    items.append(_mobile_card(run[pos], "landscape"))
                pos += size
            continue
        items.append(_mobile_card(ids[i], k))
        i += 1
    return items


def plan_chapter_items(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    export_layout: ExportLayout = "auto",
    assets: list[dict] | dict[str, dict] | None = None,
    trip_photo_total: int | None = None,
    burst_seconds: float = 3.0,
    puzzle_state: MobilePuzzlePlannerState | None = None,
) -> list[dict]:
    """
    Map asset order → media-card / media-row / media-scroll.

    Mobile: mostly single-column cards; trip > 30 may insert 8-landscape or 4-portrait 2×2 rows.
    Web: row packing for landscape/portrait/square groups.

    Special kinds (never forced into wrong row on web):
    - panorama → 单独宽条卡
    - square → 可 2/3 并列
    - tall → 单独竖卡（不并排）
    - landscape → web 三横 / 两横
    """
    profile = _effective_profile(export_layout)
    if profile == "mobile":
        total = trip_photo_total if trip_photo_total is not None else len(asset_ids)
        return _plan_chapter_items_mobile(
            asset_ids,
            aspects,
            assets_map=_assets_map_from_list(assets),
            trip_photo_total=total,
            burst_seconds=burst_seconds,
            puzzle_state=puzzle_state,
        )

    items: list[dict] = []
    ids = list(asset_ids)
    i = 0
    o = lambda aid: _kind(aid, aspects)  # noqa: E731

    while i < len(ids):
        aid = ids[i]
        k = o(aid)

        if k == "panorama":
            items.append(_card(aid, slot="panorama"))
            i += 1
            continue

        if k == "tall":
            items.append(_card(aid, slot="tall"))
            i += 1
            continue

        if k == "square":
            if i + 2 < len(ids) and o(ids[i + 1]) == "square" and o(ids[i + 2]) == "square":
                items.append(_row(ids[i : i + 3], "square-triple"))
                i += 3
                continue
            if i + 1 < len(ids) and o(ids[i + 1]) == "square":
                items.append(_row([ids[i], ids[i + 1]], "square-pair"))
                i += 2
                continue
            items.append(_card(aid, slot="square"))
            i += 1
            continue

        # 竖版优先两联：对连续标准竖版游程做 pair 优先、triple 作奇偶填充的瓦片化。
        if _is_std_portrait(k):
            run = 1
            while i + run < len(ids) and _is_std_portrait(o(ids[i + run])):
                run += 1
            if run >= 2:
                pos = i
                for size in portrait_group_sizes(run):
                    if size == 3:
                        items.append(_row(ids[pos : pos + 3], "portrait-triple"))
                    elif size == 2:
                        items.append(_row(ids[pos : pos + 2], "portrait-pair"))
                    else:
                        items.append(_card(ids[pos]))
                    pos += size
                i += run
                continue
        if i + 1 < len(ids) and _can_portrait_pair(k, o(ids[i + 1])):
            items.append(_row([ids[i], ids[i + 1]], "portrait-pair"))
            i += 2
            continue
        if _is_std_landscape(k) and i + 2 < len(ids):
            trio = ids[i : i + 3]
            if all(_is_std_landscape(o(x)) for x in trio):
                items.append(_row(trio, "landscape-triple"))
                i += 3
                continue
        if _is_std_landscape(k) and i + 1 < len(ids) and _is_std_landscape(o(ids[i + 1])):
            items.append(_row([ids[i], ids[i + 1]], "landscape-pair"))
            i += 2
            continue
        items.append(_card(aid))
        i += 1

    return items


def distribute_items_to_chapters(
    items: list[dict],
    *,
    min_chapters: int = 3,
    max_chapters: int = 5,
) -> list[list[dict]]:
    n = len(items)
    if n == 0:
        return []

    if n <= 4:
        return [items[:2], items[2:]] if n > 2 else [items]

    chapter_count = 4 if n >= 9 else 3
    chapter_count = max(min_chapters, min(max_chapters, chapter_count))

    if chapter_count == 4 and n >= 8:
        sizes = [max(2, n // 5), max(2, n // 5), max(3, n // 4), 0]
        sizes[3] = n - sum(sizes[:3])
        if sizes[3] < 1:
            sizes[2] -= 1
            sizes[3] = 1
        out: list[list[dict]] = []
        pos = 0
        for sz in sizes:
            out.append(items[pos : pos + sz])
            pos += sz
        if pos < n:
            out[-1].extend(items[pos:])
        return out

    base, rem = divmod(n, chapter_count)
    sizes = [base + (1 if i < rem else 0) for i in range(chapter_count)]
    out = []
    pos = 0
    for sz in sizes:
        out.append(items[pos : pos + sz])
        pos += sz
    return out


def pattern_for_chapter_index(index: int, total: int, items: list[dict]) -> str:
    if index == 1:
        return "open"
    if index == total and total > 1:
        return "close"
    if any(it.get("type") == "media-scroll" for it in items):
        return "gallery"
    if any(
        it.get("type") == "media-card"
        and (it.get("layout") or {}).get("slot") == "panorama"
        for it in items
    ):
        return "gallery"
    return "moment"


def build_chapters_from_plan(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    export_layout: ExportLayout = "auto",
    titles: list[str] | None = None,
    layout_engine: str = "legacy",
    assets: list[dict] | None = None,
) -> tuple[list[dict], OrientationSummary]:
    assets_map = _assets_map_from_list(assets)
    puzzle_state: MobilePuzzlePlannerState | None = None
    if mobile_puzzle_enabled(len(asset_ids)):
        puzzle_state = MobilePuzzlePlannerState.from_trip_total(len(asset_ids))
    items = plan_chapter_items(
        asset_ids,
        aspects,
        export_layout=export_layout,
        assets=assets_map,
        trip_photo_total=len(asset_ids),
        puzzle_state=puzzle_state,
    )
    buckets = distribute_items_to_chapters(items)
    total = len(buckets)
    default_titles = ["抵达", "途中", "片段", "尾声"]
    titles = titles or default_titles

    chapters: list[dict] = []
    for idx, bucket in enumerate(buckets, start=1):
        if not bucket:
            continue
        pat = pattern_for_chapter_index(idx, total, bucket)
        ch_items = list(bucket)
        if pat == "gallery":
            ch_items = _apply_gallery_layout(ch_items, export_layout=export_layout)
        chapters.append(
            {
                "id": f"ch-{idx:02d}",
                "index": idx,
                "patternId": pat,
                "title": titles[min(idx - 1, len(titles) - 1)][:12],
                "lead": "",
                "items": ch_items,
                "curation": {},
            }
        )

    from travelogue.layout_contract.engines import LAYOUT_ENGINE_SCREENS
    from travelogue.layout_engine.adapter import attach_screens_to_chapters

    summary = OrientationSummary(
        total=len(asset_ids),
        landscape=sum(1 for a in asset_ids if aspects.get(a) == "landscape"),
        portrait=sum(1 for a in asset_ids if aspects.get(a) == "portrait"),
        square=sum(1 for a in asset_ids if aspects.get(a) == "square"),
        panorama=sum(1 for a in asset_ids if aspects.get(a) == "panorama"),
        tall=sum(1 for a in asset_ids if aspects.get(a) == "tall"),
        export_layout=export_layout,
    )
    summary_dict = summary.to_dict()
    if layout_engine == LAYOUT_ENGINE_SCREENS and (
        _effective_profile(export_layout) == "web" or export_layout == "auto"
    ):
        from travelogue.config import (
            default_enable_food_grid,
            default_mixed_proximity_seconds,
            default_mundane_grid_buckets,
        )

        chapters = attach_screens_to_chapters(
            chapters,
            aspects,
            assets=assets,
            orientation_summary=summary_dict,
            day_buckets=[asset_ids],
            mixed_proximity_seconds=default_mixed_proximity_seconds(),
            trip_photo_total=len(asset_ids),
            enable_food_grid=default_enable_food_grid(),
            mundane_grid_buckets=default_mundane_grid_buckets(),
        )
        from travelogue.curation.chapter_items import compact_chapter_items_for_screens

        compact_chapter_items_for_screens(chapters)
    return chapters, summary


def build_chapters_from_buckets(
    buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    *,
    export_layout: ExportLayout = "auto",
    titles: list[str] | None = None,
    layout_engine: str = "legacy",
    assets: list[dict] | None = None,
    orientation_summary: dict | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    trip_photo_total: int | None = None,
    pattern_hints: list[str] | None = None,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    layout_density: str | None = None,
    cfg: AppConfig | None = None,
    trip: dict | None = None,
) -> list[dict]:
    """Plan items per chapter bucket (Agent 1 day groups → Agent 1.5 layout)."""
    from travelogue.curation.curate_patterns import resolve_chapter_pattern
    from travelogue.layout_contract.engines import LAYOUT_ENGINE_SCREENS
    from travelogue.layout_engine.adapter import attach_screens_to_chapters

    default_titles = ["抵达", "途中", "片段", "尾声"]
    titles = titles or default_titles
    chapters: list[dict] = []
    non_empty = [b for b in buckets if b]
    total = len(non_empty)
    if trip_photo_total is None and assets:
        trip_photo_total = len(assets)
    elif trip_photo_total is None:
        trip_photo_total = sum(len(b) for b in non_empty)
    assets_map = _assets_map_from_list(assets)
    puzzle_state: MobilePuzzlePlannerState | None = None
    if trip_photo_total and mobile_puzzle_enabled(trip_photo_total):
        puzzle_state = MobilePuzzlePlannerState.from_trip_total(trip_photo_total)
    for idx, asset_ids in enumerate(non_empty, start=1):
        if puzzle_state is not None:
            puzzle_state.begin_chapter()
        items = plan_chapter_items(
            asset_ids,
            aspects,
            export_layout=export_layout,
            assets=assets_map,
            trip_photo_total=trip_photo_total,
            puzzle_state=puzzle_state,
        )
        hint = pattern_hints[idx - 1] if pattern_hints and idx - 1 < len(pattern_hints) else None
        pat = resolve_chapter_pattern(idx, total, items, hint=hint)
        ch_items = list(items)
        if pat == "gallery":
            ch_items = _apply_gallery_layout(ch_items, export_layout=export_layout)
        chapters.append(
            {
                "id": f"ch-{idx:02d}",
                "index": idx,
                "patternId": pat,
                "title": titles[min(idx - 1, len(titles) - 1)][:12],
                "lead": "",
                "items": ch_items,
                "curation": {},
            }
        )
    if layout_engine == LAYOUT_ENGINE_SCREENS and (
        _effective_profile(export_layout) == "web" or export_layout == "auto"
    ):
        from travelogue.config import (
            default_enable_food_grid,
            default_mixed_proximity_seconds,
            default_mundane_grid_buckets,
        )

        if trip_photo_total is None and assets:
            trip_photo_total = len(assets)
        elif trip_photo_total is None:
            trip_photo_total = sum(len(b) for b in non_empty)
        chapters = attach_screens_to_chapters(
            chapters,
            aspects,
            assets=assets,
            orientation_summary=orientation_summary,
            day_buckets=non_empty,
            mixed_proximity_seconds=default_mixed_proximity_seconds(cfg=cfg),
            skip_screen_asset_ids=skip_screen_asset_ids,
            trip_photo_total=trip_photo_total,
            enable_food_grid=enable_food_grid and default_enable_food_grid(cfg=cfg),
            layout_density=layout_density,
            mundane_grid_buckets=(
                mundane_grid_buckets
                if mundane_grid_buckets
                else default_mundane_grid_buckets(cfg=cfg)
            ),
            cfg=cfg,
            # P2VF · cohort admit needs tripId inside picker (omit ⇒ fallback_fill)
            trip=trip,
        )
        from travelogue.curation.chapter_items import compact_chapter_items_for_screens

        compact_chapter_items_for_screens(chapters)
    return chapters


# Backward-compatible alias
orientation_for_asset = aspect_kind_for_asset
