"""P5-D1 / P6-D2 · longshot surface screen filter with optional MMR diversity."""

from __future__ import annotations

import copy
from typing import Mapping

DEFAULT_MAX_SCREENS = 12
BREATH_PATTERN = "screen-breath-pause"
DEFAULT_MMR_LAMBDA = 0.72


def _is_breath_screen(screen: dict) -> bool:
    return screen.get("patternId") == BREATH_PATTERN


def _screen_kind(screen: dict) -> str:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    return "hero" if len(aids) <= 1 else "grid"


def _dominant_tone_for_screen(screen: dict, assets_by_id: Mapping[str, dict]) -> str:
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        tone = (assets_by_id.get(aid) or {}).get("dominantTone")
        if isinstance(tone, str) and tone:
            return tone
    return ""


def _screen_diversity_key(screen: dict, assets_by_id: Mapping[str, dict]) -> tuple:
    return (
        str(screen.get("patternId") or ""),
        _screen_kind(screen),
        _dominant_tone_for_screen(screen, assets_by_id),
    )


def _screen_similarity(a: tuple, b: tuple) -> float:
    pid_a, kind_a, tone_a = a
    pid_b, kind_b, tone_b = b
    score = 0.0
    if pid_a and pid_a == pid_b:
        score += 0.55
    if kind_a == kind_b:
        score += 0.25
    if tone_a and tone_a == tone_b:
        score += 0.20
    return min(1.0, score)


def _screen_score(index: int, screen: dict) -> float:
    score = 1.0
    if index < 2:
        score += 2.0
    if screen.get("arcSegment") == "peak":
        score += 3.0
    if _screen_kind(screen) == "hero":
        score += 0.5
    return score


def _normalize_relevance(scores: list[float]) -> list[float]:
    if not scores:
        return []
    lo = min(scores)
    hi = max(scores)
    if hi - lo <= 1e-9:
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def _mmr_select_indices(
    indexed: list[tuple[int, dict]],
    *,
    max_pick: int,
    assets_by_id: Mapping[str, dict],
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
) -> list[int]:
    """Maximal Marginal Relevance over screen diversity keys."""
    if max_pick <= 0 or not indexed:
        return []
    rel_raw = [_screen_score(i, sc) for i, sc in indexed]
    rel = _normalize_relevance(rel_raw)
    keys = [_screen_diversity_key(sc, assets_by_id) for _, sc in indexed]
    remaining = list(range(len(indexed)))
    chosen: list[int] = []

    while remaining and len(chosen) < max_pick:
        best_pos: int | None = None
        best_mmr = float("-inf")
        for pos in remaining:
            relevance = rel[pos]
            redundancy = 0.0
            if chosen:
                redundancy = max(_screen_similarity(keys[pos], keys[c]) for c in chosen)
            mmr = mmr_lambda * relevance - (1.0 - mmr_lambda) * redundancy
            if mmr > best_mmr:
                best_mmr = mmr
                best_pos = pos
        if best_pos is None:
            break
        chosen.append(best_pos)
        remaining.remove(best_pos)
    return [indexed[pos][0] for pos in chosen]


def select_longshot_screens(
    screens: list[dict],
    *,
    max_screens: int = DEFAULT_MAX_SCREENS,
    assets_by_id: Mapping[str, dict] | None = None,
    enable_mmr: bool = True,
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
    max_consecutive_same_pattern: int = 2,
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

    if enable_mmr and assets_by_id:
        mmr_indices = set(
            _mmr_select_indices(
                indexed,
                max_pick=max_screens,
                assets_by_id=assets_by_id,
                mmr_lambda=mmr_lambda,
            )
        )
        chosen = set(must) | mmr_indices
        if len(chosen) < max_screens:
            ranked = sorted(indexed, key=lambda t: (-_screen_score(t[0], t[1]), t[0]))
            for i, _ in ranked:
                if len(chosen) >= max_screens:
                    break
                chosen.add(i)
    else:
        ranked = sorted(indexed, key=lambda t: (-_screen_score(t[0], t[1]), t[0]))
        chosen = set(must)
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

    if max_consecutive_same_pattern > 0:
        ordered = sorted(chosen)
        filtered: list[int] = []
        for idx in ordered:
            trial = filtered + [idx]
            trial_screens = [content[i] for i in trial]
            from travelogue.curation.layout_constraints import plan_violates_consecutive_pattern

            if plan_violates_consecutive_pattern(
                trial_screens,
                max_streak=max_consecutive_same_pattern,
            ):
                continue
            filtered.append(idx)
        if filtered:
            chosen = set(filtered)

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


def filter_chapter_for_longshot(chapter: dict, *, max_screens: int = DEFAULT_MAX_SCREENS, **kwargs) -> dict:
    screens = chapter.get("screens") or []
    if not screens:
        return chapter
    filtered = select_longshot_screens(screens, max_screens=max_screens, **kwargs)
    if filtered == screens:
        return chapter
    out = dict(chapter)
    out["screens"] = filtered
    return out


def chapters_for_longshot_render(
    chapters: list[dict],
    *,
    max_screens: int = DEFAULT_MAX_SCREENS,
    assets_by_id: Mapping[str, dict] | None = None,
    enable_mmr: bool = True,
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
    max_consecutive_same_pattern: int = 2,
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

    pick_kwargs = {
        "assets_by_id": assets_by_id or {},
        "enable_mmr": enable_mmr,
        "mmr_lambda": mmr_lambda,
        "max_consecutive_same_pattern": max_consecutive_same_pattern,
    }
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
            picked = select_longshot_screens(screens, max_screens=cap, **pick_kwargs)
            ch_copy["screens"] = picked
        out.append(ch_copy)
    return out
