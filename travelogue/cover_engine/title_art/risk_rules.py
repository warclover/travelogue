"""路线 C 标题风险规则（W0.5b / W0.5b+ 数据驱动）。

把已知高失败类标题在发起 API 之前短路到路线 B——省 15～28 秒白等，
**不替代** D-CAL-19 OCR 门禁。

覆盖：
- 标点被吞（「一路向西…」）
- 叠字形变（「一茶一饭间」）
- 汉字后再嵌阿拉伯数字（「重走318国道」· W0.5b 双采样均失败）
  ——纯数字开头+单位（「918公里」）实测稳定，不拦
"""

from __future__ import annotations

from travelogue.cover_engine.title_art.char_frequency import _is_han

#: 明确会触发「标点被吞 / 标点难生成」风险的字符（中英文常见标题标点）。
_RISKY_PUNCTUATION = frozenset(
    "·…—–-—～~!！?？,，.。:：;；'\"“”‘’（）()【】[]《》<>/\\|@#*&"
)


def title_has_risky_punctuation(text: str) -> bool:
    """标题是否含路线 C 已知高风险标点。"""
    return any(ch in _RISKY_PUNCTUATION for ch in text)


def title_has_repeated_hanzi(text: str) -> bool:
    """标题是否含「同一汉字出现 ≥2 次」（叠字风险，非必须相邻）。"""
    seen: set[str] = set()
    for ch in text:
        if not _is_han(ch):
            continue
        if ch in seen:
            return True
        seen.add(ch)
    return False


def title_has_risky_digit_mix(text: str) -> bool:
    """汉字出现后再嵌入阿拉伯数字（如「重走318国道」）→ 高风险。

    纯数字前缀 + 汉字单位（「918公里」）W0.5b 实测可过，不拦截。
    """
    seen_han = False
    for ch in text:
        if _is_han(ch):
            seen_han = True
        elif ch.isdigit() and seen_han:
            return True
    return False


def route_c_risk_reason(text: str) -> str | None:
    """若标题不应尝试路线 C，返回可读原因码；否则 ``None``。"""
    if title_has_risky_punctuation(text):
        return "punctuation"
    if title_has_repeated_hanzi(text):
        return "repeated_char"
    if title_has_risky_digit_mix(text):
        return "digit_mix"
    return None
