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
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _slug_title,
    _trip_title,
)
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import (
    file_prefix_for_platform,
    get_profile,
    resolve_aspect_slide_count,
    resolve_xhs_slide_count,
)
from travelogue.export.poster_bric_pack import _poster_candidate_pairs, list_poster_photo_paths

_log = logging.getLogger(__name__)

_COLLAGE_PHOTO_LIMIT = 72


def list_collage_photo_paths(trip_dir: Path, *, limit: int = _COLLAGE_PHOTO_LIMIT) -> list[Path]:
    """Kept image paths excluding collage assets (alias of list_poster_photo_paths)."""
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
    """Advisory ``target_per_card`` hint for album_spread, derived from the
    user's manual "跨页数" (spread count) request — mirrors
    ``_xhs_target_per_card``'s "auto stays greedy, manual overrides steer
    chunking" contract (§5.1). ``slide_count`` here counts **spreads**
    (the platform's own output unit), so it's clamped against
    ``album_spread``'s own profile bounds first; the target Card count is
    then ~2x the clamped spread count (one spread = two Cards, plus a
    possible trailing lone half-page — §3.1)."""
    if slide_count is None:
        return None
    n_spreads, _hint = resolve_aspect_slide_count(
        photo_count=n_photos,
        slide_count=slide_count,
        profile=profile,
        hint_kind="album",
    )
    if n_spreads <= 0:
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

    pairs = _poster_candidate_pairs(trip_dir, limit=_COLLAGE_PHOTO_LIMIT)
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
        album_target_per_card = _album_target_per_card(
            len(paths), slide_count=slide_count, profile=profile
        )
        plans = plan_cards(
            paths, target_per_card=album_target_per_card, avoid_immediate_repeat=True
        )
        spreads = _pair_cards_for_spreads(plans)
        gutter = (
            int(round(ALBUM_GUTTER * 1.25)) if int(scale or 2) > 2 else ALBUM_GUTTER
        )
        pages_render = []
        for left, right in spreads:
            right_arg = (list(right.photos), right.template) if right else None
            data, _diag = render_spread(
                (list(left.photos), left.template),
                right_arg,
                card_wh=card_wh,
                gutter=gutter,
                asset_lookup=asset_lookup,
            )
            pages_render.append(data)
        user_hint = f"已生成 {len(pages_render)} 张画册跨页拼贴（两张 3:4 + 中缝）"
        user_hint += _mismatch_hint_suffix(plans)
        segment_reason = "collage_pages"

    writer = PlatformExportWriter(trip_dir, prefix, ext=out_ext, single_file=False)
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
