"""CLG · 过河不得开导吃卷轴的两平台（身份判断在 S-07 dispatch）。"""

from __future__ import annotations

from travelogue.errors import CodeError

CROSSING_LONGSHOT_LOCKED = frozenset({"wechat_chat", "wechat_moments"})
CLG_NEEDS_JOURNAL_MESSAGE = "长图要在游记里做"


class CrossingLongshotNeedsJournal(CodeError):
    def __init__(self, message: str = CLG_NEEDS_JOURNAL_MESSAGE) -> None:
        super().__init__("E_CLG_NEEDS_JOURNAL", message)


def is_crossing_longshot_locked(platform: str | None) -> bool:
    return str(platform or "").strip() in CROSSING_LONGSHOT_LOCKED


def reject_crossing_longshot_if_locked(platform: str | None, *, folio: bool) -> None:
    if folio and is_crossing_longshot_locked(platform):
        raise CrossingLongshotNeedsJournal()
