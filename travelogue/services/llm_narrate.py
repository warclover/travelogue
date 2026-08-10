"""Agent 2 · LLM narrative fill (DeepSeek / DashScope)."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.curation.asset_caption import (
    apply_caption_to_trip,
    asset_skips_caption,
    chapter_caption_asset_ids,
    resolve_caption,
)
from travelogue.llm.client import chat_completion, parse_json_content
from travelogue.llm.narrate_cache import read_cached, write_cached
from travelogue.services.errors import NarrateError
from travelogue.services.narrate import (
    NarrateResult,
    _finalize_copy,
    _manifest_limits,
    _utc_now_iso,
)
from travelogue.services.narrative_brief import build_chapter_brief, build_meta_brief
from travelogue.services.narrative_scope import (
    captions_allowed,
    chapter_lead_allowed,
    resolve_narrative_scope,
)
from travelogue.services.narrative_validate import validate_narrative

SYSTEM_PROMPT = """你是旅行视觉游记的文案编辑。你只输出合法 JSON，不写 HTML。

规则：
1. 中文、短句；禁止流水账、公文腔和 AI 套话。
2. 严格遵守 brief.limits 字数上限（按字符计）。
3. 只写 brief 中 fieldsRequested 请求的字段；brief.existing 已有内容不要重复输出。
4. 地点、人物、事件必须来自 brief；优先用 trip.editorialSubject 作为全书主语（杂志名/主题）。若 placesUserSet 为 false，不要用 trip.places 或 EXIF 城市覆盖 editorialSubject。
5. 禁用词：综上所述、值得一提的是、不可否认、众所周知、总而言之、美不胜收、令人难忘、值得、美好、精彩。
6. relaxed 语气可感官细节；documentary 语气偏时间地点事实，少用感叹号。
7. lead 不要复述 chapter.title，不要以 chapter.title 开头，也不要写成“标题，地点。”这种格式。
8. 若 brief 中 items[].skipCaption 为 true（或 assets[].skipCaption），不要输出该图的 caption。
9. 负向示例：不要写「这次旅行令人难忘」；可写「雨太大，先回酒店拿伞」。
10. 禁止解释照片意义，禁止导游词；caption 优先精简 voiceExcerpt。"""


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
    cfg: AppConfig | None = None,
) -> list[str]:
    errs = [e for e in validate_narrative(trip, cfg=cfg) if not e.startswith("WARN:")]
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
    from travelogue.services.copy_subject import narrative_copy_subject
    from travelogue.services.narrate import _build_lead

    meta = trip.get("meta") or {}
    intent = trip.get("intent")
    asset_list = trip.get("assets") or []
    assets = {a["id"]: a for a in asset_list}
    chapters = trip.get("chapters") or []
    idx = int(chapter.get("index") or 0)
    lim = _manifest_limits()
    return _finalize_copy(
        _build_lead(
            chapter,
            meta=meta,
            intent=intent,
            assets=assets,
            default_place=narrative_copy_subject(meta, intent=intent, assets=asset_list),
            tone=tone,
            chapter_index=idx,
            chapter_total=len(chapters),
        ),
        lim["chapterLeadMaxChars"],
        seen=lead_seen,
    )


def _needs_meta(trip: dict, *, regenerate: bool = False) -> bool:
    from travelogue.domain.copy_origin import is_user_protected

    meta = trip.get("meta") or {}
    hook_locked = is_user_protected(meta, "hookOrigin")
    epi_locked = (
        str(trip.get("epilogueOrigin") or "").strip().lower() == "user" or meta.get("edited")
    )
    need_hook = (not hook_locked) and (regenerate or not (meta.get("hook") or "").strip())
    need_epilogue = (
        (not epi_locked)
        and (regenerate or not (trip.get("epilogue") or "").strip())
        and len(trip.get("chapters") or []) >= 2
    )
    return need_hook or need_epilogue


def _find_chapter_index(trip: dict, chapter_id: str) -> int | None:
    for i, ch in enumerate(trip.get("chapters") or []):
        if ch.get("id") == chapter_id:
            return i
    return None


def _chapter_indices(trip: dict, chapter_id: str | None) -> list[int]:
    chapters = trip.get("chapters") or []
    if not chapter_id:
        return list(range(len(chapters)))
    idx = _find_chapter_index(trip, chapter_id)
    if idx is None:
        raise NarrateError("E_NARRATE_CHAPTER", f"unknown chapter {chapter_id!r}")
    return [idx]


def _chapter_needs_copy(
    chapter: dict,
    trip: dict,
    *,
    regenerate: bool = False,
    scope: str = "frame",
) -> bool:
    from travelogue.domain.copy_origin import is_user_protected

    chapters = trip.get("chapters") or []
    lead_locked = is_user_protected(chapter, "leadOrigin")
    need_lead = (
        (not lead_locked)
        and chapter_lead_allowed(chapter, chapters, scope)
        and (regenerate or not (chapter.get("lead") or "").strip())
    )
    if need_lead:
        return True
    if not captions_allowed(scope):
        return False
    assets = {a["id"]: a for a in trip.get("assets") or []}
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        asset = assets.get(aid)
        if is_user_protected(item, "captionOrigin") or is_user_protected(asset, "captionOrigin"):
            continue
        if asset_skips_caption(asset) and not regenerate:
            continue
        if regenerate or not resolve_caption(item, asset).strip():
            return True
    return False


def _planned_fields(
    trip: dict,
    *,
    regenerate: bool = False,
    chapter_id: str | None = None,
    scope: str | None = None,
    cfg: AppConfig | None = None,
) -> list[str]:
    from travelogue.domain.copy_origin import is_user_protected

    scope_val = resolve_narrative_scope(override=scope, cfg=cfg)
    fields: list[str] = []
    meta = trip.get("meta") or {}
    chapters = trip.get("chapters") or []
    if (
        not chapter_id
        and not is_user_protected(meta, "hookOrigin")
        and (regenerate or not (meta.get("hook") or "").strip())
    ):
        fields.append("meta.hook")
    assets = {a["id"]: a for a in trip.get("assets") or []}
    for ch in chapters:
        if chapter_id and ch.get("id") != chapter_id:
            continue
        idx = ch.get("index")
        if (
            not is_user_protected(ch, "leadOrigin")
            and chapter_lead_allowed(ch, chapters, scope_val)
            and (regenerate or not (ch.get("lead") or "").strip())
        ):
            fields.append(f"chapters[{idx}].lead")
        if not captions_allowed(scope_val):
            continue
        item_by_asset = {
            it.get("assetId"): it
            for it in ch.get("items") or []
            if it.get("type") == "media-card" and it.get("assetId")
        }
        for aid in chapter_caption_asset_ids(ch):
            item = item_by_asset.get(aid)
            asset = assets.get(aid)
            if is_user_protected(item, "captionOrigin") or is_user_protected(asset, "captionOrigin"):
                continue
            if asset_skips_caption(asset) and not regenerate:
                continue
            if regenerate or not resolve_caption(item, asset).strip():
                fields.append(f"assets[{aid}].caption")
    epi_locked = (
        str(trip.get("epilogueOrigin") or "").strip().lower() == "user"
        or (meta.get("edited") and (trip.get("epilogue") or "").strip())
    )
    if (
        not chapter_id
        and not epi_locked
        and len(chapters) >= 2
        and (regenerate or not (trip.get("epilogue") or "").strip())
    ):
        fields.append("epilogue")
    return fields


def _apply_meta_payload(
    trip: dict, payload: dict[str, Any], *, regenerate: bool = False
) -> list[str]:
    from travelogue.domain.copy_origin import ORIGIN_LLM, is_user_protected

    updated: list[str] = []
    lim = _manifest_limits()
    meta = trip.setdefault("meta", {})
    if not is_user_protected(meta, "hookOrigin"):
        hook = (payload.get("meta") or {}).get("hook")
        if hook and (regenerate or not (meta.get("hook") or "").strip()):
            meta["hook"] = _finalize_copy(str(hook), lim["hookMaxChars"])
            meta["hookOrigin"] = ORIGIN_LLM
            updated.append("meta.hook")
    epi_locked = str(trip.get("epilogueOrigin") or "").strip().lower() == "user"
    epilogue = payload.get("epilogue")
    if (
        not epi_locked
        and epilogue
        and (regenerate or not (trip.get("epilogue") or "").strip())
    ):
        trip["epilogue"] = _finalize_copy(str(epilogue), lim["epilogueMaxChars"])
        trip["epilogueOrigin"] = ORIGIN_LLM
        updated.append("epilogue")
    return updated


def _apply_chapter_payload(
    trip: dict,
    chapter: dict,
    payload: dict[str, Any],
    *,
    lead_seen: set[str],
    regenerate: bool = False,
    scope: str = "frame",
) -> list[str]:
    from travelogue.domain.copy_origin import ORIGIN_LLM, is_user_protected

    updated: list[str] = []
    lim = _manifest_limits()
    idx = chapter.get("index")
    chapters = trip.get("chapters") or []
    if (
        not is_user_protected(chapter, "leadOrigin")
        and chapter_lead_allowed(chapter, chapters, scope)
    ):
        lead = payload.get("lead")
        if lead and (regenerate or not (chapter.get("lead") or "").strip()):
            chapter["lead"] = _finalize_copy(
                str(lead),
                lim["chapterLeadMaxChars"],
                seen=lead_seen,
            )
            chapter["leadOrigin"] = ORIGIN_LLM
            updated.append(f"chapters[{idx}].lead")
    if not captions_allowed(scope):
        return updated
    captions = {it.get("assetId"): it.get("caption") for it in payload.get("items") or []}
    assets = {a["id"]: a for a in trip.get("assets") or []}
    item_by_asset = {
        it.get("assetId"): it
        for it in chapter.get("items") or []
        if it.get("type") == "media-card" and it.get("assetId")
    }
    for aid in chapter_caption_asset_ids(chapter):
        item = item_by_asset.get(aid)
        asset = assets.get(aid)
        if is_user_protected(item, "captionOrigin") or is_user_protected(asset, "captionOrigin"):
            continue
        if asset_skips_caption(asset) and not regenerate:
            continue
        if resolve_caption(item, asset).strip() and not regenerate:
            continue
        cap = captions.get(aid)
        if cap:
            final = _finalize_copy(str(cap), 60)
            updated.extend(apply_caption_to_trip(trip, aid, final))
            target = item if item is not None else asset
            if isinstance(target, dict):
                target["captionOrigin"] = ORIGIN_LLM
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
    stats: dict[str, int] | None = None,
    stats_lock: Any | None = None,
    shared_backoff: bool = False,
    trip: dict[str, Any] | None = None,
) -> str:
    from travelogue.ai.budget import budget_for_trip
    from travelogue.ai.gate import acp_instrumentation_active, check_gate
    from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call

    trip_id = ""
    if isinstance(trip, dict):
        trip_id = str(trip.get("tripId") or trip.get("id") or "")

    if cache_dir and not regenerate:
        cached = read_cached(
            cache_dir,
            provider=provider,
            model=model,
            scope=scope,
            brief=brief,
        )
        if cached is not None:
            if stats is not None:
                if stats_lock is not None:
                    with stats_lock:
                        stats["narrateCacheHits"] = stats.get("narrateCacheHits", 0) + 1
                else:
                    stats["narrateCacheHits"] = stats.get("narrateCacheHits", 0) + 1
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent="storyteller",
                    source="cache",
                    ok=True,
                    latency_ms=0.0,
                    model=f"{provider}/{model}",
                    reason="cache_hit",
                    trip_id=trip_id,
                ),
            )
            return json.dumps(cached, ensure_ascii=False)
    if stats is not None:
        if stats_lock is not None:
            with stats_lock:
                stats["narrateCacheMisses"] = stats.get("narrateCacheMisses", 0) + 1
        else:
            stats["narrateCacheMisses"] = stats.get("narrateCacheMisses", 0) + 1

    active = acp_instrumentation_active()
    if active:
        decision = check_gate()
        if not decision.allow:
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent="storyteller",
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=f"{provider}/{model}",
                    reason=decision.reason,
                    trip_id=trip_id,
                ),
            )
            raise NarrateError(f"ACP gate blocked narrate: {decision.reason}")
        budget = budget_for_trip(trip_id)
        if not budget.try_consume("storyteller"):
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent="storyteller",
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=f"{provider}/{model}",
                    reason="budget_exceeded",
                    trip_id=trip_id,
                ),
            )
            raise NarrateError("ACP budget exceeded for narrate")

    err: BaseException | None = None
    content = ""
    with timed_call() as clock:
        try:
            if chat_fn is not None:
                if shared_backoff:
                    from travelogue.llm.shared_backoff import get_shared_backoff

                    get_shared_backoff().wait_turn()
                content = chat_fn(messages)
            else:
                content = chat_completion(
                    messages, provider=provider, shared_backoff=shared_backoff
                )
        except BaseException as exc:  # noqa: BLE001 — re-raised after telemetry
            err = exc
    record_agent_call(
        trip,
        AgentCallRecord(
            agent="storyteller",
            source="llm",
            ok=err is None,
            latency_ms=clock.latency_ms,
            model=f"{provider}/{model}",
            reason="ok" if err is None else "exception",
            trip_id=trip_id,
            started_at=clock.started_at,
            finished_at=clock.finished_at,
        ),
    )
    if err is not None:
        raise err
    if not active:
        budget_for_trip(trip_id).force_count(1)
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
            # D-ACP-06 · dual-write into unified ai.cache (narrate_cache remains primary)
            try:
                from pathlib import Path as _Path

                from travelogue.ai.cache import content_sig, write_cached as ai_write
                from travelogue.config import get_config

                acp = getattr(get_config(), "ai_capability", None)
                ai_dir = _Path(
                    getattr(getattr(acp, "cache", None), "dir", None) or ".cache/ai"
                )
                sig = content_sig(
                    {"provider": provider, "model": model, "scope": scope, "brief": brief},
                    prompt_version="narrate-dual",
                )
                ai_write(ai_dir, agent="narrate", sig=sig, payload=payload)
            except Exception:
                pass
        except NarrateError:
            pass
    return content


def _merge_narrate_timings(trip: dict, stats: dict[str, int]) -> None:
    from travelogue.domain.pipeline_view import pipeline_dict, set_pipeline_timings

    pipe = pipeline_dict(trip)
    timings = dict(pipe.get("timings") or {})
    for key in (
        "narrateConcurrency",
        "narrateCacheHits",
        "narrateCacheMisses",
        "narrateProviderBackoffCount",
    ):
        if key in stats:
            timings[key] = stats[key]
    set_pipeline_timings(trip, timings)


def _fetch_chapter_payload(
    *,
    trip: dict,
    ch_idx: int,
    brief: dict[str, Any],
    ch_id: str,
    provider: str,
    rt_model: str,
    cache_dir: Path | None,
    regenerate: bool,
    chat_fn: Callable[[list[dict[str, str]]], str] | None,
    max_retries: int,
    stats: dict[str, int],
    stats_lock: Any | None,
    shared_backoff: bool,
    fix_errors: list[str] | None = None,
) -> dict[str, Any]:
    """Chat + parse + chapterId check (no trip mutate). Raises NarrateError when exhausted."""
    errors = fix_errors
    for attempt in range(max_retries + 1):
        prompt = _chapter_user_prompt(brief, fix_errors=errors)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content = _chat_for_brief(
            brief,
            scope=f"chapter-{ch_id}",
            provider=provider,
            model=rt_model,
            cache_dir=cache_dir,
            regenerate=regenerate,
            chat_fn=chat_fn,
            messages=messages,
            stats=stats,
            stats_lock=stats_lock,
            shared_backoff=shared_backoff,
            trip=trip,
        )
        payload = parse_json_content(content)
        if payload.get("chapterId") and payload.get("chapterId") != ch_id:
            if attempt >= max_retries:
                raise NarrateError(
                    "E_NARRATE_PARSE",
                    f"chapterId mismatch: {payload.get('chapterId')}",
                )
            errors = [f"chapterId must be {ch_id!r}"]
            continue
        return payload
    raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "chapter payload fetch failed")


def _apply_chapter_with_validation(
    trip: dict,
    *,
    ch_idx: int,
    payload: dict[str, Any],
    lead_seen: set[str],
    regenerate: bool,
    scope_val: str,
    tone_val: str,
    app_cfg: AppConfig,
    brief: dict[str, Any],
    ch_id: str,
    provider: str,
    rt_model: str,
    cache_dir: Path | None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None,
    max_retries: int,
    stats: dict[str, int],
    stats_lock: Any | None,
    shared_backoff: bool,
) -> list[str]:
    """Apply payload; on validation failure re-fetch with fix_errors (serial)."""
    last_payload: dict[str, Any] | None = payload
    fix_errors: list[str] | None = None
    working = payload
    for attempt in range(max_retries + 1):
        chapter = trip["chapters"][ch_idx]
        if attempt > 0:
            working = _fetch_chapter_payload(
                trip=trip,
                ch_idx=ch_idx,
                brief=brief,
                ch_id=ch_id,
                provider=provider,
                rt_model=rt_model,
                cache_dir=cache_dir,
                regenerate=regenerate,
                chat_fn=chat_fn,
                max_retries=max_retries,
                stats=stats,
                stats_lock=stats_lock,
                shared_backoff=shared_backoff,
                fix_errors=fix_errors,
            )
            last_payload = working
        before = deepcopy(trip)
        batch = _apply_chapter_payload(
            trip,
            chapter,
            working,
            lead_seen=lead_seen,
            regenerate=regenerate,
            scope=scope_val,
        )
        errs = _narrative_field_errors(trip, chapter_index=ch_idx, cfg=app_cfg)
        if not errs:
            return batch
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
                    scope=scope_val,
                )
                chapter["lead"] = _stub_lead_for_chapter(
                    trip, chapter, tone=tone_val, lead_seen=lead_seen
                )
                idx = chapter.get("index")
                if f"chapters[{idx}].lead" not in batch:
                    batch.append(f"chapters[{idx}].lead")
                stub_errs = _narrative_field_errors(trip, chapter_index=ch_idx, cfg=app_cfg)
                if not stub_errs:
                    return batch
            raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
        fix_errors = errs
    raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "chapter apply failed")


def _narrate_chapters_serial(
    trip: dict,
    *,
    chapter_indices: list[int],
    tone_val: str,
    scope_val: str,
    regenerate: bool,
    provider: str,
    rt_model: str,
    cache_dir: Path | None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None,
    max_retries: int,
    app_cfg: AppConfig,
    lead_seen: set[str],
    stats: dict[str, int],
    stats_lock: Any | None,
    shared_backoff: bool,
) -> list[str]:
    updated: list[str] = []
    for ch_idx in chapter_indices:
        chapter = trip["chapters"][ch_idx]
        brief = build_chapter_brief(
            trip, chapter, tone=tone_val, regenerate=regenerate, scope=scope_val
        )
        ch_id = brief["chapter"]["id"]
        payload = _fetch_chapter_payload(
            trip=trip,
            ch_idx=ch_idx,
            brief=brief,
            ch_id=ch_id,
            provider=provider,
            rt_model=rt_model,
            cache_dir=cache_dir,
            regenerate=regenerate,
            chat_fn=chat_fn,
            max_retries=max_retries,
            stats=stats,
            stats_lock=stats_lock,
            shared_backoff=shared_backoff,
        )
        batch = _apply_chapter_with_validation(
            trip,
            ch_idx=ch_idx,
            payload=payload,
            lead_seen=lead_seen,
            regenerate=regenerate,
            scope_val=scope_val,
            tone_val=tone_val,
            app_cfg=app_cfg,
            brief=brief,
            ch_id=ch_id,
            provider=provider,
            rt_model=rt_model,
            cache_dir=cache_dir,
            chat_fn=chat_fn,
            max_retries=max_retries,
            stats=stats,
            stats_lock=stats_lock,
            shared_backoff=shared_backoff,
        )
        updated.extend(batch)
    return updated


def _narrate_chapters_concurrent(
    trip: dict,
    *,
    chapter_indices: list[int],
    concurrency: int,
    tone_val: str,
    scope_val: str,
    regenerate: bool,
    provider: str,
    rt_model: str,
    cache_dir: Path | None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None,
    max_retries: int,
    app_cfg: AppConfig,
    lead_seen: set[str],
    stats: dict[str, int],
    stats_lock: Any | None,
    shared_backoff: bool,
) -> list[str]:
    """Fetch chapter payloads concurrently; apply in chapter-index ascending order."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    briefs: dict[int, dict[str, Any]] = {}
    for ch_idx in chapter_indices:
        chapter = trip["chapters"][ch_idx]
        briefs[ch_idx] = build_chapter_brief(
            trip, chapter, tone=tone_val, regenerate=regenerate, scope=scope_val
        )

    payloads: dict[int, dict[str, Any]] = {}
    errors: dict[int, BaseException] = {}

    def _job(ch_idx: int) -> tuple[int, dict[str, Any]]:
        brief = briefs[ch_idx]
        ch_id = brief["chapter"]["id"]
        payload = _fetch_chapter_payload(
            trip=trip,
            ch_idx=ch_idx,
            brief=brief,
            ch_id=ch_id,
            provider=provider,
            rt_model=rt_model,
            cache_dir=cache_dir,
            regenerate=regenerate,
            chat_fn=chat_fn,
            max_retries=max_retries,
            stats=stats,
            stats_lock=stats_lock,
            shared_backoff=shared_backoff,
        )
        return ch_idx, payload

    workers = max(1, min(concurrency, len(chapter_indices)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_job, idx): idx for idx in chapter_indices}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                ch_idx, payload = fut.result()
                payloads[ch_idx] = payload
            except BaseException as exc:  # noqa: BLE001 — collect then fail whole narrate
                errors[idx] = exc

    if errors:
        # Preserve whole-segment failure semantics (D-PT-06).
        first = errors[min(errors)]
        if isinstance(first, NarrateError):
            raise first
        raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", str(first)) from first

    updated: list[str] = []
    for ch_idx in sorted(chapter_indices):
        brief = briefs[ch_idx]
        ch_id = brief["chapter"]["id"]
        batch = _apply_chapter_with_validation(
            trip,
            ch_idx=ch_idx,
            payload=payloads[ch_idx],
            lead_seen=lead_seen,
            regenerate=regenerate,
            scope_val=scope_val,
            tone_val=tone_val,
            app_cfg=app_cfg,
            brief=brief,
            ch_id=ch_id,
            provider=provider,
            rt_model=rt_model,
            cache_dir=cache_dir,
            chat_fn=chat_fn,
            max_retries=max_retries,
            stats=stats,
            stats_lock=stats_lock,
            shared_backoff=shared_backoff,
        )
        updated.extend(batch)
    return updated


