"""Ingest-time hints for multi-journey / multi-segment albums."""

from __future__ import annotations

from travelogue.domain.time_segments import cluster_time_segments


def preview_multi_journey(assets: list[dict], *, place: str = "旅途") -> str | None:
    """
    Heuristic pre-curate hint when ingest photos likely span multiple trips.

    Uses the same segment gap as curate (default 14 days). Does not mutate trip.
    """
    if len(assets) < 6:
        return None
    segments = cluster_time_segments(assets, place=place)
    if len(segments) < 2:
        return None
    labels = [s.label for s in segments[:4]]
    preview = "、".join(labels)
    if len(segments) > 4:
        preview += f" 等{len(segments)}段"
    return (
        f"检测到可能包含 {len(segments)} 次旅行（{preview}）；"
        "默认将合成一本游记（3–5 章），可在 G1 合并段或拆成多本"
    )
