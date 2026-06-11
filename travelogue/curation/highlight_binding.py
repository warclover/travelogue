"""P19 R-504 · bind highlight windows to chapter opener heroes."""

from __future__ import annotations

from travelogue.curation.subset_planner import _quality_score
from travelogue.layout_engine.highlight_windows import detect_highlight_windows


def bind_highlight_opener_heroes(
    chapter_heroes: dict[str, str],
    buckets: list[list[str]],
    assets_by_id: dict[str, dict],
    *,
    enabled: bool = True,
    window_sizes: tuple[int, ...] = (5, 8, 12),
    max_windows: int = 2,
) -> dict[str, str]:
    """Override chapter heroes when a highlight window anchors the bucket opener."""
    if not enabled:
        return chapter_heroes
    pool = list(assets_by_id.values())
    out = dict(chapter_heroes)
    for idx, bucket in enumerate(buckets):
        if not bucket:
            continue
        ch_id = f"ch-{idx + 1:02d}"
        windows = detect_highlight_windows(
            bucket,
            assets_by_id,
            window_sizes=window_sizes,
            max_windows=max_windows,
        )
        opener = str(bucket[0])
        bound_window: frozenset[str] | None = None
        for window in windows:
            if opener in window:
                bound_window = window
                break
        if bound_window is None:
            continue
        hero = max(
            bound_window,
            key=lambda aid: _quality_score(assets_by_id.get(aid, {}), pool),
        )
        if hero:
            out[ch_id] = hero
    return out
