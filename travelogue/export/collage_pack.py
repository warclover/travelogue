"""Multi-page collage export · xiaohongshu/wechat_official (3:4 Card) + album_spread (paired 3:4 Cards + gutter).

PRD-EXPORT-CARD-COMPOSE-V1 v0.3.0 / ADR-021 v0.4. All three platforms share
the CardGrouper → CardTemplateSelector → CardRenderer pipeline
(``card_grouper.py`` / ``card_renderer.py``); none require shot-grouping /
chapter-boundary awareness — only orientation-correct slot filling (§4 v0.2
simplification). ``pack_album_pages_by_chapter``'s chapter-first packing is
**retired** (BLK-ECC-05): CardGrouper's sequential slot-count consumption
replaces it, so there is no more "按章分页" special case.

``wechat_official``（公众号图文配图，2026-08-05 追加）is a **render-identical**
sibling of ``xiaohongshu`` — same 3:4 Card canvas, same page-count formula,
same CardGrouper/Selector/Renderer call path — differing only in platform
label / file-naming prefix (``-mp-{nn}`` vs ``-xhs-{nn}``) / publish_guide
copy (see ``config/platform_profiles.yaml``), since 公众号's publish flow is
"insert into 图文 editor" rather than 小红书's "选图发笔记".
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.export.card_bookends import (
    pick_portrait_preferring_id,
    render_closing_card,
    render_cover_card,
)
from travelogue.export.card_grouper import (
    CardPlan,
    count_orientation_mismatches,
    plan_cards,
    plan_cards_with_dominant_opener,
)
from travelogue.export.card_renderer import (
    ALBUM_GUTTER,
    CARD_CANVAS,
    render_card,
    render_spread,
    scale_canvas,
)
from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _slug_title,
    _trip_title,
)
from travelogue.export.photo_grid_pack import _load_trip, _resolve_asset_image_path
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import (
    file_prefix_for_platform,
    get_profile,
    resolve_album_slide_count,
    resolve_xhs_slide_count,
)
from travelogue.export.poster_bric_pack import _poster_candidate_pairs, list_poster_photo_paths

_log = logging.getLogger(__name__)

# 小红书 / 公众号仍保持较低池上限（发布场景页数不宜过多）。
_COLLAGE_PHOTO_LIMIT = 72
# 画册印刷「尽量用完精选」：单独放大到 250；导出耗时近似随照片数线性上涨，
# UI 侧需在选中画册时提示用户可能较久（见 longshot-export-panel expectHtml）。
_ALBUM_PHOTO_LIMIT = 250


def collage_photo_limit_for_platform(platform: str) -> int:
    """Per-platform kept-photo pool cap for collage exports."""
    if str(platform or "").strip() == "album_spread":
        return _ALBUM_PHOTO_LIMIT
    return _COLLAGE_PHOTO_LIMIT


def list_collage_photo_paths(
    trip_dir: Path, *, limit: int | None = None, platform: str | None = None
) -> list[Path]:
    """Kept image paths excluding collage assets (alias of list_poster_photo_paths).

    ``limit`` wins when given; otherwise ``platform`` selects the pool cap
    (album 250 / others 72).
    """
    if limit is None:
        limit = collage_photo_limit_for_platform(platform or "")
    return list_poster_photo_paths(trip_dir, limit=limit)


def _xhs_target_per_card(n_photos: int, *, slide_count: int | None, profile: Any) -> int | None:
    """Advisory ``target_per_card`` hint — **only** when the user explicitly
    picked a "自定义张数" ``slide_count``. PRD-EXPORT-CARD-COMPOSE-V1 §5.1:
    the *auto* page-count estimate formula is retired outright (no longer
    "对齐...的「切片数」公式"); auto mode must fall through to CardGrouper's
    plain greedy largest-slot-first chunking (``target_per_card=None``).
    A manual override is a distinct, still-legitimate UX affordance, honored
    as a soft hint (template library has final say on exact slot counts)."""
    if slide_count is None:
        return None
    n_target, _hint = resolve_xhs_slide_count(
        photo_count=n_photos, slide_count=slide_count, profile=profile
    )
    if n_target <= 0:
        return None
    import math

    return max(1, int(math.ceil(n_photos / n_target)))


def _album_target_per_card(n_photos: int, *, slide_count: int | None, profile: Any) -> int | None:
    """Advisory ``target_per_card`` hint for album_spread.

    ``slide_count`` counts **body spreads** (跨页). Manual values are clamped
    only; auto (``None``) uses ``resolve_album_slide_count`` (ceil to a
    multiple of 4 for print, with a small-album guard). Soft-steer contract
    matches xhs: orientation correctness still outranks exact page count.

    Small-album auto (resolved spreads ``< 4``) returns ``None`` so CardGrouper
    stays greedy — avoids forcing a sparse 4-spread book on tiny pools.
    """
    n_spreads, _hint = resolve_album_slide_count(
        photo_count=n_photos,
        slide_count=slide_count,
        profile=profile,
    )
    if n_spreads <= 0:
        return None
    if slide_count is None and n_spreads < 4:
        return None
    target_cards = max(1, n_spreads * 2)
    import math

    return max(1, int(math.ceil(n_photos / target_cards)))


def _mismatch_hint_suffix(plans: list[CardPlan]) -> str:
    """Post-hoc mismatch heads-up (2026-08-06 product decision: warn, don't
    block/pre-estimate). Appended to ``user_hint`` whenever CardGrouper's
    supply-aware selection still had to force ``n`` slots to take a
    wrong-orientation photo — always possible at the structural extremes
    (e.g. an almost-entirely-portrait pool, or a manual "自定义张数" request
    that skews the size distribution) even though it's now rare in
    practice. Empty string when ``n == 0`` (the common case)."""
    n = count_orientation_mismatches(plans)
    if n <= 0:
        return ""
    return f"；其中 {n} 处因素材横竖版比例特殊被迫裁切，如觉不理想可调整自定义张数或补充相应方向的照片"


def _pair_cards_for_spreads(
    plans: list[CardPlan],
) -> list[tuple[CardPlan, CardPlan | None]]:
    """Pair Cards two-by-two into spreads; a trailing lone Card gets a
    stand-alone half-page (OQ-ECC-02 default resolution)."""
    spreads: list[tuple[CardPlan, CardPlan | None]] = []
    for i in range(0, len(plans), 2):
        left = plans[i]
        right = plans[i + 1] if i + 1 < len(plans) else None
        spreads.append((left, right))
    return spreads


def _album_subtitle(meta: dict[str, Any]) -> str:
    """subtitle → hook → empty (PRD-ALBUM-EXPORT-BOOKENDS-V1 §3)."""
    for key in ("subtitle", "hook"):
        text = str(meta.get(key) or "").strip()
        if text:
            return text
    return ""


def _album_cover_candidate_ids(trip: dict[str, Any]) -> list[str]:
    """Portrait-leaning cover candidates for the album 3:4 canvas."""
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    ids: list[str] = []

    def _add(raw: Any) -> None:
        aid = str(raw or "").strip()
        if aid:
            ids.append(aid)

    _add(trip.get("coverAssetId"))
    by_layout = curation.get("coverByLayout")
    if isinstance(by_layout, dict):
        _add(by_layout.get("mobile"))
    orient_by = curation.get("coverOrientationByLayout")
    if isinstance(orient_by, dict):
        mobile_orient = orient_by.get("mobile")
        if isinstance(mobile_orient, dict):
            _add(mobile_orient.get("preferredCandidateId"))
    cands_by = curation.get("coverCandidatesByLayout")
    if isinstance(cands_by, dict) and isinstance(cands_by.get("mobile"), list):
        for item in cands_by["mobile"]:
            _add(item)
    else:
        for item in trip.get("coverCandidates") or []:
            _add(item)
    # Last-resort: any kept photo so a portrait substitute exists when the
    # cover candidate list is landscape-only (album 3:4 mismatch dogfood).
    displayed = curation.get("displayedAssetIds")
    if isinstance(displayed, list):
        for item in displayed:
            _add(item)
    return ids


def _album_closing_candidate_ids(
    trip: dict[str, Any], *, exclude_ids: set[str]
) -> list[str]:
    """Closing candidates: declared id first, then displayed pool end→start."""
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    ids: list[str] = []
    seen: set[str] = set()

    def _add(raw: Any) -> None:
        aid = str(raw or "").strip()
        if not aid or aid in seen or aid in exclude_ids:
            return
        seen.add(aid)
        ids.append(aid)

    _add(curation.get("closingAssetId"))
    displayed = curation.get("displayedAssetIds")
    if isinstance(displayed, list):
        for aid in reversed(displayed):
            _add(aid)
    return ids


def _try_album_bookends(
    trip_dir: Path,
    *,
    card_wh: tuple[int, int],
) -> tuple[bytes | None, bytes | None, set[str]]:
    """Render cover/closing when assets resolve; return PNG bytes + ids to
    exclude from the body pool (only successfully rendered bookends).

    Failures are swallowed (G-ABE-05) — never raise into the album body path.
    Portrait-preferring pick avoids landscape→3:4 cover-crop mismatch.
    """
    cover_bytes: bytes | None = None
    closing_bytes: bytes | None = None
    exclude_ids: set[str] = set()
    try:
        trip = _load_trip(trip_dir)
    except LongshotExportError:
        return None, None, exclude_ids
    except Exception:
        _log.exception("album bookends: trip load failed")
        return None, None, exclude_ids

    assets_by_id = {
        str(a.get("id") or ""): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and str(a.get("id") or "").strip()
    }
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    title = str(meta.get("title") or "").strip() or _trip_title(trip_dir)
    subtitle = _album_subtitle(meta)

    def _resolve(asset: dict[str, Any]):
        return _resolve_asset_image_path(asset, trip_dir)

    cover_primary = str(trip.get("coverAssetId") or "").strip()
    if cover_primary:
        cover_id = pick_portrait_preferring_id(
            cover_primary,
            _album_cover_candidate_ids(trip),
            assets_by_id=assets_by_id,
            resolve_path=_resolve,
        )
        asset = assets_by_id.get(cover_id)
        path = _resolve(asset) if asset else None
        if path is not None and path.is_file():
            cover_bytes = render_cover_card(
                path,
                title=title,
                subtitle=subtitle,
                canvas_wh=card_wh,
                asset=asset,
            )
            if cover_bytes:
                exclude_ids.add(cover_id)

    closing_primary = ""
    curation = trip.get("curation")
    if isinstance(curation, dict):
        closing_primary = str(curation.get("closingAssetId") or "").strip()
    if closing_primary:
        closing_id = pick_portrait_preferring_id(
            closing_primary,
            _album_closing_candidate_ids(trip, exclude_ids=set(exclude_ids)),
            assets_by_id=assets_by_id,
            resolve_path=_resolve,
        )
        asset = assets_by_id.get(closing_id)
        path = _resolve(asset) if asset else None
        if path is not None and path.is_file():
            closing_bytes = render_closing_card(
                path, title=title, canvas_wh=card_wh, asset=asset
            )
            if closing_bytes:
                exclude_ids.add(closing_id)

    return cover_bytes, closing_bytes, exclude_ids


def _album_bookends_hint(
    *,
    page_count: int,
    has_cover: bool,
    has_closing: bool,
) -> str:
    parts: list[str] = []
    if has_cover:
        parts.append("封面 1 张")
    parts.append("正文跨页拼贴")
    if has_closing:
        parts.append("封底 1 张")
    detail = " + ".join(parts)
    return f"已生成 {page_count} 张画册页面（含{detail}）"


def export_collage_pack(
    trip_dir: Path,
    *,
    platform: str,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    slide_count: int | None = None,
    cfg: Any | None = None,
) -> LongshotExportResult:
    """Compose multi-page 3:4 Card collages (no Playwright / gcs flag)."""
    _ = cfg
    pid = str(platform or "").strip()
    if pid not in ("xiaohongshu", "wechat_official", "album_spread"):
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            f"collage_pack 仅支持 xiaohongshu / wechat_official / album_spread，收到「{pid}」",
        )

    trip_dir = Path(trip_dir).resolve()
    profile = get_profile(pid)
    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, pid)
    _ = fmt  # collage pages always PNG
    out_ext = "png"

    pairs = _poster_candidate_pairs(
        trip_dir, limit=collage_photo_limit_for_platform(pid)
    )
    paths = [path for path, _ in pairs]
    if not paths:
        raise LongshotExportError(
            "E_COLLAGE_N",
            "没有可导出的精选照片，请先完成策展",
        )
    # AC-ECC-06 · 与 poster_bric_pack 同源注入资产元数据，启用人物保守焦点。
    asset_lookup = dict(pairs).get

    card_wh = scale_canvas(CARD_CANVAS, scale)

    if pid in ("xiaohongshu", "wechat_official"):
        target_per_card = _xhs_target_per_card(
            len(paths), slide_count=slide_count, profile=profile
        )
        plans = plan_cards_with_dominant_opener(paths, target_per_card=target_per_card)
        pages_render = [
            render_card(
                list(plan.photos),
                plan.template,
                canvas_wh=card_wh,
                asset_lookup=asset_lookup,
            )[0]
            for plan in plans
        ]
        # 渲染管线与小红书完全一致；仅正文场景措辞不同（笔记 vs 图文）。
        body_label = "图文正文" if pid == "wechat_official" else "笔记正文"
        user_hint = (
            f"已生成 {len(pages_render)} 张竖版拼贴卡片（3:4）· 更多细节可写在{body_label}"
        )
        user_hint += _mismatch_hint_suffix(plans)
        segment_reason = "collage_pages"
    else:
        # PRD-ALBUM-EXPORT-BOOKENDS-V1 · cover/closing are album-only add-ons.
        # Exclude only successfully rendered bookend asset ids from the body
        # pool (D-ABE-03/05); shared upstream ``pairs`` stay untouched for
        # xhs/mp (G-ABE-04).
        cover_bytes, closing_bytes, exclude_ids = _try_album_bookends(
            trip_dir, card_wh=card_wh
        )
        body_pairs = [
            (p, a)
            for p, a in pairs
            if str(a.get("id") or "") not in exclude_ids
        ]
        body_paths = [p for p, _ in body_pairs]
        if not body_paths and not cover_bytes and not closing_bytes:
            raise LongshotExportError(
                "E_COLLAGE_N",
                "没有可导出的精选照片，请先完成策展",
            )

        body_pages: list[bytes] = []
        plans: list[CardPlan] = []
        if body_paths:
            album_target_per_card = _album_target_per_card(
                len(body_paths), slide_count=slide_count, profile=profile
            )
            plans = plan_cards(
                body_paths,
                target_per_card=album_target_per_card,
                avoid_immediate_repeat=True,
            )
            spreads = _pair_cards_for_spreads(plans)
            gutter = (
                int(round(ALBUM_GUTTER * 1.25))
                if int(scale or 2) > 2
                else ALBUM_GUTTER
            )
            for left, right in spreads:
                right_arg = (list(right.photos), right.template) if right else None
                data, _diag = render_spread(
                    (list(left.photos), left.template),
                    right_arg,
                    card_wh=card_wh,
                    gutter=gutter,
                    asset_lookup=asset_lookup,
                )
                body_pages.append(data)

        pages_render = (
            ([cover_bytes] if cover_bytes else [])
            + body_pages
            + ([closing_bytes] if closing_bytes else [])
        )
        user_hint = _album_bookends_hint(
            page_count=len(pages_render),
            has_cover=bool(cover_bytes),
            has_closing=bool(closing_bytes),
        )
        if plans:
            user_hint += _mismatch_hint_suffix(plans)
        segment_reason = "collage_pages"

    writer = PlatformExportWriter(
        trip_dir / EXPORT_OUTPUT_DIRNAME, prefix, ext=out_ext, single_file=False
    )
    outputs: list[LongshotOutput] = []
    total = len(pages_render)

    try:
        with writer:
            for i, data in enumerate(pages_render, start=1):
                if progress:
                    progress(i - 1, total, f"拼贴页 {i}/{total}")
                writer.write(i, data)
            finals = writer.commit()
        for path in finals:
            outputs.append(
                LongshotOutput(path=path, capture_method="collage_pages")
            )
        if progress:
            progress(total, total, "拼贴导出完成")
    except LongshotExportError:
        writer.rollback()
        raise
    except Exception as exc:
        writer.rollback()
        _log.exception("collage_pack export failed (%s)", pid)
        raise LongshotExportError(
            "E_COLLAGE_FAILED",
            f"拼贴导出失败: {exc}",
        ) from exc

    guide = (profile.publish_guide or "").strip()
    return LongshotExportResult(
        outputs=outputs,
        capture_method="collage_pages",
        title=_slug_title(title),
        segmented=len(outputs) > 1,
        segment_reason=segment_reason,
        user_hint=user_hint,
        platform=pid,
        profile_label=profile.label,
        target_page_count=len(outputs),
        publish_guide=guide,
        page_count=len(outputs),
        output_format="png",
    )
