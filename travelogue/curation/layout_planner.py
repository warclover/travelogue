"""
Orientation-aware layout planning for visual-journal.

See docs/LAYOUT-PLANNER.md for product rules (mobile 9:16 vs web 16:9).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from travelogue.media.image_ops import AspectKind, classify_aspect

ExportLayout = Literal["auto", "mobile", "web"]
RowLayout = Literal[
    "landscape-triple",
    "landscape-pair",
    "portrait-triple",
    "portrait-pair",
    "square-triple",
    "square-pair",
    "default",
]

LAYOUT_FILL = {"fill": True, "bleed": True, "overlay": True}


@dataclass
class OrientationSummary:
    """Counts after ingest (display dimensions, post-crop)."""

    total: int
    landscape: int
    portrait: int
    square: int
    panorama: int
    tall: int
    export_layout: str

    @property
    def dominant(self) -> str:
        counts = {
            "landscape": self.landscape,
            "portrait": self.portrait,
            "square": self.square,
            "panorama": self.panorama,
            "tall": self.tall,
        }
        return max(counts, key=counts.get)  # type: ignore[arg-type]

    def to_dict(self) -> dict:
        return asdict(self)


def aspect_kind_for_asset(asset: dict) -> AspectKind:
    stored = asset.get("aspectKind")
    if stored in ("portrait", "landscape", "square", "panorama", "tall"):
        return stored  # type: ignore[return-value]
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    return classify_aspect(w, h)


def summarize_orientations(
    assets: list[dict],
    *,
    export_layout: ExportLayout = "auto",
) -> OrientationSummary:
    counts = {k: 0 for k in ("landscape", "portrait", "square", "panorama", "tall")}
    for a in assets:
        k = aspect_kind_for_asset(a)
        if k in counts:
            counts[k] += 1
    return OrientationSummary(
        total=len(assets),
        landscape=counts["landscape"],
        portrait=counts["portrait"],
        square=counts["square"],
        panorama=counts["panorama"],
        tall=counts["tall"],
        export_layout=export_layout,
    )


def _effective_profile(export_layout: ExportLayout) -> Literal["mobile", "web"]:
    if export_layout == "web":
        return "web"
    return "mobile"


def _card(asset_id: str, *, slot: str | None = None) -> dict:
    layout = dict(LAYOUT_FILL)
    if slot:
        layout["slot"] = slot
    return {
        "type": "media-card",
        "assetId": asset_id,
        "layout": layout,
    }


def _row(asset_ids: list[str], row_layout: RowLayout, *, caption: str = "") -> dict:
    item: dict = {
        "type": "media-row",
        "assetIds": asset_ids,
        "rowLayout": row_layout,
    }
    if caption:
        item["caption"] = caption[:60]
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


def _is_std_landscape(k: AspectKind) -> bool:
    return k == "landscape"


def _is_std_portrait(k: AspectKind) -> bool:
    return k == "portrait"


def _can_portrait_pair(k1: AspectKind, k2: AspectKind) -> bool:
    """Web 两竖并排：标准竖版或方图；不含超长竖图。"""
    return k1 in ("portrait", "square") and k2 in ("portrait", "square")


def _mobile_card(aid: str, k: AspectKind) -> dict:
    """Mobile: one asset per row; special slots only for panorama/tall/square."""
    if k == "panorama":
        return _card(aid, slot="panorama")
    if k == "tall":
        return _card(aid, slot="tall")
    if k == "square":
        return _card(aid, slot="square")
    return _card(aid)


def plan_chapter_items(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    export_layout: ExportLayout = "auto",
) -> list[dict]:
    """
    Map asset order → media-card / media-row / media-scroll.

    Mobile: single-column media-card only (no row/scroll collage).
    Web: row packing for landscape/portrait/square groups.

    Special kinds (never forced into wrong row on web):
    - panorama → 单独宽条卡
    - square → 可 2/3 并列
    - tall → 单独竖卡（不并排）
    - landscape → web 三横 / 两横
    """
    profile = _effective_profile(export_layout)
    if profile == "mobile":
        return [_mobile_card(aid, _kind(aid, aspects)) for aid in asset_ids]

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

        if i + 2 < len(ids) and all(_is_std_portrait(o(ids[i + j])) for j in range(3)):
            items.append(_row(ids[i : i + 3], "portrait-triple"))
            i += 3
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
    items = plan_chapter_items(asset_ids, aspects, export_layout=export_layout)
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

    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_SCREENS,
        attach_screens_to_chapters,
    )

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
        from travelogue.config import default_mixed_proximity_seconds

        chapters = attach_screens_to_chapters(
            chapters,
            aspects,
            assets=assets,
            orientation_summary=summary_dict,
            day_buckets=[asset_ids],
            mixed_proximity_seconds=default_mixed_proximity_seconds(),
        )
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
) -> list[dict]:
    """Plan items per chapter bucket (Agent 1 day groups → Agent 1.5 layout)."""
    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_SCREENS,
        attach_screens_to_chapters,
    )

    default_titles = ["抵达", "途中", "片段", "尾声"]
    titles = titles or default_titles
    chapters: list[dict] = []
    non_empty = [b for b in buckets if b]
    total = len(non_empty)
    for idx, asset_ids in enumerate(non_empty, start=1):
        items = plan_chapter_items(asset_ids, aspects, export_layout=export_layout)
        pat = pattern_for_chapter_index(idx, total, items)
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
        from travelogue.config import default_mixed_proximity_seconds

        chapters = attach_screens_to_chapters(
            chapters,
            aspects,
            assets=assets,
            orientation_summary=orientation_summary,
            day_buckets=non_empty,
            mixed_proximity_seconds=default_mixed_proximity_seconds(),
        )
    return chapters


# Backward-compatible alias
orientation_for_asset = aspect_kind_for_asset
