"""Agent 2 · LLM narrative fill (DeepSeek / DashScope)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from travelogue.config import get_config
from travelogue.llm.client import chat_completion, parse_json_content
from travelogue.llm.narrate_cache import read_cached, write_cached
from travelogue.services.narrate import (
    NarrateError,
    NarrateResult,
    _finalize_copy,
    _manifest_limits,
    _utc_now_iso,
)
from travelogue.curation.asset_caption import apply_caption_to_trip, chapter_caption_asset_ids, resolve_caption
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
7. lead 不要复述 chapter.title，不要以 chapter.title 开头，也不要写成“标题，地点。”这种格式。
8. 若 items[].skipCaption 为 true，不要输出该图的 caption。"""


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


def _narrative_field_errors(
    trip: dict,
    *,
    meta_only: bool = False,
    chapter_index: int | None = None,
) -> list[str]:
    errs = [e for e in validate_narrative(trip) if not e.startswith("WARN:")]
    if meta_only:
        errs = [e for e in errs if "chapters[" not in e]
    elif chapter_index is not None:
        prefix = f"chapters[{chapter_index}]"
        errs = [e for e in errs if prefix in e]
    lim = _manifest_limits()
    meta = trip.get("meta") or {}
    if meta_only or chapter_index is None:
        hook = meta.get("hook") or ""
        if hook and len(hook) > lim["hookMaxChars"]:
            errs.append(f"meta.hook exceeds {lim['hookMaxChars']} chars")
        epilogue = trip.get("epilogue") or ""
        if epilogue and len(epilogue) > lim["epilogueMaxChars"]:
            errs.append(f"epilogue exceeds {lim['epilogueMaxChars']} chars")
    if chapter_index is None and not meta_only:
        chapters = trip.get("chapters") or []
        for i, ch in enumerate(chapters):
            lead = ch.get("lead") or ""
            if lead and len(lead) > lim["chapterLeadMaxChars"]:
                errs.append(f"chapters[{i}].lead exceeds {lim['chapterLeadMaxChars']} chars")
            for j, it in enumerate(ch.get("items") or []):
                cap = it.get("caption") or ""
                if cap and len(cap) > 60:
                    errs.append(f"chapters[{i}].items[{j}].caption too long")
    elif chapter_index is not None:
        chapters = trip.get("chapters") or []
        if chapter_index < len(chapters):
            ch = chapters[chapter_index]
            lead = ch.get("lead") or ""
            if lead and len(lead) > lim["chapterLeadMaxChars"]:
                errs.append(f"chapters[{chapter_index}].lead exceeds {lim['chapterLeadMaxChars']} chars")
            for j, it in enumerate(ch.get("items") or []):
                cap = it.get("caption") or ""
                if cap and len(cap) > 60:
                    errs.append(f"chapters[{chapter_index}].items[{j}].caption too long")
    return errs


def _stub_lead_for_chapter(
    trip: dict,
    chapter: dict,
    *,
    tone: str,
    lead_seen: set[str],
) -> str:
    from travelogue.services.narrate import _build_lead

    meta = trip.get("meta") or {}
    assets = {a["id"]: a for a in trip.get("assets") or []}
    places = meta.get("places") or ["旅途"]
    chapters = trip.get("chapters") or []
    idx = int(chapter.get("index") or 0)
    lim = _manifest_limits()
    return _finalize_copy(
        _build_lead(
            chapter,
            assets=assets,
            default_place=places[0],
            tone=tone,
            chapter_index=idx,
            chapter_total=len(chapters),
        ),
        lim["chapterLeadMaxChars"],
        seen=lead_seen,
    )


def _needs_meta(trip: dict, *, regenerate: bool = False) -> bool:
    meta = trip.get("meta") or {}
    if meta.get("edited"):
        return bool(regenerate and not (trip.get("epilogue") or "").strip())
    need_hook = regenerate or not (meta.get("hook") or "").strip()
    need_epilogue = (
        regenerate or not (trip.get("epilogue") or "").strip()
    ) and len(trip.get("chapters") or []) >= 2
    return need_hook or need_epilogue


