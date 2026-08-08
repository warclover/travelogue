"""Title Art orchestrator (PRD §5/§6/§8 · main entrypoint).

编排：§4 文案合同 → §5.4 白名单门槛 → §5.3 字形覆盖 → 定位/配色（§6）→
（可选）路线 C 尝试 → 门槛不过分层 fallback 路线 B（D-CAL-16）→ 写入
``trip.meta.titleArt``（§8）。

调用方通过依赖注入负责：
- ``resolve_asset_path``：给定 asset dict，解析可读的原图文件路径（用于
  §6.2 定位打分的取景照片）；解析失败/无封面 → 退回默认定位，不阻断。
- ``write_png``：接收最终 PNG bytes，落盘并返回相对 ``assetPath``
  （trip 根目录相对路径，写入 §8 ``titleArt.assetPath``）。

引擎本身不做任何文件 I/O，保持纯函数可测。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.cover_engine.title_art.char_frequency import title_has_only_common_chars
from travelogue.cover_engine.title_art.color import pick_readable_color, recolor_ink_on_white
from travelogue.cover_engine.title_art.contract import resolve_title_text
from travelogue.cover_engine.title_art.fonts import (
    FALLBACK_STACK,
    glyphs_covered,
    pick_default_font,
)
from travelogue.cover_engine.title_art.models import TitleArtResult, disabled_meta_dict
from travelogue.cover_engine.title_art.ocr_verify import ocr_verify as _default_ocr_verify
from travelogue.cover_engine.title_art.placement import best_placement, focal_conflict
from travelogue.cover_engine.title_art.render_b import render_title_art
from travelogue.cover_engine.title_art.route_c import RouteCFailure
from travelogue.cover_engine.title_art.route_c import generate_raw as _default_generate_raw
from travelogue.cover_engine.title_art.style_registry import default_style_id
from travelogue.cover_engine.title_art.whitelist import (
    PlacementPreset,
    is_whitelisted,
    placement_presets,
)

_log = logging.getLogger(__name__)

_SEAL_CHAR_DEFAULT = "旅"

#: ``journal.css`` ``--cover-folio-paper: #f4f1ea``——folio-overlap 左侧纸面栏
#: 的固定底色，与 asset 内容无关（OQ-CAL-09 收尾，见 ``assume_paper_bg``）。
_FOLIO_PAPER_RGB = (0xF4, 0xF1, 0xEA)

ResolveAssetPathFn = Callable[[dict[str, Any]], "Path | None"]
WritePngFn = Callable[[bytes], str]
DetectFacesFn = Callable[[Image.Image], list[tuple[int, int, int, int]]]


def _cover_asset(trip: dict) -> dict[str, Any] | None:
    asset_id = str(trip.get("coverAssetId") or "")
    if not asset_id:
        return None
    assets = trip.get("assets") if isinstance(trip.get("assets"), list) else []
    return next(
        (a for a in assets if isinstance(a, dict) and str(a.get("id") or "") == asset_id), None
    )


def _contact_stamp_hook_or_archive_present(trip: dict, cover_asset: dict[str, Any]) -> bool:
    """contact-stamp 右下角备选候选是否被 hook/档案条占用（D-CAL-20 优先顺位⑤）。

    必须跟 ``assemble.py`` 用同一套判定，否则会重演"两处各自维护一份数据"
    的接线缺口（2026-08-07 CSS 侧白名单未同步那次教训）——复用
    ``render.cover_opening`` 里已抽出的共享函数，不在这里重新手搓一份可能
    跟渲染层脱节的逻辑。刻意不接分享面的 ``sanitize_share_copy_tracked``
    护栏：draft 面永远展示未过滤的 hook，为了让同一张 title-art PNG 在两个
    面都安全，这里按"draft 会不会显示"保守判定——宁可少用一个候选，不要
    在分享面才发现冲突。
    """
    from travelogue.render.context import format_trip_meta
    from travelogue.render.cover_opening import build_cover_archive_strip, show_hook_on_cover

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    hook = str(meta.get("hook") or "").strip()
    if show_hook_on_cover(hook):
        return True
    _, _, cover_place, meta_subline = format_trip_meta(
        meta, intent=trip.get("intent"), assets=trip.get("assets") or []
    )
    archive_strip = build_cover_archive_strip(
        meta_subline=meta_subline, cover_place=cover_place, cover_asset=cover_asset
    )
    return bool(archive_strip)


def _folio_place_present(trip: dict, cover_asset: dict[str, Any]) -> bool:
    """folio-overlap 全高备选是否被地点标签（``.cover-opening__place``）占用（OQ-CAL-09）。

    该风格的地点标签跟纸面栏共享 DOM（竖排贴在纸面栏顶部），是否渲染取决于
    ``resolve_show_cover_place``——跟 ``assemble.py`` 完全同一套判定（同一个
    共享函数），否则会重演"两处各自维护一份数据"的接线缺口。``cover_asset``
    参数在这里没被用到（folio 的占用判定跟封面照片无关，只看标题/地点文案），
    保留是为了跟 ``_CONDITIONAL_OCCUPANT_CHECKS`` 统一的函数签名。
    """
    del cover_asset
    from travelogue.domain.title_humanize import resolve_display_title
    from travelogue.render.context import format_trip_meta
    from travelogue.render.cover_opening import resolve_show_cover_place

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    meta_title = resolve_display_title(meta)
    _, _, cover_place, _ = format_trip_meta(
        meta, intent=trip.get("intent"), assets=trip.get("assets") or []
    )
    raw_meta_title = str(meta.get("title") or "").strip()
    return resolve_show_cover_place(
        cover_place=cover_place, meta_title=meta_title, raw_meta_title=raw_meta_title
    )


#: tag → 本模块内检查函数的**名字**（不是函数对象本身）。故意存名字、用
#: ``globals()`` 动态取值而不是直接存函数引用——直接存引用会在模块加载时
#: 把字典值锚定到当时的函数对象，之后 ``monkeypatch.setattr(engine, "_xxx",
#: stub)`` 替换的是模块属性，不会影响字典里已经绑死的旧引用，单测想 mock
#: 这个检查函数会安静地失效（无报错但行为对不上）。
_CONDITIONAL_OCCUPANT_CHECKS: dict[str, str] = {
    "contact_stamp_hook_or_archive": "_contact_stamp_hook_or_archive_present",
    "folio_place_present": "_folio_place_present",
}


def _candidate_occupied(preset: PlacementPreset, trip: dict, cover_asset: dict[str, Any]) -> bool:
    tag = preset.conditional_occupant
    if not tag:
        return False
    fn_name = _CONDITIONAL_OCCUPANT_CHECKS.get(tag)
    check = globals().get(fn_name) if fn_name else None
    if check is None:
        return False
    try:
        return bool(check(trip, cover_asset))
    except Exception:
        # 判定失败时保守当作"已占用"——不要冒险选一个可能真的冲突的候选。
        return True


def _cover_image_for_placement(
    trip: dict, *, resolve_asset_path: ResolveAssetPathFn
) -> Image.Image | None:
    asset = _cover_asset(trip)
    if asset is None:
        return None
    try:
        path = resolve_asset_path(asset)
    except Exception:
        return None
    if path is None or not Path(path).is_file():
        return None
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


def resolve_title_art(
    trip: dict,
    *,
    resolve_asset_path: ResolveAssetPathFn,
    write_png: WritePngFn,
    route_c_enabled: bool = False,
    route_c_style_id: str | None = None,
    force: bool = False,
    detect_faces: DetectFacesFn | None = None,
    generate_raw: Callable[..., Any] = _default_generate_raw,
    ocr_verify: Callable[..., bool] = _default_ocr_verify,
) -> TitleArtResult | None:
    """计算并写入 ``trip["meta"]["titleArt"]``；同一 trip 非 force 且已有非
    stale 结果时跳过重算（避免每次「优化装帧」都重打路线 C API）。

    返回写入的 :class:`TitleArtResult`；fail-open（非白名单/空标题/字形不
    覆盖）时写回禁用占位并返回 ``None``。
    """
    meta = trip.setdefault("meta", {})
    existing = meta.get("titleArt") if isinstance(meta.get("titleArt"), dict) else None
    if existing and not force and not existing.get("stale") and existing.get("enabled"):
        return None

    style_id = str(meta.get("coverOpeningStyle") or "")
    if not is_whitelisted(style_id):
        meta["titleArt"] = disabled_meta_dict()
        return None

    text = resolve_title_text(trip)
    if text.empty:
        meta["titleArt"] = disabled_meta_dict()
        return None

    default_font = pick_default_font()
    fallback_fonts = (default_font.filename, *FALLBACK_STACK)
    probe_text = text.main + (text.subtitle or "")
    if not glyphs_covered(fallback_fonts, probe_text):
        meta["titleArt"] = disabled_meta_dict()
        return None

    cover_asset = _cover_asset(trip)
    cover_img = _cover_image_for_placement(trip, resolve_asset_path=resolve_asset_path)

    # D-CAL-20 优先顺位⑤：候选列表 = 主候选 + 已知安全的备选（多数风格今天
    # 仍只有 1 个，contact-stamp 有 2 个）。两层淘汰：① 备选若带
    # conditional_occupant，按该 trip 实际内容判定是否被占用；② 焦点冲突
    # 淘汰（D-CAL-20 优先顺位④）。剩余候选交给 best_placement 真正打分择优
    # ——如果剩到只有 1 个，打分是形式化的（唯一选项），跟"固定绑死一个矩形"
    # 行为完全等价，不引入额外随机性。
    candidates = placement_presets(style_id)
    if cover_asset is not None:
        candidates = [c for c in candidates if not _candidate_occupied(c, trip, cover_asset)]
        # OQ-CAL-09 收尾：assume_paper_bg 候选压在跟照片无关的固定纸面色块上
        # （如 folio-overlap 左侧纸面栏，该区域根本不显示 .cover-hero 照片）。
        # focal_conflict 检查的是"镜头焦点是否落在这块矩形对应的照片区域
        # 内"——对这类候选而言这个问题本身就不成立（矩形对应的不是照片内容，
        # 镜头主体不可能视觉上出现在纸面上），跳过它，否则会因为焦点恰好落在
        # 原始照片的对应坐标而误判"冲突"，冤枉淘汰一个实际完全安全的候选。
        candidates = [
            c for c in candidates if c.assume_paper_bg or not focal_conflict(cover_asset, c.rect)
        ]

    if not candidates:
        # 主 + 备选全部被淘汰——要么跟镜头焦点冲突，要么被本风格自身 UI
        # （面板/hook/档案条）占用，没有安全位置可用。宁可回退纯 HTML 标题，
        # 也不要硬贴一个大概率读不出来/挡脸的贴纸。
        _log.info(
            "title_art all candidates rejected (focal conflict / occupied) → fail-open: "
            "style=%s",
            style_id,
        )
        meta["titleArt"] = disabled_meta_dict(reason=f"focal_conflict:{style_id}")
        return None

    bg_rgb = (60, 60, 60)
    placement_pos = {"x": 0.5, "y": 0.28}
    explain: list[str] = []
    if cover_img is not None:
        from travelogue.cover_engine.title_art.color import roi_average_color

        face_fn = detect_faces
        if face_fn is None:
            try:
                from travelogue.media.subject_detect import detect_faces_in_image as face_fn
            except Exception:
                face_fn = None
        cand = best_placement(cover_img, candidates, detect_faces=face_fn)
        if cand is not None:
            x, y, w, h = cand.box
            iw, ih = cover_img.size
            if iw > 0 and ih > 0:
                placement_pos = {
                    "x": round((x + w / 2) / iw, 4),
                    "y": round((y + h / 2) / ih, 4),
                }
            bg_rgb = roi_average_color(cover_img, cand.box)
            explain.extend(cand.explain)
            if cand.preset.assume_dark_veil:
                # 该风格会在此区域固定叠加与照片无关的深色渐罩（journal.css），
                # 原始照片 ROI 的亮度采样是「遮罩前」的，直接采信会误判成够亮
                # 从而选深墨，实际渲染出来深墨读不出来——改用近黑背景估计，
                # §6.1 contrast_ratio 算法必然选回白色（2026-08-07 真实视觉核对）。
                bg_rgb = (10, 10, 10)
                explain.append(f"{style_id} 固定深色渐罩 · 忽略照片原始亮度采样")
            elif cand.preset.assume_paper_bg:
                # OQ-CAL-09 收尾：该候选压在跟照片内容完全无关的固定纸面色块
                # 上（如 folio-overlap 左侧纸面栏——那块区域压根不显示照片），
                # 原始照片 ROI 采样出来的像素跟实际渲染背景毫无关系，直接改用
                # 该风格的纸面色（journal.css ``--cover-folio-paper``）固定估计。
                bg_rgb = _FOLIO_PAPER_RGB
                explain.append(f"{style_id} 纸面底色区 · 忽略照片原始像素采样")

    contrast = pick_readable_color(bg_rgb)

    fallback_from: str | None = None
    if route_c_enabled:
        style_c = route_c_style_id or default_style_id()
        if not title_has_only_common_chars(text.main):
            # D-CAL-21 · Route C W0.5 Spike 数据驱动预筛选：标题含生僻字
            # （GB2312 一级常用字表以外）时大概率 OCR 不过（Spike 实测生僻
            # 字类目通过率仅 55.6%），直接短路到路线 B——省一次注定大概率
            # 失败的 15~28 秒 API 调用，不改变最终正确性（D-CAL-19 OCR 回读
            # 校验依旧是唯一真正的安全闸门；被本条拦下跟"调用了但 OCR 没
            # 过"最终展示效果完全等价，都是路线 B）。
            _log.info(
                "title_art route C skipped by char-frequency prefilter: style=%s", style_c
            )
            fallback_from = "diffusion-fixed-prompt-v1"
            explain.append(f"{style_c} 预筛选：标题含生僻字，直接走路线B（未调用API，D-CAL-21）")
        else:
            try:
                raw = generate_raw(style_c, title=text.main, subtitle=text.subtitle)
                if not ocr_verify(raw.image, text.main):
                    raise RouteCFailure("E_CAL_C_OCR_MISMATCH")
                ink = recolor_ink_on_white(raw.image, contrast.color_rgb)
                asset_path = write_png(_png_bytes(ink))
                result = TitleArtResult(
                    enabled=True,
                    stale=False,
                    engine="diffusion-fixed-prompt-v1",
                    template=style_c,
                    font="",
                    main_rendered=text.main,
                    truncated=text.truncated,
                    subtitle=text.subtitle,
                    main_color=contrast.color_hex,
                    seal_color="#B03A2E",
                    opening_style_id=style_id,
                    position=placement_pos,
                    asset_path=asset_path,
                    source_title=text.main,
                    explain=[*explain, f"路线C · {style_c} · {raw.model}"],
                    style_id=style_c,
                    prompt_version="v1",
                    model_provider="wanxiang",
                    ocr_verified=True,
                    fallback_from=None,
                )
                meta["titleArt"] = result.to_meta_dict()
                return result
            except RouteCFailure as exc:
                _log.info("title_art route C → fallback to route B: %s", exc)
                fallback_from = "diffusion-fixed-prompt-v1"

    rendered = render_title_art(
        text.main,
        subtitle=text.subtitle,
        main_color=contrast.color_rgb,
        seal_char=_SEAL_CHAR_DEFAULT,
        font=default_font,
    )
    asset_path = write_png(rendered.png_bytes)
    result = TitleArtResult(
        enabled=True,
        stale=False,
        engine="clean-pipeline-v1",
        template=rendered.template,
        font=rendered.font_name,
        main_rendered=text.main,
        truncated=text.truncated,
        subtitle=text.subtitle,
        main_color=contrast.color_hex,
        seal_color="#B03A2E",
        opening_style_id=style_id,
        position=placement_pos,
        asset_path=asset_path,
        source_title=text.main,
        explain=[*explain, "路线B · 字库合成" + ("（路线C fallback）" if fallback_from else "")],
        fallback_from=fallback_from,
    )
    meta["titleArt"] = result.to_meta_dict()
    return result


def _png_bytes(img: Image.Image) -> bytes:
    from travelogue.cover_engine.title_art.color import image_to_png_bytes

    return image_to_png_bytes(img)


def mark_title_art_stale(trip: dict) -> None:
    """封面照片/标题/coverOpeningStyle 变更后调用，下一次 resolve 强制重算。"""
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else None
    if not isinstance(meta, dict):
        return
    title_art = meta.get("titleArt")
    if isinstance(title_art, dict) and title_art.get("enabled"):
        title_art["stale"] = True
