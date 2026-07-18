"""Share-Face Closeout W0 · 分享面文案护栏（空优于假句 · D-SFC-01/02）。

供 narrate 写入与 render 读取共用，禁止说明书腔 / 弱枚举 / 标题复读上分享面。
"""

from __future__ import annotations

import re
import unicodedata

# 说明书腔 / 构图假句（子串命中即空）
_BANNED_SUBSTRINGS: tuple[str, ...] = (
    "竖幅",
    "横幅",
    "抬头看见",
    "慢慢翻",
    "碎片拼成",
    "下次再见",
)

# 纯时段弱枚举：仅由时段词 + 顿号/逗号组成
_DAYPART_TOKENS = ("清晨", "上午", "中午", "正午", "下午", "傍晚", "晚上", "夜景", "白天", "夜里", "凌晨")
_WEAK_ENUM = re.compile(
    r"^[\s]*"
    + r"(?:"
    + "|".join(re.escape(t) for t in _DAYPART_TOKENS)
    + r")"
    + r"(?:\s*[，,、]\s*"
    + r"(?:"
    + "|".join(re.escape(t) for t in _DAYPART_TOKENS)
    + r"))+"
    + r"[\s。．.]*$"
)

_ABOUT_DAYS = re.compile(r"关于.+的\s*\d+\s*天")


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip())
    t = re.sub(r"[\s·•._\-—–]+", "", t)
    return t.lower()


def is_unsafe_share_copy(
    text: str | None,
    *,
    title: str | None = None,
    kind: str = "caption",
) -> bool:
    """True when text must not appear on share/reader surface."""
    raw = (text or "").strip()
    if not raw:
        return False
    for phrase in _BANNED_SUBSTRINGS:
        if phrase in raw:
            return True
    if _ABOUT_DAYS.search(raw):
        return True
    if _WEAK_ENUM.match(raw):
        return True
    # 标题复读填坑（仅图注/alt；hook 允许短题名）
    if kind in {"caption", "alt"} and title:
        if _norm(raw) == _norm(title) and len(_norm(raw)) >= 2:
            return True
    return False


def sanitize_share_copy(
    text: str | None,
    *,
    title: str | None = None,
    kind: str = "caption",
) -> str:
    """Return text unchanged or '' when unsafe (空优于假句)."""
    raw = (text or "").strip()
    if not raw:
        return ""
    if is_unsafe_share_copy(raw, title=title, kind=kind):
        return ""
    return raw
