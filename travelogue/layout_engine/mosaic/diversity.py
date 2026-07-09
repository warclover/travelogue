"""MCS candidate diversity (PRD §9.4 · off | mmr | dpp)."""

from __future__ import annotations

from travelogue.layout_contract.rhythm import layout_kind_from_pattern
from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
from travelogue.layout_engine.mosaic.lte_adapter import read_templates_from_lte


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    lo = min(scores)
    hi = max(scores)
    if hi - lo <= 1e-9:
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def pattern_topology_key(pattern_id: str) -> tuple:
    if read_templates_from_lte():
        try:
            from travelogue.layout_templates.registry import get_engine

            tpl = get_engine().get(pattern_id)
            return (
                tpl.kind,
                tpl.photo_count_max,
                tuple(tpl.stage.cols or ()),
                tuple(tpl.stage.rows or ()),
                tpl.render_grid_class,
            )
        except KeyError:
            pass
    return (layout_kind_from_pattern(pattern_id), pattern_id)


def pattern_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    ka = pattern_topology_key(a)
    kb = pattern_topology_key(b)
    if ka == kb:
        return 1.0
    score = 0.0
    if ka[0] == kb[0]:
        score += 0.25
    if len(ka) > 1 and len(kb) > 1 and ka[1] == kb[1]:
        score += 0.15
    if len(ka) > 4 and len(kb) > 4 and ka[4] == kb[4]:
        score += 0.35
    if len(ka) > 2 and len(kb) > 2 and ka[2] == kb[2] and ka[2]:
        score += 0.15
    if len(ka) > 3 and len(kb) > 3 and ka[3] == kb[3] and ka[3]:
        score += 0.10
    if ka[-1] == kb[-1] and isinstance(ka[-1], str):
        score += 0.2
    return min(1.0, score)


def _chapter_pattern_ids(layout_state) -> list[str]:
    if layout_state is None:
        return []
    counts = getattr(layout_state, "pattern_counts", None) or {}
    return [pid for pid, n in counts.items() if n > 0]


def rerank_scored_candidates_mmr(
    scored: list[tuple[ScreenCandidate, float, list[str]]],
    *,
    layout_state,
    mmr_lambda: float = 0.65,
) -> list[tuple[ScreenCandidate, float, list[str]]]:
    """Re-order scored window candidates with MMR vs chapter patterns already used."""
    if len(scored) <= 1:
        return scored
    prior = _chapter_pattern_ids(layout_state)
    rel = _normalize_scores([t[1] for t in scored])
    remaining = list(range(len(scored)))
    ordered: list[int] = []

    while remaining:
        best_pos: int | None = None
        best_mmr = float("-inf")
        for pos in remaining:
            pid = scored[pos][0].pattern_id
            redundancy = 0.0
            if prior:
                redundancy = max(pattern_similarity(pid, p) for p in prior)
            if ordered:
                redundancy = max(
                    redundancy,
                    max(pattern_similarity(pid, scored[chosen][0].pattern_id) for chosen in ordered),
                )
            mmr = mmr_lambda * rel[pos] - (1.0 - mmr_lambda) * redundancy
            if mmr > best_mmr:
                best_mmr = mmr
                best_pos = pos
        if best_pos is None:
            break
        ordered.append(best_pos)
        remaining.remove(best_pos)

    return [scored[i] for i in ordered]


def rerank_scored_candidates_dpp(
    scored: list[tuple[ScreenCandidate, float, list[str]]],
    *,
    layout_state,
    mmr_lambda: float = 0.65,
) -> list[tuple[ScreenCandidate, float, list[str]]]:
    """Greedy DPP-style diversity; falls back to MMR when kernel is degenerate."""
    if len(scored) <= 1:
        return scored
    prior = _chapter_pattern_ids(layout_state)
    rel = _normalize_scores([t[1] for t in scored])
    remaining = list(range(len(scored)))
    ordered: list[int] = []
    chosen_pids: list[str] = list(prior)

    while remaining:
        best_pos: int | None = None
        best_gain = float("-inf")
        for pos in remaining:
            pid = scored[pos][0].pattern_id
            quality = rel[pos]
            diversity = 1.0
            if chosen_pids:
                max_sim = max(pattern_similarity(pid, p) for p in chosen_pids)
                diversity = max(0.05, 1.0 - max_sim)
            gain = quality * diversity
            if gain > best_gain:
                best_gain = gain
                best_pos = pos
        if best_pos is None:
            break
        ordered.append(best_pos)
        chosen_pids.append(scored[best_pos][0].pattern_id)
        remaining.remove(best_pos)

    if not ordered:
        return rerank_scored_candidates_mmr(
            scored,
            layout_state=layout_state,
            mmr_lambda=mmr_lambda,
        )
    return [scored[i] for i in ordered]


def apply_candidate_diversity(
    scored: list[tuple[ScreenCandidate, float, list[str]]],
    *,
    layout_state,
    mode: str = "off",
    mmr_lambda: float = 0.65,
) -> list[tuple[ScreenCandidate, float, list[str]]]:
    mode_norm = str(mode or "off").strip().lower()
    if mode_norm == "off" or not scored:
        return scored
    if mode_norm == "dpp":
        return rerank_scored_candidates_dpp(
            scored,
            layout_state=layout_state,
            mmr_lambda=mmr_lambda,
        )
    return rerank_scored_candidates_mmr(
        scored,
        layout_state=layout_state,
        mmr_lambda=mmr_lambda,
    )
