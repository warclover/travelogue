"""CLG · 作品集不得开导吃卷轴的两平台。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.export.crossing_longshot import (
    CrossingLongshotNeedsJournal,
    is_crossing_longshot_locked,
    reject_portfolio_crossing_longshot,
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


def test_reject_portfolio_wechat(tmp_path: Path) -> None:
    pf = tmp_path / "pf"
    _write_trip(pf, edition="portfolio")
    with pytest.raises(CrossingLongshotNeedsJournal) as exc:
        reject_portfolio_crossing_longshot(pf, "wechat_chat")
    assert exc.value.code == "E_CLG_NEEDS_JOURNAL"
    reject_portfolio_crossing_longshot(pf, "xiaohongshu")


def test_journal_wechat_not_rejected(tmp_path: Path) -> None:
    journal = tmp_path / "j"
    _write_trip(journal, edition="journal")
    reject_portfolio_crossing_longshot(journal, "wechat_chat")


def test_dispatch_rejects_portfolio_wechat(tmp_path: Path) -> None:
    from travelogue.export.dispatch import dispatch_export

    pf = tmp_path / "pf-dispatch"
    _write_trip(pf, edition="portfolio")
    with pytest.raises(CrossingLongshotNeedsJournal):
        dispatch_export(pf, platform="wechat_chat")
    with pytest.raises(CrossingLongshotNeedsJournal):
        dispatch_export(pf, platform="wechat_moments")
