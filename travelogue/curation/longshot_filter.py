"""P5-D1 · longshot surface screen filter (≤10–15 hero/grid screens, web keeps full trip)."""

from __future__ import annotations

import copy

DEFAULT_MAX_SCREENS = 12
BREATH_PATTERN = "screen-breath-pause"


def _is_breath_screen(screen: dict) -> bool:
    return screen.get("patternId") == BREATH_PATTERN


def _screen_kind(screen: dict) -> str:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    return "hero" if len(aids) <= 1 else "grid"


def _screen_score(index: int, screen: dict) -> float:
    score = 1.0
    if index < 2:
        score += 2.0
    if screen.get("arcSegment") == "peak":
        score += 3.0
    if _screen_kind(screen) == "hero":
        score += 0.5
    return score


def select_longshot_screens(
    screens: list[dict],
    *,
    max_screens: int = DEFAULT_MAX_SCREENS,
) -> list[dict]:
    """Pick ≤ max_screens photo screens; preserve document order."""
    content = [sc for sc in screens if not _is_breath_screen(sc)]
    content = [sc for sc in content if any(s.get("assetId") for s in sc.get("slots") or [])]
    if len(content) <= max_screens:
        return list(screens)

    indexed = list(enumerate(content))
    must = {0}
    for i, sc in indexed:
        if sc.get("arcSegment") == "peak":
            must.add(i)
        if i < 2:
            must.add(i)

    ranked = sorted(indexed, key=lambda t: (-_screen_score(t[0], t[1]), t[0]))
    chosen: set[int] = set(must)
    want_hero = True
    for i, sc in ranked:
        if len(chosen) >= max_screens:
            break
        if i in chosen:
            continue
        kind = _screen_kind(sc)
        if want_hero and kind != "hero":
            continue
        if not want_hero and kind != "grid":
            continue
        chosen.add(i)
        want_hero = not want_hero

    for i, _ in indexed:
        if len(chosen) >= max_screens:
            break
        chosen.add(i)

    keep = chosen
    out: list[dict] = []
    content_idx = 0
    for sc in screens:
        if _is_breath_screen(sc):
            continue
        if not any(s.get("assetId") for s in sc.get("slots") or []):
            continue
        if content_idx in keep:
            out.append(sc)
        content_idx += 1
    return out


def filter_chapter_for_longshot(chapter: dict, *, max_screens: int = DEFAULT_MAX_SCREENS) -> dict:
    screens = chapter.get("screens") or []
    if not screens:
        return chapter
    filtered = select_longshot_screens(screens, max_screens=max_screens)
    if filtered == screens:
        return chapter
    out = dict(chapter)
    out["screens"] = filtered
    return out


def chapters_for_longshot_render(
    chapters: list[dict],
    *,
    max_screens: int = DEFAULT_MAX_SCREENS,
) -> list[dict]:
    """Allocate screen budget across chapters proportionally."""
    if not chapters:
        return []

    per_chapter: list[list[dict]] = []
    counts: list[int] = []
    for ch in chapters:
        screens = [
            sc
            for sc in ch.get("screens") or []
            if not _is_breath_screen(sc)
            and any(s.get("assetId") for s in sc.get("slots") or [])
        ]
        per_chapter.append(screens)
        counts.append(len(screens))

    total = sum(counts)
    if total <= max_screens:
        out: list[dict] = []
        for ch in chapters:
            ch_copy = copy.deepcopy(ch)
            ch_copy["screens"] = [
                sc for sc in ch.get("screens") or [] if not _is_breath_screen(sc)
            ]
            out.append(ch_copy)
        return out

    budget = max_screens
    alloc = [0] * len(chapters)
    for i, n in enumerate(counts):
        if n == 0:
            continue
        share = max(1, round(budget * n / total))
        alloc[i] = min(n, share)

    while sum(alloc) > max_screens:
        i = max(range(len(alloc)), key=lambda j: alloc[j])
        if alloc[i] > 1:
            alloc[i] -= 1
        else:
            break

    while sum(alloc) < max_screens:
        candidates = [i for i, n in enumerate(counts) if alloc[i] < n]
        if not candidates:
            break
        i = max(candidates, key=lambda j: counts[j] - alloc[j])
        alloc[i] += 1

    out: list[dict] = []
    for ch, screens, cap in zip(chapters, per_chapter, alloc, strict=True):
        ch_copy = copy.deepcopy(ch)
        if not screens:
            out.append(ch_copy)
            continue
        if len(screens) <= cap:
            ch_copy["screens"] = [
                sc for sc in ch.get("screens") or [] if not _is_breath_screen(sc)
            ]
        else:
            picked = select_longshot_screens(screens, max_screens=cap)
            ch_copy["screens"] = picked
        out.append(ch_copy)
    return out
