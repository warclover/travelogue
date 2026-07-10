"""Homepage v2 · user trip Bento preview payload (PRD v2.0.5 · 方案 B′)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import quote

from PIL import Image

from travelogue.render.context import asset_aspect_kind, pick_image_src
from travelogue.render.cover_closing import resolve_closing_asset_id


def _trip_static_url(trip_id: str, rel: str | Path) -> str:
    """Public URL for a file under trip root (encode non-ASCII path segments)."""
    rel_posix = Path(rel).as_posix().lstrip("/")
    if not rel_posix:
        return f"/{trip_id}"
    encoded = "/".join(quote(seg, safe="") for seg in rel_posix.split("/"))
    return f"/{trip_id}/{encoded}"

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
# 与 image_ops.SQUARE_THRESHOLD 一致：w/h ≥ 1.08 视为横图，可用于 16:9 Web 轮播
_WEB_LANDSCAPE_RATIO_MIN = 1.08


def _image_pixel_size(path: Path) -> tuple[int, int] | None:
    """读取 PNG/JPEG 像素尺寸；PNG 走轻量头读取，其它格式回退 PIL。"""
    try:
        suffix = path.suffix.lower()
        if suffix == ".png":
            with path.open("rb") as fh:
                header = fh.read(24)
            if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
                return None
            width = int.from_bytes(header[16:20], "big")
            height = int.from_bytes(header[20:24], "big")
            if width <= 0 or height <= 0:
                return None
            return width, height
        with Image.open(path) as img:
            width, height = img.size
            if width <= 0 or height <= 0:
                return None
            return width, height
    except OSError:
        return None


def _file_width_height_ratio(path: Path) -> float | None:
    size = _image_pixel_size(path)
    if not size:
        return None
    width, height = size
    return width / height


def _is_web_landscape_file(path: Path) -> bool:
    """Web 轮播可用：横版 PNG（排除 *-ch*.png 手机长条切图）。"""
    ratio = _file_width_height_ratio(path)
    if ratio is None:
        return False
    return ratio >= _WEB_LANDSCAPE_RATIO_MIN


def _is_web_landscape_asset(asset: dict, trip_dir: Path) -> bool:
    """Web 16:9 轮播仅接受横版资产（w/h ≥ 1.08）。"""
    if not _is_image_asset(asset):
        return False
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    if w > 0 and h > 0:
        return (w / h) >= _WEB_LANDSCAPE_RATIO_MIN
    rel = pick_image_src(asset)
    if rel:
        ratio = _file_width_height_ratio(trip_dir / rel)
        if ratio is not None:
            return ratio >= _WEB_LANDSCAPE_RATIO_MIN
    kind = asset_aspect_kind(asset)
    return kind in ("landscape", "panorama")


def _is_phone_vertical_file(path: Path) -> bool:
    """手机长图可用：竖条 PNG（如 export 章节切图）。"""
    ratio = _file_width_height_ratio(path)
    if ratio is None:
        return False
    return ratio < _WEB_LANDSCAPE_RATIO_MIN


def _pick_longshot(trip_dir: Path) -> Path | None:
    rows = sorted(
        list(trip_dir.glob("*-longshot.png"))
        + list(trip_dir.glob("*-longshot.jpg"))
        + list(trip_dir.glob("*-longshot.jpeg"))
    )
    return rows[0] if rows else None


def _chapter_pngs(trip_dir: Path) -> list[Path]:
    return sorted(
        list(trip_dir.glob("*-ch*.png"))
        + list(trip_dir.glob("*-ch*.jpg"))
        + list(trip_dir.glob("*-ch*.jpeg")),
        key=lambda p: p.name.lower(),
    )


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


# Homepage Bento 缩略预览：优先中档 WebP，避免一次解码多张 w3200 把浏览器打爆。
_BENTO_WIDTH_PREFERENCE: tuple[str, ...] = ("w1600", "w800", "w2400", "w3200")


def _bento_display_rel(trip_dir: Path, asset: dict) -> str | None:
    """Pick a mid-size on-disk variant for homepage preview (prefer w1600)."""
    rel = pick_image_src(asset)
    if not rel:
        return None
    rel_posix = Path(rel).as_posix()
    if (trip_dir / rel_posix).is_file():
        # displayFile 常为 *-w3200.webp；同 stem 若有更小档则改用。
        for width_key in _BENTO_WIDTH_PREFERENCE:
            candidate = _swap_webp_width(rel_posix, width_key)
            if candidate and (trip_dir / candidate).is_file():
                return candidate
        return rel_posix
    paths = asset.get("paths")
    if isinstance(paths, dict):
        for width_key in _BENTO_WIDTH_PREFERENCE:
            candidate = paths.get(width_key)
            if candidate and (trip_dir / candidate).is_file():
                return str(candidate).replace("\\", "/")
    return None


def _swap_webp_width(rel: str, width_key: str) -> str | None:
    """assets/foo-w3200.webp → assets/foo-w1600.webp（仅匹配已知档位后缀）。"""
    m = re.search(r"^(.*)-w(800|1600|2400|3200)(\.webp)$", rel, flags=re.IGNORECASE)
    if not m:
        return None
    return f"{m.group(1)}-{width_key}{m.group(3)}"


def _asset_public_url(trip_id: str, trip_dir: Path, asset: dict) -> str | None:
    rel = _bento_display_rel(trip_dir, asset)
    if not rel:
        return None
    return _trip_static_url(trip_id, rel)


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
    landscape_only: bool = False,
) -> str | None:
    assets = _asset_map(trip)
    best_url: str | None = None
    best_score: tuple[int, float] | None = None
    for aid in asset_ids:
        asset = assets.get(str(aid))
        if not _is_image_asset(asset) or not asset.get("layoutEligible", True):
            continue
        if landscape_only and not _is_web_landscape_asset(asset, trip_dir):
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
    if cover_id:
        asset = assets.get(str(cover_id))
        if _is_image_asset(asset) and _is_web_landscape_asset(asset, trip_dir):
            direct = _asset_public_url(trip_id, trip_dir, asset)
            if direct:
                return direct
    # 无显式横版封面资产时，从全部资产里挑最佳横图。
    # 注意：preview.jpg 是竖版封面卡（下半为深色标题栏），若直接用作 16:9 轮播首页
    # 会在框内露出深色标题带（“黑块”）。故仅当整本没有任何横图时才回退 preview.jpg。
    url = _best_asset_url(
        trip,
        trip_id,
        trip_dir,
        _eligible_asset_ids(trip),
        kind_scores=_WEB_KIND_SCORE,
        target_ratio=_TARGET_WEB_RATIO,
        landscape_only=True,
    )
    return url or fallback


def _chapter_carousel_asset_id(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    chapter: dict,
    index: int,
    ch_pngs: list[Path],
) -> str | None:
    """Web carousel 章页对应的 trip 资产 id；横版 *-ch*.png 章页无资产 id。"""
    if index <= len(ch_pngs):
        png = ch_pngs[index - 1]
        if _is_web_landscape_file(png):
            return None
    if not chapter:
        return None
    assets = _asset_map(trip)
    best_id: str | None = None
    best_score: tuple[int, float] | None = None
    for aid in _iter_chapter_asset_ids(chapter):
        asset = assets.get(str(aid))
        if not _is_image_asset(asset) or not asset.get("layoutEligible", True):
            continue
        if not _is_web_landscape_asset(asset, trip_dir):
            continue
        score = _asset_fit_score(
            asset,
            kind_scores=_WEB_KIND_SCORE,
            target_ratio=_TARGET_WEB_RATIO,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_id = str(aid)
    return best_id


def _epilogue_asset_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    *,
    exclude_asset_ids: set[str],
    avoid_urls: set[str],
    fallback: str,
    prefer_landscape: bool,
) -> str:
    """尾声图：与正式 closing 同源，且不与 carousel 章页（尤其最后一章）重复。"""
    assets = _asset_map(trip)
    closing_id = resolve_closing_asset_id(
        trip,
        assets,
        prefer_landscape=prefer_landscape,
        exclude_ids=exclude_asset_ids,
    )
    if closing_id:
        asset = assets.get(closing_id)
        if asset and (not prefer_landscape or _is_web_landscape_asset(asset, trip_dir)):
            url = _asset_public_url(trip_id, trip_dir, asset)
            if url and url not in avoid_urls:
                return url

    for aid in reversed(_eligible_asset_ids(trip)):
        if aid in exclude_asset_ids:
            continue
        asset = assets.get(aid)
        if not asset:
            continue
        if prefer_landscape and not _is_web_landscape_asset(asset, trip_dir):
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if url and url not in avoid_urls:
            return url

    if fallback not in avoid_urls:
        return fallback
    return fallback


def _best_chapter_portrait_url(
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
        kind_scores=_PHONE_KIND_SCORE,
        target_ratio=_TARGET_PHONE_RATIO,
    )
    return url or fallback


def _best_cover_portrait_url(
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
        kind_scores=_PHONE_KIND_SCORE,
        target_ratio=_TARGET_PHONE_RATIO,
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


def _portrait_url_for_carousel_page(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    page: dict[str, Any],
    chapters: list[dict],
    *,
    cover_url: str,
    preview_url: str,
    epilogue_exclude_asset_ids: set[str] | None = None,
    epilogue_avoid_urls: set[str] | None = None,
) -> str:
    role = page.get("role")
    if role == "cover":
        # 手机框封面优先 trip preview（9:16），与章内竖图区分
        return preview_url or _best_cover_portrait_url(
            trip, trip_id, trip_dir, fallback=cover_url
        )
    if role == "chapter":
        idx = int(page.get("chapterIndex") or 0)
        if idx > 0 and idx <= len(chapters):
            return _best_chapter_portrait_url(
                trip, trip_id, trip_dir, chapters[idx - 1], fallback=cover_url
            )
    if role == "epilogue":
        return _epilogue_asset_url(
            trip,
            trip_id,
            trip_dir,
            exclude_asset_ids=epilogue_exclude_asset_ids or set(),
            avoid_urls=epilogue_avoid_urls or set(),
            fallback=cover_url,
            prefer_landscape=False,
        )
    return str(page.get("url") or cover_url)


def _longshot_pages_from_carousel(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    carousel_pages: list[dict[str, Any]],
    chapters: list[dict],
    *,
    cover_url: str,
    preview_url: str,
    epilogue_exclude_asset_ids: set[str] | None = None,
    epilogue_avoid_urls: set[str] | None = None,
) -> list[dict[str, Any]]:
    """与 Web carousel 同序 · 每页选竖版原图（无导出长图时的 fallback）。"""
    pages: list[dict[str, Any]] = []
    for page in carousel_pages:
        entry: dict[str, Any] = {
            "id": str(page.get("id") or "longshot"),
            "label": str(page.get("label") or "微信长图"),
            "url": _portrait_url_for_carousel_page(
                trip,
                trip_id,
                trip_dir,
                page,
                chapters,
                cover_url=cover_url,
                preview_url=preview_url,
                epilogue_exclude_asset_ids=epilogue_exclude_asset_ids,
                epilogue_avoid_urls=epilogue_avoid_urls,
            ),
            "scrollPreview": True,
        }
        if page.get("chapterIndex") is not None:
            entry["chapterIndex"] = page["chapterIndex"]
        pages.append(entry)
    return pages


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


def _build_longshot_pages(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    chapters: list[dict],
    ch_pngs: list[Path],
    carousel_pages: list[dict[str, Any]],
    *,
    cover_url: str,
    preview_url: str,
    epilogue_exclude_asset_ids: set[str] | None = None,
    epilogue_avoid_urls: set[str] | None = None,
) -> list[dict[str, Any]]:
    """手机框切换序列：整卷 longshot → 竖条 *-ch*.png → 按 carousel 章序竖版原图。"""
    longshot = _pick_longshot(trip_dir)
    if longshot:
        return [
            {
                "id": "longshot",
                "label": "微信长图",
                "url": _trip_static_url(trip_id, longshot.name),
                "scrollPreview": True,
            }
        ]

    vertical_strips = [png for png in ch_pngs if _is_phone_vertical_file(png)]
    if vertical_strips:
        pages: list[dict[str, Any]] = []
        for i, png in enumerate(vertical_strips, 1):
            ch = chapters[i - 1] if i - 1 < len(chapters) else {}
            pages.append(
                {
                    "id": str(ch.get("id") or f"ch{i:02d}"),
                    "label": _chapter_label(ch, i) if ch else f"第{i}章",
                    "chapterIndex": i,
                    "url": _trip_static_url(trip_id, png.name),
                    "scrollPreview": True,
                }
            )
        return pages

    if carousel_pages and chapters:
        derived = _longshot_pages_from_carousel(
            trip,
            trip_id,
            trip_dir,
            carousel_pages,
            chapters,
            cover_url=cover_url,
            preview_url=preview_url,
            epilogue_exclude_asset_ids=epilogue_exclude_asset_ids,
            epilogue_avoid_urls=epilogue_avoid_urls,
        )
        if derived:
            chapter_pages = [p for p in derived if p.get("chapterIndex")]
            if chapter_pages:
                return chapter_pages
            return derived

    fallback = _best_longshot_url(trip, trip_id, trip_dir, fallback=preview_url)
    return [{"id": "longshot", "label": "微信长图", "url": fallback, "scrollPreview": True}]


def _ranked_chapter_asset_urls(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    chapter: dict,
    *,
    used_urls: set[str],
) -> list[str]:
    """章内候选 URL（仅横版），排除 carousel 已用 URL。"""
    assets = _asset_map(trip)
    ranked: list[tuple[tuple[int, float], str]] = []
    seen: set[str] = set()
    for aid in _iter_chapter_asset_ids(chapter):
        asset = assets.get(str(aid))
        if not _is_image_asset(asset) or not asset.get("layoutEligible", True):
            continue
        if not _is_web_landscape_asset(asset, trip_dir):
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if not url or url in used_urls or url in seen:
            continue
        seen.add(url)
        score = _asset_fit_score(
            asset,
            kind_scores=_WEB_KIND_SCORE,
            target_ratio=_TARGET_WEB_RATIO,
        )
        ranked.append((score, url))
    ranked.sort(reverse=True)
    return [url for _, url in ranked]


def _first_unused_landscape_asset_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    *,
    used_urls: set[str],
) -> str | None:
    assets = _asset_map(trip)
    for aid in _eligible_asset_ids(trip):
        asset = assets.get(aid)
        if not asset or not _is_web_landscape_asset(asset, trip_dir):
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if url and url not in used_urls:
            return url
    return None


def _any_landscape_asset_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
) -> str | None:
    """整本第一张横图（忽略去重）。用于横图耗尽时的兜底，
    避免竖版 preview.jpg（封面卡）进入 16:9 轮播产生黑块。"""
    assets = _asset_map(trip)
    for aid in _eligible_asset_ids(trip):
        asset = assets.get(aid)
        if not asset or not _is_web_landscape_asset(asset, trip_dir):
            continue
        url = _asset_public_url(trip_id, trip_dir, asset)
        if url:
            return url
    return None


def _chapter_page_url(
    trip: dict,
    trip_id: str,
    trip_dir: Path,
    chapter: dict,
    index: int,
    ch_pngs: list[Path],
    *,
    used_urls: set[str],
    fallback: str,
) -> str:
    """章节轮播 URL：横版 *-ch*.png 优先；不与封面/前章重复。"""
    if index <= len(ch_pngs):
        png = ch_pngs[index - 1]
        if _is_web_landscape_file(png):
            url = _trip_static_url(trip_id, png.name)
            if url not in used_urls:
                return url

    for url in _ranked_chapter_asset_urls(
        trip, trip_id, trip_dir, chapter, used_urls=used_urls
    ):
        return url

    spare = _first_unused_landscape_asset_url(trip, trip_id, trip_dir, used_urls=used_urls)
    if spare:
        return spare
    # 横图已耗尽：宁可复用一张横图，也不让竖版 preview.jpg 进轮播（会露深色标题带）。
    reuse = _any_landscape_asset_url(trip, trip_id, trip_dir)
    if reuse:
        return reuse
    return fallback


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
    used_carousel_urls: set[str] = {cover_url}
    chapter_carousel_asset_ids: set[str] = set()
    if chapters:
        for i, ch in enumerate(chapters, 1):
            chapter_url = _chapter_page_url(
                trip,
                trip_id,
                trip_dir,
                ch,
                i,
                ch_pngs,
                used_urls=used_carousel_urls,
                fallback=preview_url,
            )
            used_carousel_urls.add(chapter_url)
            carousel_asset_id = _chapter_carousel_asset_id(trip, trip_id, trip_dir, ch, i, ch_pngs)
            if carousel_asset_id:
                chapter_carousel_asset_ids.add(carousel_asset_id)
            pages.append(
                {
                    "id": str(ch.get("id") or f"ch{i:02d}"),
                    "role": "chapter",
                    "label": _chapter_label(ch, i),
                    "chapterIndex": i,
                    "url": chapter_url,
                }
            )
    elif ch_pngs:
        for i, png in enumerate(ch_pngs, 1):
            png_url = _trip_static_url(trip_id, png.name)
            if _is_web_landscape_file(png) and png_url not in used_carousel_urls:
                url = png_url
            else:
                url = (
                    _first_unused_landscape_asset_url(
                        trip, trip_id, trip_dir, used_urls=used_carousel_urls
                    )
                    or _any_landscape_asset_url(trip, trip_id, trip_dir)
                    or (
                        preview_url
                        if preview_url not in used_carousel_urls
                        else cover_url
                    )
                )
            used_carousel_urls.add(url)
            pages.append(
                {
                    "id": f"ch{i:02d}",
                    "role": "chapter",
                    "label": f"第{i}章",
                    "chapterIndex": i,
                    "url": url,
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

    epilogue_url = _epilogue_asset_url(
        trip,
        trip_id,
        trip_dir,
        exclude_asset_ids=chapter_carousel_asset_ids,
        avoid_urls=used_carousel_urls,
        fallback=cover_url,
        prefer_landscape=True,
    )
    if epilogue_url in used_carousel_urls:
        # 与已用页重复时，优先换一张未用横图；没有则保留横图（宁可重复也不上竖版封面卡）。
        spare_epilogue = _first_unused_landscape_asset_url(
            trip, trip_id, trip_dir, used_urls=used_carousel_urls
        )
        if spare_epilogue:
            epilogue_url = spare_epilogue
    pages.append(
        {"id": "epilogue", "role": "epilogue", "label": "尾声", "url": epilogue_url},
    )

    longshot_pages = _build_longshot_pages(
        trip,
        trip_id,
        trip_dir,
        chapters,
        ch_pngs,
        pages,
        cover_url=cover_url,
        preview_url=preview_url,
        epilogue_exclude_asset_ids=chapter_carousel_asset_ids,
        epilogue_avoid_urls=used_carousel_urls,
    )
    longshot_url = longshot_pages[0]["url"] if longshot_pages else preview_url

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
        "longshotPages": longshot_pages,
        "pages": pages,
    }
