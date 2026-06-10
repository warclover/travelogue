"""Phase 11 · chapter decorLine generation (rule-based + optional LLM brief)."""

from __future__ import annotations

import re
from collections.abc import Callable

from travelogue.config import AppConfig, get_config
from travelogue.services.narrate import BANNED_PHRASES, _finalize_copy

_DECOR_BANNED = BANNED_PHRASES + (
    "综上所述",
    "值得一提的是",
    "令人难忘",
    "美不胜收",
    "众所周知",
)

MOOD_VALUES = frozenset({"松弛", "热闹", "赶路", "意外", "仪式感", "平静"})
FOCUS_VALUES = frozenset({"人", "地方", "食物", "关系", "自我感受"})

_GENERIC_RE = re.compile(
    r"(值得|难忘|美好|精彩|瞬间|回忆|旅程|旅行|风景|照片|记录)",
)

_TAG_STUB_RE = re.compile(
    r"(?:^person\s*·|\bface\s*·|[，,]\s*photo[。.]?$)",
    re.IGNORECASE,
)


def decor_line_is_tag_stub(line: str) -> bool:
    """True when decorLine is rule/tag stitch, not natural-language copy."""
    text = str(line or "").strip()
    if not text:
        return False
    if " · " in text:
        return True
    return bool(_TAG_STUB_RE.search(text))


def decor_line_config(cfg: AppConfig | None = None) -> AppConfig:
    return cfg or get_config()


def _max_chars(cfg: AppConfig) -> int:
    return max(1, min(30, int(cfg.narrative.decor_line_max_chars or 30)))


def _chapter_assets(chapter: dict, trip: dict) -> list[dict]:
    assets = {a["id"]: a for a in trip.get("assets") or []}
    out: list[dict] = []
    for it in chapter.get("items") or []:
        aid = it.get("assetId")
        if aid and aid in assets:
            out.append(assets[aid])
    for sc in chapter.get("screens") or []:
        for slot in sc.get("slots") or []:
            aid = slot.get("assetId")
            if aid and aid in assets and assets[aid] not in out:
                out.append(assets[aid])
    return out


def _chapter_voice_excerpts(chapter: dict, trip: dict) -> list[str]:
    out: list[str] = []
    for asset in _chapter_assets(chapter, trip):
        voice = asset.get("voice") or {}
        excerpt = (voice.get("transcriptPreview") or voice.get("transcript") or "").strip()
        if excerpt:
            out.append(excerpt[:120])
    return out


def chapter_has_voice(chapter: dict, trip: dict) -> bool:
    return bool(_chapter_voice_excerpts(chapter, trip))


def extract_chapter_facts(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> list[str]:
    """Event-oriented facts; voice and anchors precede visual tags."""
    app_cfg = decor_line_config(cfg)
    facts: list[str] = []
    curation = chapter.get("curation") or {}

    for excerpt in _chapter_voice_excerpts(chapter, trip):
        facts.append(excerpt)

    for anchor in curation.get("memoryAnchors") or []:
        text = str(anchor or "").strip()
        if text:
            facts.append(text)

    intent = _copy_intent(chapter)
    note = intent.get("note", "")
    if note:
        facts.append(note)

    for place in curation.get("places") or []:
        text = str(place or "").strip()
        if text:
            facts.append(text)

    if app_cfg.narrative.decor_line_visual_facts_enabled:
        from travelogue.services.visual_facts import extract_visual_facts

        facts.extend(extract_visual_facts(chapter, trip))

    tag_counts: dict[str, int] = {}
    cities: set[str] = set()
    for asset in _chapter_assets(chapter, trip):
        for tag in asset.get("tags") or []:
            t = str(tag or "").strip()
            if t:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        city = (asset.get("place") or {}).get("city")
        if city:
            cities.add(str(city).strip())

    for tag, _ in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:4]:
        facts.append(tag)
    facts.extend(sorted(cities)[:2])

    title = str(chapter.get("title") or "").strip()
    if title:
        facts.append(title)

    notes = (trip.get("intent") or {}).get("travelNotes")
    if notes:
        snippet = str(notes).strip()[:40]
        if snippet:
            facts.append(snippet)

    deduped: list[str] = []
    seen: set[str] = set()
    for f in facts:
        key = f.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)
    return deduped


