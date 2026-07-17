"""QA-SR-05 / AC-SR-12 · stub hook forbidden instructional patterns."""

from __future__ import annotations

import re

from travelogue.services.narrate import run_narrate
from travelogue.services.narrative_scope import SCOPE_FRAME


def _trip(*, title: str = "周末近郊", place: str = "旅途") -> dict:
    return {
        "meta": {
            "title": title,
            "places": [place],
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-02",
            "hook": "",
        },
        "intent": {"placesUserSet": False},
        "assets": [
            {"id": "a1", "layoutEligible": True, "type": "image"},
            {"id": "a2", "layoutEligible": True, "type": "image"},
        ],
        "chapters": [{"id": "c1", "assetIds": ["a1", "a2"], "title": "一日"}],
    }


def test_ac_sr_12_stub_hook_no_instructional_patterns() -> None:
    trip = _trip(title="京都雨后", place="京都")
    run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    hook = str((trip.get("meta") or {}).get("hook") or "")
    assert hook, "有主体时应产出可读 hook"
    assert "京都" in hook or "雨后" in hook
    assert "汇成" not in hook
    assert "张照片" not in hook
    assert not re.search(r"关于.+的\d+天", hook)


def test_ac_sr_12_stub_hook_may_be_empty_without_subject() -> None:
    trip = _trip(title="", place="旅途")
    trip["meta"]["dateStart"] = ""
    trip["meta"]["dateEnd"] = ""
    run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    hook = str((trip.get("meta") or {}).get("hook") or "")
    assert hook == ""
    assert "汇成" not in hook
    assert not re.search(r"关于.+的\d+天", hook)