def _chapter_needs_copy(chapter: dict, trip: dict, *, regenerate: bool = False) -> bool:
    if chapter.get("edited"):
        return False
    if regenerate:
        return True
    if not (chapter.get("lead") or "").strip():
        return True
    assets = {a["id"]: a for a in trip.get("assets") or []}
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        if item and item.get("edited"):
            continue
        if not resolve_caption(item, assets.get(aid)).strip():
            return True
    return False


def _planned_fields(trip: dict, *, regenerate: bool = False) -> list[str]:
    fields: list[str] = []
    meta = trip.get("meta") or {}
    if not meta.get("edited") and (regenerate or not (meta.get("hook") or "").strip()):
        fields.append("meta.hook")
    assets = {a["id"]: a for a in trip.get("assets") or []}
    for ch in trip.get("chapters") or []:
        if ch.get("edited"):
            continue
        idx = ch.get("index")
        if regenerate or not (ch.get("lead") or "").strip():
            fields.append(f"chapters[{idx}].lead")
        item_by_asset = {
            it.get("assetId"): it
            for it in ch.get("items") or []
            if it.get("type") == "media-card" and it.get("assetId")
        }
        for aid in chapter_caption_asset_ids(ch):
            item = item_by_asset.get(aid)
            if item and item.get("edited"):
                continue
            if regenerate or not resolve_caption(item, assets.get(aid)).strip():
                fields.append(f"assets[{aid}].caption")
    if len(trip.get("chapters") or []) >= 2 and (
        regenerate or not (trip.get("epilogue") or "").strip()
    ):
        if not meta.get("edited"):
            fields.append("epilogue")
    return fields


def _apply_meta_payload(
    trip: dict, payload: dict[str, Any], *, regenerate: bool = False
) -> list[str]:
    updated: list[str] = []
    lim = _manifest_limits()
    meta = trip.setdefault("meta", {})
    if not meta.get("edited"):
        hook = (payload.get("meta") or {}).get("hook")
        if hook and (regenerate or not (meta.get("hook") or "").strip()):
            meta["hook"] = _finalize_copy(str(hook), lim["hookMaxChars"])
            updated.append("meta.hook")
    epilogue = payload.get("epilogue")
    if epilogue and (regenerate or not (trip.get("epilogue") or "").strip()):
        trip["epilogue"] = _finalize_copy(str(epilogue), lim["epilogueMaxChars"])
        updated.append("epilogue")
    return updated


def _apply_chapter_payload(
    trip: dict,
    chapter: dict,
    payload: dict[str, Any],
    *,
    lead_seen: set[str],
    regenerate: bool = False,
) -> list[str]:
    updated: list[str] = []
    lim = _manifest_limits()
    idx = chapter.get("index")
    if not chapter.get("edited"):
        lead = payload.get("lead")
        if lead and (regenerate or not (chapter.get("lead") or "").strip()):
            chapter["lead"] = _finalize_copy(
                str(lead),
                lim["chapterLeadMaxChars"],
                seen=lead_seen,
            )
            updated.append(f"chapters[{idx}].lead")
    captions = {it.get("assetId"): it.get("caption") for it in payload.get("items") or []}
    assets = {a["id"]: a for a in trip.get("assets") or []}
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        if item and item.get("edited"):
            continue
        if resolve_caption(item, assets.get(aid)).strip() and not regenerate:
            continue
        cap = captions.get(aid)
        if cap:
            final = _finalize_copy(str(cap), 60)
            updated.extend(apply_caption_to_trip(trip, aid, final))
    return updated


def _chat_for_brief(
    brief: dict[str, Any],
    *,
    scope: str,
    provider: str,
    model: str,
    cache_dir: Path | None,
    regenerate: bool,
    chat_fn: Callable[[list[dict[str, str]]], str] | None,
    messages: list[dict[str, str]],
) -> str:
    if cache_dir and not regenerate:
        cached = read_cached(
            cache_dir,
            provider=provider,
            model=model,
            scope=scope,
            brief=brief,
        )
        if cached is not None:
            return json.dumps(cached, ensure_ascii=False)
    if chat_fn is not None:
        content = chat_fn(messages)
    else:
        content = chat_completion(messages, provider=provider)
    if cache_dir:
        try:
            payload = parse_json_content(content)
            write_cached(
                cache_dir,
                provider=provider,
                model=model,
                scope=scope,
                brief=brief,
                payload=payload,
            )
        except NarrateError:
            pass
    return content


