"""Agent 2 · LLM narrative fill (DeepSeek / DashScope)."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Callable

from travelogue.config import get_config
from travelogue.llm.client import chat_completion, parse_json_content
from travelogue.services.narrate import (
    NarrateError,
    NarrateResult,
    _finalize_copy,
    _manifest_limits,
    _utc_now_iso,
)
from travelogue.services.narrative_brief import build_chapter_brief, build_meta_brief
from travelogue.services.narrative_validate import validate_narrative

SYSTEM_PROMPT = """你是旅行视觉游记的文案编辑。你只输出合法 JSON，不写 HTML。

规则：
1. 中文、短句；禁止流水账、公文腔和 AI 套话。
2. 严格遵守 brief.limits 字数上限（按字符计）。
3. 只写 brief 中 fieldsRequested 请求的字段；brief.existing 已有内容不要重复输出。
4. 地点、人物、事件必须来自 brief，禁止虚构未出现的境外城市或人物。
5. 禁用词：综上所述、值得一提的是、不可否认、众所周知、总而言之、美不胜收、令人难忘。
6. relaxed 语气可感官细节；documentary 语气偏时间地点事实，少用感叹号。
7. 若 items[].skipCaption 为 true，不要输出该图的 caption。"""


def _meta_user_prompt(brief: dict[str, Any], *, fix_errors: list[str] | None = None) -> str:
    parts = [
        "根据以下 brief 填写全书 meta 文案（hook 与 epilogue）。",
        "",
        "brief:",
        json.dumps(brief, ensure_ascii=False, indent=2),
        "",
        "outputSchema:",
        json.dumps(
            {"meta": {"hook": "string | null"}, "epilogue": "string | null"},
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "只返回 JSON，不要 markdown 代码块。",
    ]
    if fix_errors:
        parts.extend(["", "上次校验错误，请仅修正：", *[f"- {e}" for e in fix_errors]])
    return "\n".join(parts)


def _chapter_user_prompt(brief: dict[str, Any], *, fix_errors: list[str] | None = None) -> str:
    parts = [
        "根据以下 brief 填写单章 lead 与 media-card caption。",
        "",
        "brief:",
        json.dumps(brief, ensure_ascii=False, indent=2),
        "",
        "outputSchema:",
        json.dumps(
            {
                "chapterId": "string",
                "lead": "string",
                "items": [{"assetId": "string", "caption": "string | null"}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "只返回 JSON，不要 markdown 代码块。",
    ]
    if fix_errors:
        parts.extend(["", "上次校验错误，请仅修正：", *[f"- {e}" for e in fix_errors]])
    return "\n".join(parts)


def _narrative_field_errors(trip: dict) -> list[str]:
    errs = [e for e in validate_narrative(trip) if not e.startswith("WARN:")]
    lim = _manifest_limits()
    meta = trip.get("meta") or {}
    hook = meta.get("hook") or ""
    if hook and len(hook) > lim["hookMaxChars"]:
        errs.append(f"meta.hook exceeds {lim['hookMaxChars']} chars")
    epilogue = trip.get("epilogue") or ""
    if epilogue and len(epilogue) > lim["epilogueMaxChars"]:
        errs.append(f"epilogue exceeds {lim['epilogueMaxChars']} chars")
    for i, ch in enumerate(trip.get("chapters") or []):
        lead = ch.get("lead") or ""
        if lead and len(lead) > lim["chapterLeadMaxChars"]:
            errs.append(f"chapters[{i}].lead exceeds {lim['chapterLeadMaxChars']} chars")
        for j, it in enumerate(ch.get("items") or []):
            cap = it.get("caption") or ""
            if cap and len(cap) > 60:
                errs.append(f"chapters[{i}].items[{j}].caption too long")
    return errs


def _needs_meta(trip: dict) -> bool:
    meta = trip.get("meta") or {}
    if meta.get("edited"):
        return bool(not (trip.get("epilogue") or "").strip())
    need_hook = not (meta.get("hook") or "").strip()
    need_epilogue = not (trip.get("epilogue") or "").strip() and len(trip.get("chapters") or []) >= 2
    return need_hook or need_epilogue


def _chapter_needs_copy(chapter: dict) -> bool:
    if chapter.get("edited"):
        return False
    if not (chapter.get("lead") or "").strip():
        return True
    for item in chapter.get("items") or []:
        if item.get("type") != "media-card" or item.get("edited"):
            continue
        if not (item.get("caption") or "").strip():
            return True
    return False


def _planned_fields(trip: dict) -> list[str]:
    fields: list[str] = []
    meta = trip.get("meta") or {}
    if not meta.get("edited") and not (meta.get("hook") or "").strip():
        fields.append("meta.hook")
    for ch in trip.get("chapters") or []:
        if ch.get("edited"):
            continue
        idx = ch.get("index")
        if not (ch.get("lead") or "").strip():
            fields.append(f"chapters[{idx}].lead")
        for item in ch.get("items") or []:
            if (
                item.get("type") == "media-card"
                and not item.get("edited")
                and not (item.get("caption") or "").strip()
            ):
                fields.append(f"chapters[{idx}].items[{item.get('assetId')}].caption")
    if not (trip.get("epilogue") or "").strip() and len(trip.get("chapters") or []) >= 2:
        if not meta.get("edited"):
            fields.append("epilogue")
    return fields


def _apply_meta_payload(trip: dict, payload: dict[str, Any]) -> list[str]:
    updated: list[str] = []
    lim = _manifest_limits()
    meta = trip.setdefault("meta", {})
    if not meta.get("edited"):
        hook = (payload.get("meta") or {}).get("hook")
        if hook and not (meta.get("hook") or "").strip():
            meta["hook"] = _finalize_copy(str(hook), lim["hookMaxChars"])
            updated.append("meta.hook")
    epilogue = payload.get("epilogue")
    if epilogue and not (trip.get("epilogue") or "").strip():
        trip["epilogue"] = _finalize_copy(str(epilogue), lim["epilogueMaxChars"])
        updated.append("epilogue")
    return updated


def _apply_chapter_payload(
    trip: dict,
    chapter: dict,
    payload: dict[str, Any],
    *,
    lead_seen: set[str],
) -> list[str]:
    updated: list[str] = []
    lim = _manifest_limits()
    idx = chapter.get("index")
    if not chapter.get("edited") and not (chapter.get("lead") or "").strip():
        lead = payload.get("lead")
        if lead:
            chapter["lead"] = _finalize_copy(
                str(lead),
                lim["chapterLeadMaxChars"],
                seen=lead_seen,
            )
            updated.append(f"chapters[{idx}].lead")
    captions = {it.get("assetId"): it.get("caption") for it in payload.get("items") or []}
    for item in chapter.get("items") or []:
        if item.get("type") != "media-card" or item.get("edited"):
            continue
        if (item.get("caption") or "").strip():
            continue
        aid = item.get("assetId")
        cap = captions.get(aid)
        if cap:
            item["caption"] = _finalize_copy(str(cap), 60)
            updated.append(f"chapters[{idx}].items[{aid}].caption")
    return updated


def run_llm_narrate(
    trip: dict,
    *,
    provider: str,
    tone: str | None = None,
    dry_run: bool = False,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> NarrateResult:
    """Fill hook, leads, captions, epilogue via LLM (metadata brief only)."""
    meta = trip.setdefault("meta", {})
    if tone:
        meta["tone"] = tone if tone in ("relaxed", "documentary") else meta.get("tone", "relaxed")
    tone_val = meta.get("tone") or get_config().narrative.tone_default or "relaxed"

    planned = _planned_fields(trip)
    if dry_run:
        return NarrateResult(fields_updated=planned)

    if not planned:
        return NarrateResult(fields_updated=[])

    max_retries = get_config().narrative.max_auto_fix_retries
    lead_seen: set[str] = set()
    updated: list[str] = []

    def _chat(messages: list[dict[str, str]]) -> str:
        if chat_fn is not None:
            return chat_fn(messages)
        return chat_completion(messages, provider=provider)

    if _needs_meta(trip):
        brief = build_meta_brief(trip, tone=tone_val)
        fix_errors: list[str] | None = None
        for attempt in range(max_retries + 1):
            prompt = _meta_user_prompt(brief, fix_errors=fix_errors)
            content = _chat(
                [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
            )
            payload = parse_json_content(content)
            before = deepcopy(trip)
            batch = _apply_meta_payload(trip, payload)
            errs = _narrative_field_errors(trip)
            if not errs:
                updated.extend(batch)
                break
            trip.clear()
            trip.update(before)
            if attempt >= max_retries:
                raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
            fix_errors = errs

    for chapter in trip.get("chapters") or []:
        if not _chapter_needs_copy(chapter):
            continue
        brief = build_chapter_brief(trip, chapter, tone=tone_val)
        ch_id = brief["chapter"]["id"]
        fix_errors = None
        for attempt in range(max_retries + 1):
            prompt = _chapter_user_prompt(brief, fix_errors=fix_errors)
            content = _chat(
                [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
            )
            payload = parse_json_content(content)
            if payload.get("chapterId") and payload.get("chapterId") != ch_id:
                if attempt >= max_retries:
                    raise NarrateError(
                        "E_NARRATE_PARSE",
                        f"chapterId mismatch: {payload.get('chapterId')}",
                    )
                fix_errors = [f"chapterId must be {ch_id!r}"]
                continue
            before = deepcopy(trip)
            batch = _apply_chapter_payload(trip, chapter, payload, lead_seen=lead_seen)
            errs = _narrative_field_errors(trip)
            if not errs:
                updated.extend(batch)
                break
            trip.clear()
            trip.update(before)
            if attempt >= max_retries:
                raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
            fix_errors = errs

    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "copy_draft"
    rt_model = get_config().llm.model or provider
    pipe.setdefault("runs", []).append(
        {
            "runId": f"narrate-{_utc_now_iso()}",
            "agent": "storyteller",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": f"{provider}/{rt_model}",
        }
    )
    trip["updatedAt"] = _utc_now_iso()
    return NarrateResult(fields_updated=updated)
