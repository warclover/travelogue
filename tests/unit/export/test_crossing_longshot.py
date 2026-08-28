"""CLG · 作品集不得开导吃卷轴的两平台。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.export.crossing_longshot import (
    CrossingLongshotNeedsJournal,
    is_crossing_longshot_locked,
    reject_crossing_longshot_if_locked,
)


def _write_trip(trip_dir: Path, *, edition: str) -> None:
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps({"title": "t", "studio": {"edition": edition}}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_is_crossing_longshot_locked() -> None:
    assert is_crossing_longshot_locked("wechat_chat") is True
    assert is_crossing_longshot_locked("wechat_moments") is True
    assert is_crossing_longshot_locked("xiaohongshu") is False


def test_reject_portfolio_wechat() -> None:
    with pytest.raises(CrossingLongshotNeedsJournal) as exc:
        reject_crossing_longshot_if_locked("wechat_chat", folio=True)
    assert exc.value.code == "E_CLG_NEEDS_JOURNAL"
    reject_crossing_longshot_if_locked("xiaohongshu", folio=True)


def test_journal_wechat_not_rejected() -> None:
    reject_crossing_longshot_if_locked("wechat_chat", folio=False)


def test_dispatch_rejects_portfolio_wechat(tmp_path: Path) -> None:
    from travelogue.export.dispatch import dispatch_export

    pf = tmp_path / "pf-dispatch"
    _write_trip(pf, edition="portfolio")
    with pytest.raises(CrossingLongshotNeedsJournal):
        dispatch_export(pf, platform="wechat_chat")
    with pytest.raises(CrossingLongshotNeedsJournal):
        dispatch_export(pf, platform="wechat_moments")