def run_llm_narrate(
    trip: dict,
    *,
    provider: str,
    tone: str | None = None,
    dry_run: bool = False,
    regenerate: bool = False,
    cache_dir: Path | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> NarrateResult:
    """Fill hook, leads, captions, epilogue via LLM (metadata brief only)."""
    meta = trip.setdefault("meta", {})
    if tone:
        meta["tone"] = tone if tone in ("relaxed", "documentary") else meta.get("tone", "relaxed")
    tone_val = meta.get("tone") or get_config().narrative.tone_default or "relaxed"

    planned = _planned_fields(trip, regenerate=regenerate)
    if dry_run:
        return NarrateResult(fields_updated=planned)

    if not planned:
        return NarrateResult(fields_updated=[])

    max_retries = get_config().narrative.max_auto_fix_retries
    lead_seen: set[str] = set()
    updated: list[str] = []
    rt_model = get_config().llm.model or provider

    if _needs_meta(trip, regenerate=regenerate):
        brief = build_meta_brief(trip, tone=tone_val, regenerate=regenerate)
        fix_errors: list[str] | None = None
        for attempt in range(max_retries + 1):
            prompt = _meta_user_prompt(brief, fix_errors=fix_errors)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
            content = _chat_for_brief(
                brief,
                scope="meta",
                provider=provider,
                model=rt_model,
                cache_dir=cache_dir,
                regenerate=regenerate,
                chat_fn=chat_fn,
                messages=messages,
            )
            payload = parse_json_content(content)
            before = deepcopy(trip)
            batch = _apply_meta_payload(trip, payload, regenerate=regenerate)
            errs = _narrative_field_errors(trip, meta_only=True)
            if not errs:
                updated.extend(batch)
                break
            trip.clear()
            trip.update(before)
            if attempt >= max_retries:
                raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
            fix_errors = errs

    chapters = trip.get("chapters") or []
    for ch_idx in range(len(chapters)):
        chapter = trip["chapters"][ch_idx]
        if not _chapter_needs_copy(chapter, trip, regenerate=regenerate):
            continue
        brief = build_chapter_brief(trip, chapter, tone=tone_val, regenerate=regenerate)
        ch_id = brief["chapter"]["id"]
        fix_errors = None
        last_payload: dict[str, Any] | None = None
        for attempt in range(max_retries + 1):
            chapter = trip["chapters"][ch_idx]
            prompt = _chapter_user_prompt(brief, fix_errors=fix_errors)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
            content = _chat_for_brief(
                brief,
                scope=f"chapter-{ch_id}",
                provider=provider,
                model=rt_model,
                cache_dir=cache_dir,
                regenerate=regenerate,
                chat_fn=chat_fn,
                messages=messages,
            )
            payload = parse_json_content(content)
            last_payload = payload
            if payload.get("chapterId") and payload.get("chapterId") != ch_id:
                if attempt >= max_retries:
                    raise NarrateError(
                        "E_NARRATE_PARSE",
                        f"chapterId mismatch: {payload.get('chapterId')}",
                    )
                fix_errors = [f"chapterId must be {ch_id!r}"]
                continue
            before = deepcopy(trip)
            batch = _apply_chapter_payload(
                trip, chapter, payload, lead_seen=lead_seen, regenerate=regenerate
            )
            errs = _narrative_field_errors(trip, chapter_index=ch_idx)
            if not errs:
                updated.extend(batch)
                break
            trip.clear()
            trip.update(before)
            if attempt >= max_retries:
                if any("VR-N04" in e for e in errs) and last_payload is not None:
                    chapter = trip["chapters"][ch_idx]
                    batch = _apply_chapter_payload(
                        trip,
                        chapter,
                        last_payload,
                        lead_seen=lead_seen,
                        regenerate=regenerate,
                    )
                    chapter["lead"] = _stub_lead_for_chapter(
                        trip, chapter, tone=tone_val, lead_seen=lead_seen
                    )
                    idx = chapter.get("index")
                    if f"chapters[{idx}].lead" not in batch:
                        batch.append(f"chapters[{idx}].lead")
                    stub_errs = _narrative_field_errors(trip, chapter_index=ch_idx)
                    if not stub_errs:
                        updated.extend(batch)
                        break
                raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
            fix_errors = errs

    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "copy_draft"
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
