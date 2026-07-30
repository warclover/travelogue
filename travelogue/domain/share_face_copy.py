"""Share-Face Closeout W0 · 分享面文案护栏（空优于假句 · D-SFC-01/02）。

供 narrate 写入与 render 读取共用，禁止说明书腔 / 弱枚举 / 标题复读上分享面。
"""

from __future__ import annotations

import re
import unicodedata

# 说明书腔 / 构图假句 / 示例泄漏（子串命中即空 · SFI 并入同一表，非第三套）
_BANNED_SUBSTRINGS: tuple[str, ...] = (
    "竖幅",
    "横幅",
    "抬头看见",
    "慢慢翻",
    "碎片拼成",
    "下次再见",
    "示例游记",
    "--",  # 裸脏分隔（如「武大--米娜」）· D-SFI-01 工程串
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
    # 标题复读填坑（图注/alt/封面 lead·hook；空优于题名回声）
    if kind in {"caption", "alt", "lead"} and title:
        t = title.strip()
        if _norm(raw) == _norm(t) and len(_norm(raw)) >= 2:
            return True
        # SFP D-SFP-05 · 「5月27日 · 杂志题名」式回声
        if t and len(t) >= 2 and t in raw:
            remainder = raw.replace(t, "", 1).strip(" ·•._-—–")
            if not remainder or re.fullmatch(
                r"\d{1,2}月\d{1,2}日(?:\s*[–—\-~～]\s*\d{1,2}(?:月\d{1,2}日)?)?",
                remainder,
            ):
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


def sanitize_share_copy_tracked(
    text: str | None,
    *,
    title: str | None = None,
    kind: str = "caption",
    edited: bool = False,
) -> tuple[str, bool]:
    """Sanitize with optional edited exemption; return (text, blanked).

    ``edited=True`` 粗豁免：对象级手改不过滤（编辑面可保留原文）。
    """
    raw = (text or "").strip()
    if not raw:
        return "", False
    if edited:
        return raw, False
    if is_unsafe_share_copy(raw, title=title, kind=kind):
        # SFP §7 · 题名回声类 blank 单独记一笔（其它禁词仍走 sfc_stub_blanked）
        if kind in {"caption", "alt", "lead"} and title and str(title).strip():
            t = str(title).strip()
            if t in raw or _norm(raw) == _norm(t):
                try:
                    from travelogue.domain.share_face_purity import emit_sfp_event

                    emit_sfp_event(
                        "sfp_caption_echo_suppressed",
                        {"kind": kind, "titleLen": len(t)},
                    )
                except Exception:
                    pass
        return "", True
    return raw, False


def record_stub_hit(
    *,
    surface: str,
    field: str,
    pattern_id: str | None = None,
    trip_id: str | None = None,
) -> None:
    """Emit render-side stub blank telemetry (D-SFI-01 · AC-SFI-01)."""
    try:
        from travelogue.domain.studio_events import append_studio_homepage_event

        meta: dict[str, str] = {"surface": surface, "field": field}
        if pattern_id:
            meta["pattern_id"] = pattern_id
        if trip_id:
            meta["trip_id"] = trip_id
        append_studio_homepage_event("stub_hits", meta)
        append_studio_homepage_event("sfc_stub_blanked", meta)
    except Exception:
        # Telemetry must never break render
        pass
