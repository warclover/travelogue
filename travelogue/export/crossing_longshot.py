"""CLG · 作品集过河不得开导吃卷轴的两平台。"""

from __future__ import annotations

from pathlib import Path

from travelogue.errors import CodeError

CROSSING_LONGSHOT_LOCKED = frozenset({"wechat_chat", "wechat_moments"})
CLG_NEEDS_JOURNAL_MESSAGE = "长图要在游记里做"


class CrossingLongshotNeedsJournal(CodeError):
    def __init__(self, message: str = CLG_NEEDS_JOURNAL_MESSAGE) -> None:
        super().__init__("E_CLG_NEEDS_JOURNAL", message)


def is_crossing_longshot_locked(platform: str | None) -> bool:
    return str(platform or "").strip() in CROSSING_LONGSHOT_LOCKED


def reject_portfolio_crossing_longshot(trip_dir: Path, platform: str | None) -> None:
    from travelogue.export.portfolio_wechat import trip_is_portfolio

    if trip_is_portfolio(trip_dir) and is_crossing_longshot_locked(platform):
        raise CrossingLongshotNeedsJournal()
