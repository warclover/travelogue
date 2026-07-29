"""Share-Ready W2 · default trip title from folder names (D-SR-14 / BE-SR-05).

First-Session Trust W1 · BE-FST-06 · folder-noise → displayTitle fallback.
Share-Face Closeout W0 · D-SFC-03 · 再校验 stored displayTitle；地名抽取（OQ-SFC-01）。
"""

from __future__ import annotations

import re
from typing import Any

_DEFAULT_TITLE = "我的旅途"
# 仅剥已知媒体/压缩后缀；文件夹名可合法含点（如「2024.10 京都」）。
_KNOWN_SUFFIX = re.compile(
    r"\.(?:zip|jpe?g|png|gif|webp|heic|heif|bmp|tiff?|mov|mp4|avi|mkv|pdf|rar|7z)$",
    re.IGNORECASE,
)
_HASH_OR_TEST_SUFFIX = re.compile(
    r"[-_]?(?:[0-9a-f]{8,}|(?:ux-)?handtest[-_\w]*|demo[-_]?\d+|copy(?:\s*\(\d+\))?)$",
    re.IGNORECASE,
)
_NOISE_PREFIX = re.compile(r"^(新建文件夹|untitled|copy)\s*", re.IGNORECASE)
_HEXISH = re.compile(r"^[0-9a-f-]{8,}$", re.IGNORECASE)
# 中文启发式 · OQ-FST-02：尾缀数字 / 无分隔粘连 / 导出目录腔
_CJK_TRAILING_DIGIT = re.compile(r"[\u4e00-\u9fff]\d{1,3}$")
_GLUED_ALNUM = re.compile(r"^[\u4e00-\u9fffA-Za-z]{2,}\d{1,3}$")
_EXPORT_DIRISH = re.compile(
    r"(导出|download|dcim|camera roll|img_|vid_|screenshot)",
    re.IGNORECASE,
)
_LEADING_YEAR = re.compile(r"^(?:19|20)\d{2}")
_TRAILING_SERIAL = re.compile(r"\d{1,3}$")
_CJK_PLACE = re.compile(r"^[\u4e00-\u9fff]{2,6}$")
_DIRTY_SEP = re.compile(r"--|_{2,}|\.\.")
# SFP D-SFP-04 · 「旅行 · 24 1 20–25 1 16」/「24.1.20–25.1.16」数字日期链
# （勿误伤「旅行 · 1月20日」/「2024.10 京都」类文件夹名）
_DIGIT_DATE_SPAN = re.compile(
    r"(?:"
    r"\d{1,2}\s+\d{1,2}\s+\d{1,2}\s*[–—\-~～]\s*\d{1,2}\s+\d{1,2}\s+\d{1,2}"
    r"|"
    r"\d{1,2}\.\d{1,2}\.\d{1,2}\s*[–—\-~～]\s*\d{1,2}\.\d{1,2}\.\d{1,2}"
    r"|"
    r"旅行\s*·\s*\d{1,2}[\s.]\d{1,2}"
    r"|"
    r"(?<![月日年./])\d{1,2}\s+\d{1,2}\s+\d{1,2}(?!\s*[月日])"
    r")"
)
_TRAILING_CJK_SERIAL = re.compile(r"([\u4e00-\u9fff]+)\d{1,3}$")


