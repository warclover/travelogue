"""LLM decorLine candidate generation (K short lines from chapter brief)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.llm.client import chat_completion, parse_json_content
from travelogue.services.decor_line import (
    decor_line_facts_sufficient,
    validate_decor_line,
    _max_chars,
)
from travelogue.services.narrate import _finalize_copy
from travelogue.services.narrative_brief import build_chapter_decor_brief

DECOR_SYSTEM_PROMPT = """你是旅行视觉游记的章级点缀文案编辑。只输出合法 JSON。

规则：
1. 中文单句，每句 <= brief.limits.decorLineMaxChars 字。
2. 只使用 brief.chapter.facts / memoryAnchors / voiceExcerpts / copyIntent，禁止虚构。
3. 轻描淡写、事实优先；禁止解释照片意义、禁止导游词、禁止 AI 套话。
4. 禁用：综上所述、令人难忘、美不胜收、值得、美好、精彩。
5. 负向示例：不要「这次旅行令人难忘」；可「雨太大，先回酒店拿伞」。
6. 输出 K 个不同候选；质量不够可少写，但至少 1 个。"""


def _decor_user_prompt(brief: dict[str, Any], *, k: int) -> str:
    return "\n".join(
        [
            f"根据 brief 生成 {k} 条章级 decorLine 候选（单句、互不相同）。",
            "",
            "brief:",
            json.dumps(brief, ensure_ascii=False, indent=2),
            "",
            "outputSchema:",
            json.dumps({"candidates": ["string"]}, ensure_ascii=False, indent=2),
            "",
            "只返回 JSON，不要 markdown 代码块。",
        ]
    )


def should_call_llm_decor(chapter: dict, trip: dict, *, cfg: AppConfig | None = None) -> bool:
    app_cfg = cfg or get_config()
    nar = app_cfg.narrative
    if not nar.decor_line_llm_enabled:
        return False
    if not decor_line_facts_sufficient(chapter, trip, cfg=app_cfg):
        return False
    if nar.decor_line_voice_first:
        from travelogue.services.decor_line import chapter_has_voice, voice_decor_candidates

        if chapter_has_voice(chapter, trip):
            voice_cands = voice_decor_candidates(chapter, trip, cfg=app_cfg)
            if voice_cands:
                return False
    return True


def generate_llm_decor_line_candidates(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> list[str]:
    app_cfg = cfg or get_config()
    if not should_call_llm_decor(chapter, trip, cfg=app_cfg):
        return []
    k = max(1, int(app_cfg.narrative.decor_line_candidates or 3))
    brief = build_chapter_decor_brief(trip, chapter, cfg=app_cfg)
    messages = [
        {"role": "system", "content": DECOR_SYSTEM_PROMPT},
        {"role": "user", "content": _decor_user_prompt(brief, k=k)},
    ]
    if chat_fn:
        content = chat_fn(messages)
    else:
        content = chat_completion(messages, temperature=0.4)
    payload = parse_json_content(content)
    raw = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return []
    max_chars = _max_chars(app_cfg)
    cleaned: list[str] = []
    for item in raw:
        text = _finalize_copy(str(item or ""), max_chars)
        if not text or text in cleaned:
            continue
        if validate_decor_line(text, chapter, cfg=app_cfg):
            continue
        cleaned.append(text)
        if len(cleaned) >= k:
            break
    return cleaned
