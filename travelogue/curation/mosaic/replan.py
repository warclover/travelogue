"""Single-screen replan API (Benchmark P1 · studio integration stub)."""

from __future__ import annotations

from typing import Any, Literal

ReplanStrategy = Literal["alt_topk", "legacy"]


def replan_screen(
    chapters: list[dict],
    screen_id: str,
    *,
    strategy: ReplanStrategy = "alt_topk",
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Reserved for post-auto layout edits (PRD benchmark §4.2 P1).

    Raises NotImplementedError until studio passes window context + mosaic cfg.
    """
    raise NotImplementedError(
        f"replan_screen({screen_id!r}, strategy={strategy!r}, top_k={top_k}) "
        "is not wired yet; use mosaicDecisionLog replay for offline analysis."
    )