def humanize_folder_title(raw: str | None, *, limit: int = 20) -> str:
    """Clean folder/upload basename into a readable default magazine title.

    Does not decide overwrite policy — callers must skip when the user already edited.
    """
    name = (raw or "").strip()
    if not name:
        return _DEFAULT_TITLE
    name = _KNOWN_SUFFIX.sub("", name)
    name = _HASH_OR_TEST_SUFFIX.sub("", name)
    name = re.sub(r"[_\-.]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = _NOISE_PREFIX.sub("", name).strip()
    if not name or _HEXISH.match(name):
        return _DEFAULT_TITLE
    if len(name) > limit:
        return name[:limit]
    return name


def looks_like_digit_date_span(title: str | None) -> bool:
    """D-SFP-04 · bare digit / space date chains that must not win the cover face."""
    t = (title or "").strip()
    if not t:
        return False
    return bool(_DIGIT_DATE_SPAN.search(t))


def is_folder_title_noise(title: str | None) -> bool:
    """True when title looks like a folder/export name (W1 Chinese heuristics)."""
    t = (title or "").strip()
    if not t or t == _DEFAULT_TITLE:
        return False
    if _DIRTY_SEP.search(t):
        return True
    if _EXPORT_DIRISH.search(t):
        return True
    if looks_like_digit_date_span(t):
        return True
    if _CJK_TRAILING_DIGIT.search(t):
        return True
    if " " not in t and "·" not in t and "—" not in t and _GLUED_ALNUM.match(t):
        return True
    return False


def _soften_title_candidate(title: str | None) -> str:
    """Drop trailing folder serial (「精选2」→「精选」) for display ranking only."""
    t = (title or "").strip()
    if not t:
        return ""
    m = _TRAILING_CJK_SERIAL.match(t)
    if m:
        return m.group(1).strip()
    return t


def extract_place_label(raw: str | None) -> str | None:
    """OQ-SFC-01 · 从脏文件夹名抽取 2–6 字中文地名（去尾数字与前导年份）。"""
    cleaned = humanize_folder_title(raw, limit=40)
    if not cleaned or cleaned == _DEFAULT_TITLE:
        return None
    t = cleaned.replace(" ", "")
    t = _TRAILING_SERIAL.sub("", t)
    t = _LEADING_YEAR.sub("", t)
    t = t.strip(" ·-_.")
    if _CJK_PLACE.match(t):
        return t
    return None


def _parse_iso_ymd(value: str) -> tuple[int, int, int] | None:
    parts = str(value or "").strip()[:10].split("-")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _is_cross_year_span(meta: dict[str, Any] | None) -> bool:
    meta = meta or {}
    start = _parse_iso_ymd(str(meta.get("dateStart") or ""))
    end = _parse_iso_ymd(str(meta.get("dateEnd") or ""))
    return bool(start and end and start[0] != end[0])


def _looks_like_yearless_date_span(label: str) -> bool:
    """Detect shelf labels like ``1月20–1月16日`` that omit year (cross-year smell)."""
    t = str(label or "").strip()
    if not t or "年" in t or re.search(r"(?:19|20)\d{2}", t):
        return False
    return bool(re.search(r"\d{1,2}月\d{1,2}.+\d{1,2}月\d{1,2}", t))


def _date_fallback_label(meta: dict[str, Any] | None) -> str:
    meta = meta or {}
    start = _parse_iso_ymd(str(meta.get("dateStart") or ""))
    if not start:
        return "画册"
    y, m, d = start
    label = f"{m}月{d}日"
    end = _parse_iso_ymd(str(meta.get("dateEnd") or ""))
    if end and end != start:
        y2, m2, d2 = end
        if y != y2:
            # Compact cross-year form fits shelf limit (~20 with place prefix)
            label = f"{y % 100}.{m}.{d}–{y2 % 100}.{m2}.{d2}"
        else:
            label = f"{m}月{d}–{m2}月{d2}日"
    return label


def _place_fallback_label(meta: dict[str, Any] | None) -> str:
    meta = meta or {}
    places = meta.get("places") or []
    if isinstance(places, list):
        for p in places:
            s = str(p or "").strip()
            if s and s not in {"旅途", "未知", "这里"}:
                return s
    return "旅行"


def _fallback_display(meta: dict[str, Any] | None, *, limit: int) -> str:
    place = _place_fallback_label(meta)
    date_part = _date_fallback_label(meta)
    fallback = f"{place} · {date_part}"
    return fallback[:limit] if len(fallback) > limit else fallback


def _accept_display(candidate: str, *, limit: int) -> str | None:
    """Return humanized title when清洗后已可读；否则 None（交 resolve 做地点回退）。"""
    from travelogue.domain.share_face_copy import is_unsafe_share_copy

    t = (candidate or "").strip()
    if not t:
        return None
    # PMX · 题名禁词（如「示例游记」）不得上展示面；先清洗再判，避免裸「--」误伤
    cleaned = humanize_folder_title(t, limit=limit)
    if not cleaned or cleaned == _DEFAULT_TITLE or is_folder_title_noise(cleaned):
        return None
    if is_unsafe_share_copy(cleaned, kind="title"):
        return None
    return cleaned


def migrate_stale_display_title(meta: dict[str, Any] | None) -> bool:
    """D2 / D-SFP-12 · sync stale ``displayTitle`` to resolved face (save/open path).

    Returns True when ``meta`` was mutated. Idempotent when already aligned.
    Never promotes folder-noise titles into the display face.
    Never overwrites user-protected magazine titles (USR-SFP-04).
    """
    from travelogue.domain.copy_origin import is_user_protected

    meta = meta if isinstance(meta, dict) else None
    if not meta:
        return False
    if is_user_protected(meta, "titleOrigin"):
        return False
    resolved = resolve_display_title(meta, limit=32)
    stored = str(meta.get("displayTitle") or "").strip()
    if not resolved or stored == resolved:
        return False
    meta["displayTitle"] = resolved[:32]
    return True

def resolve_display_title(
    meta: dict[str, Any] | None,
    *,
    limit: int = 20,
    raw_title: str | None = None,
) -> str:
    """Cover / FirstSuccess / shelf display name (BE-FST-06 · D-SFC-03 · D-SFP-03).

    Prefer readable ``title`` over dirty stored ``displayTitle`` (quality order).
    Noise path: 有真实地点 → ``{地} · {日}``；否则地名抽取 → ``{地} · 旅行``（OQ-SFC-01）。
    """
    from travelogue.domain.share_face_copy import is_unsafe_share_copy

    meta = meta or {}
    stored = str(meta.get("displayTitle") or "").strip()
    raw = (raw_title if raw_title is not None else str(meta.get("title") or "")).strip()

    def _try(candidate: str) -> str | None:
        accepted = _accept_display(candidate, limit=limit)
        if accepted and _is_cross_year_span(meta) and _looks_like_yearless_date_span(accepted):
            return None
        if accepted and looks_like_digit_date_span(accepted):
            return None
        return accepted

    # D-SFP-03 · 可读 title 优于脏 displayTitle（先试原串）
    for candidate in (raw, stored):
        accepted = _try(candidate)
        if accepted:
            return accepted

    # D-SFP-04 · stored 为数字日期链（含点号形）时，允许「精选2」→「精选」抢面
    if looks_like_digit_date_span(stored):
        soft = _soften_title_candidate(raw)
        if soft and soft != raw:
            accepted = _try(soft)
            if accepted:
                return accepted

    # 清洗后仍噪音：优先 meta 地点；否则文件夹地名抽取
    meta_place = _place_fallback_label(meta)
    if meta_place != "旅行":
        return _fallback_display(meta, limit=limit)

    # PMX · 禁词题名不得经 extract_place_label 再拼回展示面
    leak_source = raw or stored
    if leak_source and is_unsafe_share_copy(leak_source, kind="title"):
        return _fallback_display(meta, limit=limit)

    extracted = extract_place_label(leak_source)
    if extracted and not is_unsafe_share_copy(extracted, kind="title"):
        out = f"{extracted} · 旅行"
        return out[:limit] if len(out) > limit else out

    return _fallback_display(meta, limit=limit)