def decor_line_facts_sufficient(chapter: dict, trip: dict, *, cfg: AppConfig | None = None) -> bool:
    """True when voice, anchor, intent note, or enough non-title facts exist."""
    app_cfg = decor_line_config(cfg)
    if chapter_has_voice(chapter, trip):
        return True
    curation = chapter.get("curation") or {}
    if any(str(a or "").strip() for a in (curation.get("memoryAnchors") or [])):
        return True
    if _copy_intent(chapter).get("note"):
        return True
    title = str(chapter.get("title") or "").strip()
    non_title = [f for f in extract_chapter_facts(chapter, trip, cfg=cfg) if f != title]
    min_count = max(1, int(app_cfg.narrative.decor_line_min_fact_count or 2))
    return len(non_title) >= min_count


def _copy_intent(chapter: dict) -> dict[str, str]:
    raw = (chapter.get("curation") or {}).get("copyIntent") or {}
    out: dict[str, str] = {}
    mood = str(raw.get("mood") or "").strip()
    focus = str(raw.get("focus") or "").strip()
    note = str(raw.get("note") or "").strip()
    if mood in MOOD_VALUES:
        out["mood"] = mood
    if focus in FOCUS_VALUES:
        out["focus"] = focus
    if note:
        out["note"] = note[:30]
    return out


def apply_copy_intent_cascade(
    trip: dict,
    chapter_id: str,
    payload: dict | None,
    *,
    apply_to_subsequent: bool = False,
) -> list[str]:
    """Apply copyIntent to one chapter or from current through following chapters."""
    chapters = trip.get("chapters") or []
    start_idx: int | None = None
    for idx, ch in enumerate(chapters):
        if ch.get("id") == chapter_id:
            start_idx = idx
            break
    if start_idx is None:
        return []
    targets = chapters[start_idx:] if apply_to_subsequent else [chapters[start_idx]]
    updated: list[str] = []
    for ch in targets:
        apply_chapter_copy_intent(ch, payload)
        ch_id = ch.get("id")
        if ch_id:
            updated.append(str(ch_id))
    return updated


def apply_chapter_copy_intent(chapter: dict, payload: dict | None) -> dict[str, str]:
    """Merge PATCH payload into chapter.curation.copyIntent; return normalized intent."""
    curation = chapter.setdefault("curation", {})
    existing = dict(curation.get("copyIntent") or {})
    if payload:
        for key in ("mood", "focus", "note"):
            if key not in payload:
                continue
            val = payload[key]
            if val is None or (isinstance(val, str) and not str(val).strip()):
                existing.pop(key, None)
            else:
                existing[key] = str(val).strip()
    if existing:
        curation["copyIntent"] = existing
    else:
        curation.pop("copyIntent", None)
    normalized = _copy_intent(chapter)
    if normalized:
        curation["copyIntent"] = normalized
    else:
        curation.pop("copyIntent", None)
    return normalized


def _contains_banned(text: str) -> bool:
    lower = text.lower()
    return any(p in text or p in lower for p in _DECOR_BANNED)


def _repeats_title(candidate: str, chapter: dict) -> bool:
    title = str(chapter.get("title") or "").strip()
    if not title:
        return False
    return candidate.startswith(title) or title in candidate


def _repeats_lead(candidate: str, chapter: dict) -> bool:
    lead = str(chapter.get("lead") or "").strip()
    if not lead:
        return False
    return candidate == lead or lead in candidate


