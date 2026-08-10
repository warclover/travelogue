"""Editorial intent hints for curate (Phase 4 M19 · PRD-PHASE4 §8.3)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_STOPWORDS = frozenset(
    {
        "我们",
        "你们",
        "他们",
        "这个",
        "那个",
        "不要",
        "可以",
        "已经",
        "还是",
        "就是",
        "一个",
        "没有",
        "什么",
        "怎么",
        "因为",
        "所以",
        "如果",
        "然后",
        "但是",
        "而且",
        "或者",
        "以及",
        "还有",
        "希望",
        "想要",
        "需要",
        "觉得",
        "感觉",
        "比较",
        "非常",
        "特别",
        "真的",
        "可能",
        "应该",
        "不会",
        "不是",
        "这样",
        "那样",
        "一下",
        "一点",
        "一些",
        "这些",
        "那些",
        "自己",
        "大家",
        "一起",
        "慢慢",
        "慢慢走",
    }
)

_CJK_TOKEN = re.compile(r"[\u4e00-\u9fff]{2,6}")
_DAY_HINT = re.compile(
    r"(?:day\s*(\d+)|d\s*(\d+)|第\s*(\d+)\s*天)",
    re.IGNORECASE,
)
_PEAK_PHRASE = re.compile(r"高潮|最难忘|highlight|climax|peak", re.IGNORECASE)

INTENT_PEAK_ARC_BOOST = 0.1
ANCHOR_MATCH_MULTIPLIER = 1.05


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().casefold()


def resolve_user_notes(trip: dict) -> str:
    intent = trip.get("intent") or {}
    return str(trip.get("userNotes") or intent.get("userNotes") or "").strip()


def _keyword_candidates(token: str) -> list[str]:
    if len(token) <= 3:
        return [token]
    if len(token) == 4:
        return [token[:2], token[2:]]
    return [token]


def extract_user_notes_keywords(user_notes: str, *, max_items: int = 10) -> list[str]:
    """Extract short meaningful tokens from free-text userNotes."""
    if not user_notes.strip():
        return []
    seen: set[str] = set()
    keywords: list[str] = []
    for segment in re.split(r"[\s,，。；;、！!？?]+", user_notes):
        segment = segment.strip()
        if not segment:
            continue
        for match in _CJK_TOKEN.finditer(segment):
            for token in _keyword_candidates(match.group(0)):
                key = _normalize(token)
                if len(key) < 2 or key in _STOPWORDS or key in seen:
                    continue
                seen.add(key)
                keywords.append(token[:6])
                if len(keywords) >= max_items:
                    return keywords
    return keywords


def peak_chapter_hints(user_notes: str, total_chapters: int) -> set[int]:
    """Map peak phrases / day markers in userNotes to 1-based chapter indices."""
    if total_chapters <= 0 or not user_notes.strip():
        return set()

    hints: set[int] = set()
    for match in _DAY_HINT.finditer(user_notes):
        raw = next(g for g in match.groups() if g)
        try:
            day = int(raw)
        except (TypeError, ValueError):
            continue
        if 1 <= day <= total_chapters:
            hints.add(day)

    if _PEAK_PHRASE.search(user_notes) and not hints:
        hints.add(max(1, min(total_chapters, (total_chapters + 1) // 2)))
    return hints


def _intent_brief(trip: dict) -> dict[str, Any]:
    intent = trip.get("intent") if isinstance(trip.get("intent"), dict) else {}
    brief = intent.get("intentBrief")
    return brief if isinstance(brief, dict) else {}


def peak_chapter_hints_for_trip(trip: dict, total_chapters: int) -> set[int]:
    """Prefer ``intent.intentBrief.layoutHints.peakChapterIndex`` when present (ACP W2)."""
    brief = _intent_brief(trip)
    layout = brief.get("layoutHints") if isinstance(brief.get("layoutHints"), dict) else {}
    peak_idx = layout.get("peakChapterIndex")
    try:
        idx = int(peak_idx) if peak_idx is not None else None
    except (TypeError, ValueError):
        idx = None
    if idx is not None and 1 <= idx <= total_chapters:
        return {idx}
    return peak_chapter_hints(resolve_user_notes(trip), total_chapters)


def arc_segment_for_chapter_with_intent(
    index: int,
    total: int,
    *,
    profile: str = "dynamic",
    peak_chapters: set[int] | None = None,
) -> str:
    """Chapter-level arc beat from profile; intent peak is applied at screen stamp time."""
    _arc = __import__("travelogue.curation.arc_patterns", fromlist=["arc_segment_for_chapter"])
    arc_segment_for_chapter = _arc.arc_segment_for_chapter

    _ = peak_chapters  # layout callers pass peak_chapters separately for scoring boost
    return arc_segment_for_chapter(index, total, profile=profile)  # type: ignore[arg-type]


def is_intent_peak_chapter(index: int, peak_chapters: set[int] | None) -> bool:
    return bool(peak_chapters and index in peak_chapters)


def build_intent_hints(trip: dict) -> dict[str, Any]:
    """Merge editorial hints from intent + ingest signals (preserves planCities)."""
    curation = trip.get("curation") or {}
    hints: dict[str, Any] = dict(curation.get("intentHints") or {})

    # Prefer intent.travelPlan.cities when present; otherwise keep existing planCities.
    travel_plan = (trip.get("intent") or {}).get("travelPlan") or {}
    plan_cities = travel_plan.get("cities")
    if isinstance(plan_cities, list) and plan_cities:
        hints["planCities"] = list(plan_cities)

    user_notes = resolve_user_notes(trip)
    keywords = extract_user_notes_keywords(user_notes)
    brief = _intent_brief(trip)
    # ACP W2 · Intent Brief keywords enrich regex tokens (do not replace when empty).
    if brief.get("source") in ("llm", "cache"):
        extra: list[str] = []
        title_hint = brief.get("titleHint")
        if isinstance(title_hint, str) and title_hint.strip():
            extra.extend(extract_user_notes_keywords(title_hint, max_items=4))
        for peak in brief.get("peakMoments") or []:
            if isinstance(peak, str) and peak.strip():
                extra.extend(extract_user_notes_keywords(peak, max_items=3))
        if extra:
            merged: list[str] = []
            seen: set[str] = set()
            for tok in [*keywords, *extra]:
                key = _normalize(tok)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(tok)
                if len(merged) >= 12:
                    break
            keywords = merged
    if keywords:
        hints["userNotesKeywords"] = keywords
    else:
        hints.pop("userNotesKeywords", None)

    intent = trip.get("intent") or {}
    folders = intent.get("folders") or {}
    featured_detected = bool(folders.get("featuredDetected"))
    featured_assets = any(a.get("userTier") == "featured" for a in trip.get("assets") or [])
    if featured_detected or featured_assets:
        hints["featuredBoost"] = True
    else:
        hints.pop("featuredBoost", None)

    _ld = __import__(
        "travelogue.curation.layout_density",
        fromlist=["intent_hints_for_density", "layout_density_from_trip"],
    )
    intent_hints_for_density = _ld.intent_hints_for_density
    layout_density_from_trip = _ld.layout_density_from_trip

    density_hints = intent_hints_for_density(layout_density_from_trip(trip))
    if density_hints:
        hints.update(density_hints)
    else:
        for key in ("layoutDensity", "preferMosaic", "nineQuotaScale"):
            hints.pop(key, None)

    # ACP W2 · layoutHints.preferMosaic overrides density preferMosaic when set.
    layout_b = brief.get("layoutHints") if isinstance(brief.get("layoutHints"), dict) else {}
    if brief.get("source") in ("llm", "cache") and layout_b.get("preferMosaic") is not None:
        hints["preferMosaic"] = bool(layout_b.get("preferMosaic"))
    if brief.get("source") in ("llm", "cache") and layout_b.get("arc"):
        hints["intentBriefArc"] = str(layout_b.get("arc"))
    cull = brief.get("cullPolicy") if isinstance(brief.get("cullPolicy"), dict) else {}
    if brief.get("source") in ("llm", "cache") and cull:
        hints["intentBriefCullPolicy"] = {
            k: cull[k] for k in ("dropScreenshots", "keepEmotionalBlur", "keepPortraits", "foodPriority")
            if cull.get(k) is not None
        }

    return hints


def apply_editorial_intent_hints(trip: dict) -> dict[str, Any]:
    hints = build_intent_hints(trip)
    curation = trip.setdefault("curation", {})
    if hints:
        curation["intentHints"] = hints
    elif "intentHints" in curation:
        curation.pop("intentHints", None)
    return hints


def prior_chapter_memory_anchors(trip: dict) -> list[list[str]]:
    anchors: list[list[str]] = []
    for ch in trip.get("chapters") or []:
        raw = (ch.get("curation") or {}).get("memoryAnchors") or []
        cleaned = [str(item).strip()[:24] for item in raw if str(item).strip()]
        anchors.append(cleaned[:3])
    return anchors


def _chapter_copy_text(chapter: dict) -> str:
    parts: list[str] = []
    for key in ("title", "lead", "hook"):
        value = chapter.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    for item in chapter.get("items") or []:
        if not isinstance(item, dict):
            continue
        for key in ("title", "caption"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
    return " ".join(parts)


def evaluate_intent_keyword_coverage(trip: dict, *, threshold: float = 0.6) -> dict[str, Any]:
    """P-EVAL G-P4-03: share of chapters whose copy hits userNotesKeywords."""
    hints = (trip.get("curation") or {}).get("intentHints") or {}
    keywords = hints.get("userNotesKeywords") or extract_user_notes_keywords(resolve_user_notes(trip))
    chapters = trip.get("chapters") or []
    if not keywords or not chapters:
        return {
            "keywords": keywords,
            "chapterCount": len(chapters),
            "hitChapters": 0,
            "ratio": 0.0,
            "passesGP403": False,
        }
    hit = 0
    for chapter in chapters:
        text = _chapter_copy_text(chapter).casefold()
        if any(str(kw).casefold() in text for kw in keywords):
            hit += 1
    ratio = hit / len(chapters)
    return {
        "keywords": keywords,
        "chapterCount": len(chapters),
        "hitChapters": hit,
        "ratio": round(ratio, 4),
        "passesGP403": ratio >= threshold,
    }

