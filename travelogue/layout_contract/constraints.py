"""Layout constraint constants shared by planner and LSE (M-B4a kernel)."""

FOCAL_EDGE_MARGIN = 0.15

DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN = 2


def max_consecutive_pattern_streak(screens: list[dict]) -> int:
    streak = 0
    best = 0
    prev: str | None = None
    for screen in screens:
        pid = screen.get("patternId")
        if not pid:
            streak = 0
            prev = None
            continue
        if pid == prev:
            streak += 1
        else:
            streak = 1
            prev = pid
        best = max(best, streak)
    return best


def plan_violates_consecutive_pattern(
    screens: list[dict],
    *,
    max_streak: int = DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
) -> bool:
    return max_consecutive_pattern_streak(screens) > max_streak
