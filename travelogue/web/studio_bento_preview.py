"""Homepage v2 · user trip Bento preview payload (PRD v2.0.5 · 方案 B′)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from travelogue.render.context import asset_aspect_kind, pick_image_src

# Web 16:9 carousel · 优先横图
_WEB_KIND_SCORE: dict[str, int] = {
    "panorama": 5,
    "landscape": 4,
    "square": 2,
    "portrait": 1,
    "tall": 0,
}
_TARGET_WEB_RATIO = 16 / 9

# 手机 9:16 · 优先竖图
_PHONE_KIND_SCORE: dict[str, int] = {
    "tall": 5,
    "portrait": 4,
    "square": 2,
    "landscape": 1,
    "panorama": 0,
}
_TARGET_PHONE_RATIO = 9 / 16

_KIND_RATIO_HINT: dict[str, float] = {
    "panorama": 2.0,
    "landscape": _TARGET_WEB_RATIO,
    "square": 1.0,
    "portrait": _TARGET_PHONE_RATIO,
    "tall": 0.4,
}


def _pick_longshot(trip_dir: Path) -> Path | None:
    rows = sorted(trip_dir.glob("*-longshot.png"))
    return rows[0] if rows else None


def _chapter_pngs(trip_dir: Path) -> list[Path]:
    return sorted(trip_dir.glob("*-ch*.png"), key=lambda p: p.name.lower())


def _asset_map(trip: dict) -> dict[str, dict]:
    return {str(a["id"]): a for a in trip.get("assets") or [] if a.get("id")}


def _is_image_asset(asset: dict | None) -> bool:
    return bool(asset) and asset.get("type", "image") == "image"


def _iter_chapter_asset_ids(chapter: dict) -> Iterator[str]:
    for screen in chapter.get("screens") or []:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if aid:
                yield str(aid)
    for item in chapter.get("items") or []:
        itype = item.get("type") or ""
        if itype == "media-card":
            aid = item.get("assetId")
            if aid:
                yield str(aid)
        elif itype in ("media-row", "media-scroll"):
            for aid in item.get("assetIds") or []:
                if aid:
                    yield str(aid)


def _asset_public_url(trip_id: str, trip_dir: Path, asset: dict) -> str | None:
    rel = pick_image_src(asset)
    if not rel:
        return None
    if not (trip_dir / rel).is_file():
        return None
    return f"/{trip_id}/{Path(rel).as_posix()}"


def _asset_width_height_ratio(asset: dict) -> float:
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    if w > 0 and h > 0:
        return w / h
    return _KIND_RATIO_HINT.get(asset_aspect_kind(asset), 1.0)


def _asset_fit_score(
    asset: dict,
    *,
    kind_scores: dict[str, int],
    target_ratio: float,
) -> tuple[int, float]:
    kind = asset_aspect_kind(asset)
    kind_score = kind_scores.get(kind, 0)
    ratio = _asset_width_height_ratio(asset)
    ratio_closeness = -abs(ratio - target_ratio)
    return kind_score, ratio_closeness


def _best_asset_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    asset_ids: Iterator[str] | list[str],
    *,
    kind_scores: dict[str, int],
    target_ratio: float,
) -> str | None:
    assets = _asset_map(trip)
    best_url: str | None = None
    best_score: tuple[int, float] | None = None
    for aid in asset_ids:
        asset = assets.get(str(aid))
        if not _is_image_asset(asset) or not asset.get("layoutEligible", True):
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if not url:
            continue
        score = _asset_fit_score(asset, kind_scores=kind_scores, target_ratio=target_ratio)
        if best_score is None or score > best_score:
            best_score = score
            best_url = url
    return best_url


def _eligible_asset_ids(trip: dict) -> list[str]:
    return [
        str(a["id"])
        for a in trip.get("assets") or []
        if a.get("id") and _is_image_asset(a) and a.get("layoutEligible", True)
    ]


def _best_chapter_image_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    chapter: dict,
    *,
    fallback: str,
) -> str:
    url = _best_asset_url(
        trip,
        trip_id,
        trip_dir,
        _iter_chapter_asset_ids(chapter),
        kind_scores=_WEB_KIND_SCORE,
        target_ratio=_TARGET_WEB_RATIO,
    )
    return url or fallback


def _best_cover_image_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    *,
    fallback: str,
) -> str:
    assets = _asset_map(trip)
    cover_id = trip.get("coverAssetId")
    ordered_ids: list[str] = []
    if cover_id:
        ordered_ids.append(str(cover_id))
    for aid in _eligible_asset_ids(trip):
        if aid not in ordered_ids:
            ordered_ids.append(aid)
    url = _best_asset_url(
        trip,
        trip_id,
        trip_dir,
        ordered_ids,
        kind_scores=_WEB_KIND_SCORE,
        target_ratio=_TARGET_WEB_RATIO,
    )
    if url:
        return url
    if cover_id:
        asset = assets.get(str(cover_id))
        if _is_image_asset(asset):
            direct = _asset_public_url(trip_id, trip_dir, asset)
            if direct:
                return direct
    return fallback


def _best_epilogue_image_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    *,
    fallback: str,
) -> str:
    chapters = trip.get("chapters") or []
    for chapter in reversed(chapters):
        url = _best_asset_url(
            trip,
            trip_id,
            trip_dir,
            _iter_chapter_asset_ids(chapter),
            kind_scores=_WEB_KIND_SCORE,
            target_ratio=_TARGET_WEB_RATIO,
        )
        if url:
            return url
    assets = _asset_map(trip)
    for aid in reversed(_eligible_asset_ids(trip)):
        asset = assets.get(aid)
        if not asset:
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if url:
            return url
    return fallback


def _best_longshot_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    *,
    fallback: str,
) -> str:
    url = _best_asset_url(
        trip,
        trip_id,
        trip_dir,
        _eligible_asset_ids(trip),
        kind_scores=_PHONE_KIND_SCORE,
        target_ratio=_TARGET_PHONE_RATIO,
    )
    return url or fallback


def _chapter_label(chapter: dict, index: int) -> str:
    return str(chapter.get("title") or f"第{index}章").strip()[:20] or f"第{index}章"


def build_trip_bento_preview(trip_dir: Path, trip: dict, trip_id: str) -> dict[str, Any] | None:
    """Manifest-like payload for Bento「我的最近一本」Tab. None if no preview.jpg."""
    preview_jpg = trip_dir / "preview.jpg"
    if not preview_jpg.is_file():
        return None

    meta = trip.get("meta") or {}
    intent = trip.get("intent") or {}
    title = str(intent.get("title") or meta.get("title") or trip_id).strip()[:20] or trip_id
    chapters = trip.get("chapters") or []
    photo_count = sum(
        1 for a in trip.get("assets") or [] if a.get("type", "image") == "image"
    )

    preview_url = f"/{trip_id}/preview.jpg"
    cover_url = _best_cover_image_url(trip, trip_id, trip_dir, fallback=preview_url)
    pages: list[dict[str, Any]] = [
        {"id": "cover", "role": "cover", "label": "封面", "url": cover_url},
    ]

    ch_pngs = _chapter_pngs(trip_dir)
    if ch_pngs:
        for i, png in enumerate(ch_pngs, 1):
            ch = chapters[i - 1] if i - 1 < len(chapters) else {}
            pages.append(
                {
                    "id": str(ch.get("id") or f"ch{i:02d}"),
                    "role": "chapter",
                    "label": _chapter_label(ch, i),
                    "chapterIndex": i,
                    "url": f"/{trip_id}/{png.name}",
                }
            )
    elif chapters:
        for i, ch in enumerate(chapters, 1):
            pages.append(
                {
                    "id": str(ch.get("id") or f"ch{i:02d}"),
                    "role": "chapter",
                    "label": _chapter_label(ch, i),
                    "chapterIndex": i,
                    "url": _best_chapter_image_url(
                        trip, trip_id, trip_dir, ch, fallback=cover_url
                    ),
                }
            )
    else:
        pages.append(
            {
                "id": "ch01",
                "role": "chapter",
                "label": "正文",
                "chapterIndex": 1,
                "url": cover_url,
            }
        )

    epilogue_url = _best_epilogue_image_url(trip, trip_id, trip_dir, fallback=cover_url)
    pages.append(
        {"id": "epilogue", "role": "epilogue", "label": "尾声", "url": epilogue_url},
    )

    longshot = _pick_longshot(trip_dir)
    if longshot:
        longshot_url = f"/{trip_id}/{longshot.name}"
    else:
        longshot_url = _best_longshot_url(trip, trip_id, trip_dir, fallback=preview_url)

    return {
        "version": "1",
        "source": "user",
        "tripId": trip_id,
        "title": title,
        "previewUrl": f"/{trip_id}/index.html",
        "meta": {
            "photoCount": photo_count,
            "chapterCount": len(chapters) or len(ch_pngs),
        },
        "assets": {
            "background": cover_url,
            "longshot": longshot_url,
        },
        "pages": pages,
    }
