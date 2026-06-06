"""Phase 11 · chapter decorLine generation (rule-based + optional LLM brief)."""

from __future__ import annotations

import re

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


def extract_chapter_facts(chapter: dict, trip: dict) -> list[str]:
    facts: list[str] = []
    title = str(chapter.get("title") or "").strip()
    if title:
        facts.append(title)
    curation = chapter.get("curation") or {}
    for anchor in curation.get("memoryAnchors") or []:
        text = str(anchor or "").strip()
        if text:
            facts.append(text)
    for place in curation.get("places") or []:
        text = str(place or "").strip()
        if text:
            facts.append(text)
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
    if primary:
        cands.append(f"{primary}，留在这一章。")
    if secondary:
        cands.append(f"记住{secondary}。")
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


def generate_decor_line_candidates(
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    k = max(1, int(app_cfg.narrative.decor_line_candidates or 3))
    facts = extract_chapter_facts(chapter, trip)
    intent = _copy_intent(chapter) if app_cfg.narrative.decor_line_intent_enabled else {}
    raw = _template_candidates(facts, intent)
    max_chars = _max_chars(app_cfg)
    cleaned: list[str] = []
    for text in raw:
        final = _finalize_copy(text, max_chars)
        if final and final not in cleaned:
            cleaned.append(final)
        if len(cleaned) >= k:
            break
    return cleaned[:k]


def pick_best_decor_line(
    candidates: list[str],
    chapter: dict,
    trip: dict,
    *,
    cfg: AppConfig | None = None,
) -> str:
    app_cfg = decor_line_config(cfg)
    facts = extract_chapter_facts(chapter, trip)
    intent = _copy_intent(chapter) if app_cfg.narrative.decor_line_intent_enabled else {}
    use_intent = bool(intent) and app_cfg.narrative.decor_line_intent_enabled
    best = ""
    best_score = -1.0
    for cand in candidates:
        if validate_decor_line(cand, chapter, cfg=app_cfg):
            continue
        score = _score_candidate(cand, chapter, facts, intent, use_intent=use_intent)
        if score > best_score:
            best_score = score
            best = cand
    min_score = 0.35 if not app_cfg.narrative.decor_line_allow_empty else 0.28
    if best_score < min_score:
        return ""
    return best


def chapter_needs_decor_line(
    chapter: dict,
    *,
    regenerate: bool = False,
) -> bool:
    if chapter.get("edited"):
        return False
    if regenerate:
        return True
    if "decorLine" in chapter:
        return False
    return True


def apply_decor_lines(
    trip: dict,
    *,
    regenerate: bool = False,
    dry_run: bool = False,
    chapter_id: str | None = None,
    cfg: AppConfig | None = None,
) -> list[str]:
    app_cfg = decor_line_config(cfg)
    if not app_cfg.narrative.decor_line_enabled:
        return []
    updated: list[str] = []
    chapters = trip.get("chapters") or []
    for ch in chapters:
        if chapter_id and ch.get("id") != chapter_id:
            continue
        if not chapter_needs_decor_line(ch, regenerate=regenerate):
            continue
        idx = ch.get("index")
        field = f"chapters[{idx}].decorLine"
        if dry_run:
            updated.append(field)
            continue
        candidates = generate_decor_line_candidates(ch, trip, cfg=app_cfg)
        chosen = pick_best_decor_line(candidates, ch, trip, cfg=app_cfg)
        ch["decorLine"] = chosen
        updated.append(field)
    if updated and not dry_run:
        curation = trip.setdefault("curation", {})
        copy_style = curation.setdefault("copyStyle", {})
        copy_style["phase"] = "p11-lite-line"
    return updated
