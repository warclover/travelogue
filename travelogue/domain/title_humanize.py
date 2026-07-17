"""Share-Ready W2 · default trip title from folder names (D-SR-14 / BE-SR-05).

First-Session Trust W1 · BE-FST-06 · folder-noise → displayTitle fallback.
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


def is_folder_title_noise(title: str | None) -> bool:
    """True when title looks like a folder/export name (W1 Chinese heuristics)."""
    t = (title or "").strip()
    if not t or t == _DEFAULT_TITLE:
        return False
    if _EXPORT_DIRISH.search(t):
        return True
    if _CJK_TRAILING_DIGIT.search(t):
        return True
    if " " not in t and "·" not in t and "—" not in t and _GLUED_ALNUM.match(t):
        return True
    return False


def _date_fallback_label(meta: dict[str, Any] | None) -> str:
    meta = meta or {}
    start = str(meta.get("dateStart") or "").strip()[:10]
    end = str(meta.get("dateEnd") or "").strip()[:10]
    if not start:
        return "游记"
    try:
        y, m, d = start.split("-")
        label = f"{int(m)}月{int(d)}日"
    except ValueError:
        return "游记"
    if end and end != start:
        try:
            _, m2, d2 = end.split("-")
            label = f"{int(m)}月{int(d)}–{int(m2)}月{int(d2)}日"
        except ValueError:
            pass
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


def resolve_display_title(
    meta: dict[str, Any] | None,
    *,
    limit: int = 20,
    raw_title: str | None = None,
) -> str:
    """Cover / FirstSuccess / shelf display name (BE-FST-06).

    Prefer stored ``meta.displayTitle``; else humanize; if still folder-noise,
    fall back to ``{place|旅行} · {date|游记}``.
    """
    meta = meta or {}
    stored = str(meta.get("displayTitle") or "").strip()
    if stored:
        return stored[:limit] if len(stored) > limit else stored

    raw = (raw_title if raw_title is not None else str(meta.get("title") or "")).strip()
    cleaned = humanize_folder_title(raw, limit=limit) if raw else _DEFAULT_TITLE
    if not is_folder_title_noise(raw) and not is_folder_title_noise(cleaned):
        return cleaned

    place = _place_fallback_label(meta)
    date_part = _date_fallback_label(meta)
    fallback = f"{place} · {date_part}"
    return fallback[:limit] if len(fallback) > limit else fallback