def run_llm_narrate(
    trip: dict,
    *,
    provider: str,
    tone: str | None = None,
    dry_run: bool = False,
    regenerate: bool = False,
    cache_dir: Path | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    chapter_id: str | None = None,
    scope: str | None = None,
    cfg: AppConfig | None = None,
) -> NarrateResult:
    """
    Fill hook, leads, captions, epilogue via LLM (metadata brief only).

    Prefer ``run_narrate`` as the entry point: it runs scope cleanup and writes
    ``curation.narrativeScope``. This function only persists ``narrativeScope``
    (no cleanup) when ``dry_run`` is false.

    Chapter LLM calls may run concurrently when ``llm.narrate_concurrency > 1``;
    payloads are always applied in chapter-index order (lead_seen).
    """
    from travelogue.domain.copy_origin import migrate_edited_to_origin
    from travelogue.llm.shared_backoff import get_shared_backoff

    scope_val = resolve_narrative_scope(override=scope, cfg=cfg)
    if not dry_run:
        trip.setdefault("curation", {})["narrativeScope"] = scope_val
    if chapter_id:
        _chapter_indices(trip, chapter_id)
    # BE-SFI-00 · promote legacy edited → field origin before planning skips
    migrate_edited_to_origin(trip)
    meta = trip.setdefault("meta", {})
    if tone:
        meta["tone"] = tone if tone in ("relaxed", "documentary") else meta.get("tone", "relaxed")
    app_cfg = cfg or get_config()
    tone_val = meta.get("tone") or app_cfg.narrative.tone_default or "relaxed"

    planned = _planned_fields(
        trip, regenerate=regenerate, chapter_id=chapter_id, scope=scope_val, cfg=app_cfg
    )
    if dry_run:
        return NarrateResult(fields_updated=planned)

    if not planned:
        return NarrateResult(fields_updated=[])

    max_retries = app_cfg.narrative.max_auto_fix_retries
    lead_seen: set[str] = set()
    updated: list[str] = []
    rt_model = app_cfg.llm.model or provider
    concurrency = max(1, min(8, int(app_cfg.llm.narrate_concurrency or 1)))
    shared_backoff = bool(app_cfg.llm.narrate_concurrency_backoff)
    stats: dict[str, int] = {
        "narrateConcurrency": 1,
        "narrateCacheHits": 0,
        "narrateCacheMisses": 0,
        "narrateProviderBackoffCount": 0,
    }
    stats_lock = threading.Lock()
    backoff_before = get_shared_backoff().backoff_count

    if not chapter_id and _needs_meta(trip, regenerate=regenerate):
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
                stats=stats,
                stats_lock=stats_lock,
                shared_backoff=shared_backoff,
                trip=trip,
            )
            payload = parse_json_content(content)
            before = deepcopy(trip)
            batch = _apply_meta_payload(trip, payload, regenerate=regenerate)
            errs = _narrative_field_errors(trip, meta_only=True, cfg=app_cfg)
            if not errs:
                updated.extend(batch)
                break
            trip.clear()
            trip.update(before)
            if attempt >= max_retries:
                raise NarrateError("E_NARRATE_RETRY_EXHAUSTED", "; ".join(errs[:3]))
            fix_errors = errs

    chapter_indices = [
        ch_idx
        for ch_idx in _chapter_indices(trip, chapter_id)
        if _chapter_needs_copy(
            trip["chapters"][ch_idx], trip, regenerate=regenerate, scope=scope_val
        )
    ]

    if chapter_indices:
        # AC-PT-06: concurrency=1 (or single chapter) keeps the serial path.
        if concurrency <= 1 or len(chapter_indices) <= 1:
            stats["narrateConcurrency"] = 1
            updated.extend(
                _narrate_chapters_serial(
                    trip,
                    chapter_indices=chapter_indices,
                    tone_val=tone_val,
                    scope_val=scope_val,
                    regenerate=regenerate,
                    provider=provider,
                    rt_model=rt_model,
                    cache_dir=cache_dir,
                    chat_fn=chat_fn,
                    max_retries=max_retries,
                    app_cfg=app_cfg,
                    lead_seen=lead_seen,
                    stats=stats,
                    stats_lock=stats_lock,
                    shared_backoff=shared_backoff,
                )
            )
        else:
            stats["narrateConcurrency"] = concurrency
            updated.extend(
                _narrate_chapters_concurrent(
                    trip,
                    chapter_indices=chapter_indices,
                    concurrency=concurrency,
                    tone_val=tone_val,
                    scope_val=scope_val,
                    regenerate=regenerate,
                    provider=provider,
                    rt_model=rt_model,
                    cache_dir=cache_dir,
                    chat_fn=chat_fn,
                    max_retries=max_retries,
                    app_cfg=app_cfg,
                    lead_seen=lead_seen,
                    stats=stats,
                    stats_lock=stats_lock,
                    shared_backoff=shared_backoff,
                )
            )

    stats["narrateProviderBackoffCount"] = max(
        0, get_shared_backoff().backoff_count - backoff_before
    )
    _merge_narrate_timings(trip, stats)

    from travelogue.services.pipeline_state import append_pipeline_run, set_pipeline_status

    set_pipeline_status(trip, "copy_draft")
    append_pipeline_run(
        trip,
        {
            "runId": f"narrate-{_utc_now_iso()}",
            "agent": "storyteller",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": f"{provider}/{rt_model}",
        },
    )
    trip["updatedAt"] = _utc_now_iso()
    return NarrateResult(fields_updated=updated)
