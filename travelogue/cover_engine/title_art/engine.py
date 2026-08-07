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

from travelogue.cover_engine.title_art.color import pick_readable_color, recolor_ink_on_white
from travelogue.cover_engine.title_art.contract import resolve_title_text
from travelogue.cover_engine.title_art.fonts import (
    FALLBACK_STACK,
    glyphs_covered,
    pick_default_font,
)
from travelogue.cover_engine.title_art.models import TitleArtResult, disabled_meta_dict
from travelogue.cover_engine.title_art.ocr_verify import ocr_verify as _default_ocr_verify
from travelogue.cover_engine.title_art.placement import best_placement
from travelogue.cover_engine.title_art.render_b import render_title_art
from travelogue.cover_engine.title_art.route_c import RouteCFailure
from travelogue.cover_engine.title_art.route_c import generate_raw as _default_generate_raw
from travelogue.cover_engine.title_art.style_registry import default_style_id
from travelogue.cover_engine.title_art.whitelist import is_whitelisted, placement_preset

_log = logging.getLogger(__name__)

_SEAL_CHAR_DEFAULT = "旅"

ResolveAssetPathFn = Callable[[dict[str, Any]], "Path | None"]
WritePngFn = Callable[[bytes], str]
DetectFacesFn = Callable[[Image.Image], list[tuple[int, int, int, int]]]


def _cover_image_for_placement(
    trip: dict, *, resolve_asset_path: ResolveAssetPathFn
) -> Image.Image | None:
    asset_id = str(trip.get("coverAssetId") or "")
    if not asset_id:
        return None
    assets = trip.get("assets") if isinstance(trip.get("assets"), list) else []
    asset = next(
        (a for a in assets if isinstance(a, dict) and str(a.get("id") or "") == asset_id), None
    )
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

    cover_img = _cover_image_for_placement(trip, resolve_asset_path=resolve_asset_path)
    preset = placement_preset(style_id)
    bg_rgb = (60, 60, 60)
    placement_pos = {"x": 0.5, "y": 0.28}
    explain: list[str] = []
    if cover_img is not None and preset is not None:
        from travelogue.cover_engine.title_art.color import roi_average_color

        face_fn = detect_faces
        if face_fn is None:
            try:
                from travelogue.media.subject_detect import detect_faces_in_image as face_fn
            except Exception:
                face_fn = None
        cand = best_placement(cover_img, [preset], detect_faces=face_fn)
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

    contrast = pick_readable_color(bg_rgb)

    fallback_from: str | None = None
    if route_c_enabled:
        style_c = route_c_style_id or default_style_id()
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
