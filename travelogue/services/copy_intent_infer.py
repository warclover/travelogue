"""Passive copyIntent inference from voice / anchors (no user input required)."""

from __future__ import annotations

from travelogue.services.decor_line import FOCUS_VALUES, MOOD_VALUES, _chapter_voice_excerpts

_MOOD_HINTS: tuple[tuple[str, str], ...] = (
    ("赶路", "赶|地铁|高铁|飞机|转车|排队"),
    ("意外", "意外|没想到|突然|居然|竟然"),
    ("仪式感", "仪式|典礼|婚礼|毕业|生日"),
    ("热闹", "热闹|人声|拥挤|排队|夜市"),
    ("平静", "安静|慢|风|停|静"),
    ("松弛", "躺|歇|慢|空|懒"),
)

_FOCUS_HINTS: tuple[tuple[str, str], ...] = (
    ("食物", "吃|餐|食|味|面|菜|饭|咖啡|茶"),
    ("人", "一起|我们|同伴|合影|朋友|家人"),
    ("关系", "一起|同伴|朋友|家人|同事"),
    ("自我感受", "觉得|感受|心里|自己"),
    ("地方", "街|路|城|镇|寺|馆|园|山|海|湖"),
)


def infer_copy_intent(chapter: dict, trip: dict) -> dict[str, str]:
    """Return mood/focus hints inferred from chapter signals (may be partial)."""
    corpus_parts: list[str] = []
    for excerpt in _chapter_voice_excerpts(chapter, trip):
        corpus_parts.append(excerpt)
    curation = chapter.get("curation") or {}
    for anchor in curation.get("memoryAnchors") or []:
        text = str(anchor or "").strip()
        if text:
            corpus_parts.append(text)
    corpus = " ".join(corpus_parts)
    if not corpus.strip():
        return {}

    import re

    out: dict[str, str] = {}
    for mood, pattern in _MOOD_HINTS:
        if mood in MOOD_VALUES and re.search(pattern, corpus):
            out["mood"] = mood
            break
    for focus, pattern in _FOCUS_HINTS:
        if focus in FOCUS_VALUES and re.search(pattern, corpus):
            out["focus"] = focus
            break
    return out


def resolve_copy_intent(chapter: dict, trip: dict) -> dict[str, str]:
    """Explicit copyIntent merged with passive inference (explicit wins)."""
    from travelogue.services.decor_line import _copy_intent

    explicit = _copy_intent(chapter)
    if explicit:
        return explicit
    return infer_copy_intent(chapter, trip)