def validate_decor_line(
    text: str,
    chapter: dict,
    *,
    cfg: AppConfig | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    max_chars = _max_chars(app_cfg)
    errs: list[str] = []
    if not text:
        return errs
    if "\n" in text or "\r" in text:
        errs.append("VR-N11-01: decorLine must be single line")
    if len(text) > max_chars:
        errs.append(f"VR-N11-02: decorLine exceeds {max_chars} chars")
    if _contains_banned(text):
        errs.append("VR-N11-03: decorLine contains banned phrase")
    if _repeats_title(text, chapter):
        errs.append("VR-N11-04: decorLine repeats chapter title")
    if _repeats_lead(text, chapter):
        errs.append("VR-N11-05: decorLine repeats chapter lead")
    return errs


def validate_copy_intent(chapter: dict, *, chapter_index: int | None = None) -> list[str]:
    prefix = f"chapters[{chapter_index}]" if chapter_index is not None else "chapter"
    raw = (chapter.get("curation") or {}).get("copyIntent")
    if raw is None:
        return []
    if not isinstance(raw, dict):
        return [f"{prefix}.curation.copyIntent must be object"]
    errs: list[str] = []
    mood = raw.get("mood")
    if mood is not None and str(mood).strip() and str(mood).strip() not in MOOD_VALUES:
        errs.append(f"{prefix}.curation.copyIntent.mood invalid enum")
    focus = raw.get("focus")
    if focus is not None and str(focus).strip() and str(focus).strip() not in FOCUS_VALUES:
        errs.append(f"{prefix}.curation.copyIntent.focus invalid enum")
    note = raw.get("note")
    if isinstance(note, str) and len(note) > 30:
        errs.append(f"{prefix}.curation.copyIntent.note exceeds 30 chars")
    return errs


def _score_candidate(
    candidate: str,
    chapter: dict,
    facts: list[str],
    intent: dict[str, str],
    *,
    use_intent: bool,
    voice_snippets: list[str] | None = None,
) -> float:
    if not candidate:
        return -1.0
    length = len(candidate)
    brevity = 1.0 - abs(length - 22) / 22.0
    brevity = max(0.0, min(1.0, brevity))
    factual = 0.0
    lower = candidate.lower()
    for fact in facts:
        if fact and (fact in candidate or fact.lower() in lower):
            factual += 0.35
    factual = min(1.0, factual)
    if voice_snippets:
        for voice in voice_snippets:
            snippet = voice[:12]
            trimmed = voice.strip()
            if snippet and (snippet in candidate or candidate in trimmed or trimmed in candidate):
                factual = min(1.0, factual + 0.3)
                break
    generic_hits = len(_GENERIC_RE.findall(candidate))
    anti_generic = max(0.0, 1.0 - generic_hits * 0.25)
    style_fit = 0.85 if "！" not in candidate and "!" not in candidate else 0.5
    intent_fit = 0.0
    if use_intent and intent:
        note = intent.get("note", "")
        mood = intent.get("mood", "")
        focus = intent.get("focus", "")
        if note and (note in candidate or note[:8] in candidate):
            intent_fit += 0.5
        if mood and mood in candidate:
            intent_fit += 0.25
        if focus == "食物" and any(k in candidate for k in ("吃", "餐", "食", "味")):
            intent_fit += 0.25
        elif focus == "人" and any(k in candidate for k in ("一起", "我们", "同伴", "合影")):
            intent_fit += 0.25
        elif focus == "地方" and any(f in candidate for f in facts if len(f) >= 2):
            intent_fit += 0.2
        intent_fit = min(1.0, intent_fit)
    if use_intent and intent:
        return (
            0.32 * factual
            + 0.2 * brevity
            + 0.16 * anti_generic
            + 0.12 * style_fit
            + 0.2 * intent_fit
        )
    return 0.4 * factual + 0.25 * brevity + 0.2 * anti_generic + 0.15 * style_fit


def _template_candidates(facts: list[str], intent: dict[str, str]) -> list[str]:
    cands: list[str] = []
    primary = facts[0] if facts else ""
    secondary = facts[1] if len(facts) > 1 else ""
    note = intent.get("note", "")
    mood = intent.get("mood", "")
    if note:
        cands.append(note[:30])
    if primary and secondary:
        cands.append(f"{primary}，{secondary}。".replace("。。", "。"))
    if primary and mood:
        cands.append(f"{primary}，{mood}。")
    if mood and not primary:
        cands.append(f"{mood}的一小段路。")
    deduped: list[str] = []
    seen: set[str] = set()
    for c in cands:
        c = c.strip().rstrip("。。") + ("。" if c.strip() and not c.endswith("。") else "")
        c = c.replace("。。", "。")
        if not c or c in seen:
            continue
        seen.add(c)
        deduped.append(c)
    return deduped


def voice_decor_candidates(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> list[str]:
    from travelogue.services.voice_excerpt import trim_voice_for_copy

    app_cfg = decor_line_config(cfg)
    if not app_cfg.narrative.decor_line_voice_first:
        return []
    max_chars = _max_chars(app_cfg)
    out: list[str] = []
    for excerpt in _chapter_voice_excerpts(chapter, trip):
        trimmed = trim_voice_for_copy(excerpt, max_chars=max_chars)
        if trimmed and trimmed not in out:
            out.append(trimmed)
    return out


def _dedupe_candidates(candidates: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for text in candidates:
        key = text.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _merge_decor_candidates(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    k = max(1, int(app_cfg.narrative.decor_line_candidates or 3))
    max_chars = _max_chars(app_cfg)
    facts = extract_chapter_facts(chapter, trip, cfg=app_cfg)
    intent = _copy_intent(chapter) if app_cfg.narrative.decor_line_intent_enabled else {}
    pool: list[str] = []

    pool.extend(voice_decor_candidates(chapter, trip, cfg=app_cfg))

    note = intent.get("note", "")
    if note:
        final = _finalize_copy(note[:30], max_chars)
        if final:
            pool.append(final)

    llm_pool: list[str] = []
    if app_cfg.narrative.decor_line_llm_enabled:
        from travelogue.services.llm_decor_line import generate_llm_decor_line_candidates

        llm_pool = generate_llm_decor_line_candidates(
            chapter, trip, cfg=app_cfg, chat_fn=chat_fn
        )
        pool.extend(llm_pool)

    # Tag-stitch templates are fallback only when LLM is off or returned nothing.
    if not app_cfg.narrative.decor_line_llm_enabled or not llm_pool:
        for text in _template_candidates(facts, intent):
            final = _finalize_copy(text, max_chars)
            if final:
                pool.append(final)

    cleaned: list[str] = []
    for text in _dedupe_candidates(pool):
        if validate_decor_line(text, chapter, cfg=app_cfg):
            continue
        cleaned.append(text)
        if len(cleaned) >= k * 2:
            break
    return cleaned[: max(k * 2, k)]


def generate_decor_line_candidates(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    k = max(1, int(app_cfg.narrative.decor_line_candidates or 3))
    merged = _merge_decor_candidates(chapter, trip, cfg=app_cfg, chat_fn=chat_fn)
    return merged[:k]


def pick_best_decor_line(
    candidates: list[str],
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> str:
    from travelogue.services.copy_intent_infer import resolve_copy_intent

    app_cfg = decor_line_config(cfg)
    facts = extract_chapter_facts(chapter, trip, cfg=app_cfg)
    intent = resolve_copy_intent(chapter, trip) if app_cfg.narrative.decor_line_intent_enabled else {}
    use_intent = bool(intent) and app_cfg.narrative.decor_line_intent_enabled
    voice_snippets = _chapter_voice_excerpts(chapter, trip)
    best = ""
    best_score = -1.0
    for cand in candidates:
        if validate_decor_line(cand, chapter, cfg=app_cfg):
            continue
        score = _score_candidate(
            cand,
            chapter,
            facts,
            intent,
            use_intent=use_intent,
            voice_snippets=voice_snippets,
        )
        if score > best_score:
            best_score = score
            best = cand
    min_score = 0.32 if not app_cfg.narrative.decor_line_allow_empty else 0.26
    if voice_snippets and best in voice_decor_candidates(chapter, trip, cfg=app_cfg):
        min_score = max(0.22, min_score - 0.04)
    if best_score < min_score:
        return ""
    return best


def chapter_needs_decor_line(
    chapter: dict,
    trip: dict | None = None,
    *,
    regenerate: bool = False,
    cfg: AppConfig | None = None,
) -> bool:
    if chapter.get("edited"):
        return False
    if regenerate:
        return True
    line = str(chapter.get("decorLine") or "").strip()
    if line:
        app_cfg = decor_line_config(cfg)
        if app_cfg.narrative.decor_line_llm_enabled and decor_line_is_tag_stub(line):
            return True
        if trip:
            phase = str(
                ((trip.get("curation") or {}).get("copyStyle") or {}).get("phase") or ""
            )
            if phase and phase != "lite-copy-v1.1":
                return True
        return False
    return True


def apply_decor_lines(
    trip: dict,
    *,
    regenerate: bool = False,
    dry_run: bool = False,
    chapter_id: str | None = None,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    if not app_cfg.narrative.decor_line_enabled or not app_cfg.narrative.copy_generation_enabled:
        return []
    updated: list[str] = []
    chapters = trip.get("chapters") or []
    for ch in chapters:
        if chapter_id and ch.get("id") != chapter_id:
            continue
        if not chapter_needs_decor_line(ch, trip, regenerate=regenerate, cfg=app_cfg):
            continue
        idx = ch.get("index")
        field = f"chapters[{idx}].decorLine"
        if dry_run:
            updated.append(field)
            continue
        if not decor_line_facts_sufficient(ch, trip, cfg=app_cfg):
            ch["decorLine"] = ""
            updated.append(field)
            continue
        candidates = generate_decor_line_candidates(
            ch, trip, cfg=app_cfg, chat_fn=chat_fn
        )
        chosen = pick_best_decor_line(candidates, ch, trip, cfg=app_cfg)
        ch["decorLine"] = chosen
        if (chosen or "").strip() and not ch.get("edited"):
            ch.pop("lead", None)
        updated.append(field)
    if updated and not dry_run:
        curation = trip.setdefault("curation", {})
        copy_style = curation.setdefault("copyStyle", {})
        copy_style["phase"] = "lite-copy-v1.1"
        from travelogue.services.copy_metrics import merge_copy_run_note, record_copy_metrics

        metrics = record_copy_metrics(trip)
        merge_copy_run_note(
            trip,
            agent="storyteller-lite",
            note=f"decorLine fill={metrics.get('decor_line_fill_rate')} empty={metrics.get('decor_line_empty_rate')}",
        )
    return updated
