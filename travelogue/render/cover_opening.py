"""Cover opening helpers: place/title de-dupe, system hook filter, cover media fit."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

# Stub hooks from travelogue.services.narrate._build_hook (frame / pre-LLM).
# Keep legacy「碎片」patterns for old trips; also catch W1/W2「照片汇成」类模板句.
_SYSTEM_HOOK_PATTERNS = (
    re.compile(r"^\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^\d+\s*张照片汇成这一页[。．]?$"),
    re.compile(r"^.+，\d+\s*帧记录[。．]?$"),
    re.compile(r"^.+，\d+\s*张照片[。．]?$"),
    re.compile(r"^.+，\d+\s*帧留在这里[。．]?$"),
    re.compile(r"^.+，\d+\s*张照片留在这里[。．]?$"),
    re.compile(r"^.+[·•].+，慢慢翻[。．]?$"),
    re.compile(r"^在.+的(\d+天|[\d\.]+\s*[–-]\s*[\d\.]+)，\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^在.+的(\d+天|[\d\.]+\s*[–-]\s*[\d\.]+)，\d+\s*张照片汇成这一页[。．]?$"),
    re.compile(r"^.+·.+，\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^.+·.+，\d+\s*张照片汇成这一页[。．]?$"),
)

_PORTRAIT_CONTAIN_AR = 1.2


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip().casefold())


def cover_place_is_distinct(place: str, title: str) -> bool:
    """False when place duplicates the magazine title (common with narrative_copy_subject)."""
    p = _normalize_label(place)
    t = _normalize_label(title)
    if not p:
        return False
    if not t:
        return True
    if p == t:
        return False
    # 近重复：较短一方几乎占满较长一方（避免「黔西南三日漫游」vs「…·精选」）
    # 但不误伤「京都」vs「雨后京都」这类地名眉题
    shorter, longer = (p, t) if len(p) <= len(t) else (t, p)
    if shorter in longer and len(shorter) >= max(4, int(len(longer) * 0.7)):
        return False
    return True


def is_system_cover_hook(hook: str) -> bool:
    text = (hook or "").strip()
    if not text:
        return False
    return any(p.match(text) for p in _SYSTEM_HOOK_PATTERNS)


def show_hook_on_cover(hook: str) -> bool:
    text = (hook or "").strip()
    if not text:
        return False
    if is_system_cover_hook(text):
        return False
    return len(text) <= 56


def cover_asset_aspect(asset: dict) -> float | None:
    try:
        w = float(asset.get("width") or 0)
        h = float(asset.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return w / h


def cover_use_contain_fit(asset: dict) -> bool:
    ar = cover_asset_aspect(asset)
    return ar is not None and ar < _PORTRAIT_CONTAIN_AR


def resolve_split_mat_title_layout(title: str) -> str:
    """split-mat cover title axis: vertical | vertical-compact | horizontal."""
    text = (title or "").strip()
    n = len(text)
    if n <= 8:
        return "vertical"
    if n <= 14:
        return "vertical-compact"
    return "horizontal"


def resolve_monument_title_layout(title: str) -> str:
    """type-monument 镂空巨字尺寸档：compact | wrapped | wrapped-long。

    起因：`--cover-monument-title-size: min(25vw, 45vh)` 是给 2~4 字短标题
    设计的巨字尺寸（单行，`line-height:0.88` 紧排出"石刻碑文"的厚重感）。
    该尺寸对更长的标题原样使用时，`-webkit-line-clamp:3` 会把文字换到 2~3
    行，但 0.88 的行高比 1 更紧，大字重笔画又有纵向溢出（尤其粗体/毛笔感
    字形），换行后相邻两行会真的视觉重叠——不是排版 bug，是"巨字尺寸没有
    随标题变长收敛"这件事本身没做（详见 D-CAL-26 附带发现 §8.4）。

    分档给 CSS 用（不做完全动态度量，避免引入 JS 运行时测量）：短标题维持
    原尺寸单行效果；中/长标题按经验档降字号 + 放宽行高，用真实标题渲染
    截图核对过（见决策记录）。
    """
    text = (title or "").strip()
    n = len(text)
    if n <= 4:
        return "compact"
    if n <= 7:
        return "wrapped"
    return "wrapped-long"


def resolve_show_cover_place(
    *, cover_place: str, meta_title: str, raw_meta_title: str
) -> bool:
    """是否在封面渲染 ``.cover-opening__place``（D-CAL-20 优先顺位⑤延伸）。

    从 ``assemble.py`` 抽出，供 ``travelogue.cover_engine.title_art.engine``
    复用——引擎需要判定某个 trip 在 folio-overlap 风格下，左侧纸面栏顶部是否
    会被竖排地点标签实际占用，从而决定 title-art 全列候选是否安全，必须跟
    这里完全同一套判定，否则会重演"两处各自维护一份数据"的接线缺口（呼应
    2026-08-07 CSS 侧白名单未同步 / contact-stamp 档案条判定那两次教训）。
    """
    return cover_place_is_distinct(cover_place, meta_title) and (
        not raw_meta_title or cover_place_is_distinct(cover_place, raw_meta_title)
    )


def build_cover_archive_strip(
    *, meta_subline: str, cover_place: str, cover_asset: dict[str, Any]
) -> str:
    """contact-stamp 档案条文案（仅用 trip meta，reader 端拿不到相机 EXIF）。

    从 ``assemble.py`` 抽出（D-CAL-20 优先顺位⑤）：``travelogue.cover_engine
    .title_art.engine`` 需要判定某个 trip 在 contact-stamp 右下角是否会渲染
    出档案条文案，从而决定 title-art 的右下角候选是否安全可用——必须跟这里
    完全同一套逻辑，否则会重演「两处各自维护一份数据」的接线缺口（呼应
    2026-08-07 CSS 侧白名单未同步那次教训）。
    """
    archive_bits: list[str] = []
    if meta_subline:
        archive_bits.append(str(meta_subline).strip())
    if cover_place and cover_place not in (meta_subline or ""):
        archive_bits.append(cover_place)
    taken_at = str(cover_asset.get("takenAt") or "").strip()
    if taken_at:
        try:
            from datetime import datetime as _dt

            t = _dt.fromisoformat(taken_at.replace("Z", "+00:00"))
            archive_bits.append(t.strftime("%H:%M"))
        except ValueError:
            pass
    return "\n".join(archive_bits[:3]) if archive_bits else ""


def cover_focal_point(asset: dict) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        fx, fy = 0.5, 0.45
    return max(0.0, min(1.0, fx)), max(0.0, min(1.0, fy))


def resolve_cover_subtitle(trip: dict[str, Any] | None, meta: dict[str, Any] | None = None) -> str:
    """R2.1 · ``{subtitle 或 一句话} · {日期范围}``；绝不拼入杂志 title。"""
    trip = trip or {}
    meta = meta if isinstance(meta, dict) else (trip.get("meta") or {})
    from travelogue.services.narrative_brief import resolve_user_notes

    raw_subtitle = str(meta.get("subtitle") or "").strip()
    one_liner = (resolve_user_notes(trip) or "").strip()
    base = raw_subtitle or one_liner
    if not base:
        return ""
    date_bit = ""
    start = str(meta.get("dateStart") or "").strip()[:10]
    end = str(meta.get("dateEnd") or "").strip()[:10]
    if start:
        try:
            d0 = date.fromisoformat(start)
            date_bit = d0.strftime("%Y.%m.%d")
            if end and end != start:
                d1 = date.fromisoformat(end)
                date_bit = f"{date_bit} – {d1.strftime('%m.%d')}"
        except ValueError:
            date_bit = ""
    out = f"{base} · {date_bit}" if date_bit and date_bit not in base else base
    return out[:80] if len(out) > 80 else out
