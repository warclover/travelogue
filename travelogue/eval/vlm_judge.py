"""P19 VLM pairwise judge helpers (mock + report aggregation)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROMPT_REL = "docs/p19/vlm-judge-prompt-v1.md"


def mock_pairwise_judge(trip_id: str, baseline: dict, candidate: dict) -> dict[str, Any]:
    """Deterministic stub until API judge is wired."""
    b_seq = baseline.get("patternSequence") or []
    c_seq = candidate.get("patternSequence") or []
    if b_seq == c_seq:
        winner = "tie"
    else:
        winner = "B" if len(set(c_seq)) >= len(set(b_seq)) else "A"
    dims = {k: winner for k in ("rhythm", "whitespace", "crop", "monotony", "book_like")}
    return {
        "tripId": trip_id,
        "overallWinner": winner,
        "dimensions": dims,
        "confidence": 0.5,
        "briefReason": "mock: pattern diversity heuristic",
        "mode": "mock",
    }


def aggregate_judge_report(
    results: list[dict[str, Any]],
    *,
    mode: str,
    prompt_version: str,
    repo_root: Path,
) -> dict[str, Any]:
    wins_b = sum(1 for r in results if r.get("overallWinner") == "B")
    wins_a = sum(1 for r in results if r.get("overallWinner") == "A")
    ties = sum(1 for r in results if r.get("overallWinner") == "tie")
    total = len(results)
    return {
        "promptVersion": prompt_version,
        "promptPath": str(repo_root / PROMPT_REL),
        "mode": mode,
        "tripCount": total,
        "candidateWins": wins_b,
        "baselineWins": wins_a,
        "ties": ties,
        "candidateWinRate": round(wins_b / total, 4) if total else 0.0,
        "trips": results,
    }
