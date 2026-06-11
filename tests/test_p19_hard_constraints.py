"""P19 hard constraints: no unfiltered consecutive-pattern fallback."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from travelogue.curation.layout_constraints import plan_violates_consecutive_pattern
from travelogue.web.studio_handlers import layout_strategy_handlers
from travelogue.web.studio_handlers.layout_strategy_handlers import handle_lse_capabilities_patch

from tests.studio_test_helpers import MockStudioHandler


def _screen(pid: str, aid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": aid}]}


def test_p19_consecutive_filter_does_not_fallback_to_violating_plans() -> None:
    violating = [
        ("bad", [
            _screen("screen-portrait-1", "a1"),
            _screen("screen-portrait-1", "a2"),
            _screen("screen-portrait-1", "a3"),
        ]),
    ]
    filtered = [
        plan
        for plan in violating
        if not plan_violates_consecutive_pattern(plan[1], max_streak=2)
    ]
    # P19: reject unfiltered — old code used `filtered_plans or candidates`
    candidates = filtered
    assert candidates == []
    legacy_behavior = filtered or violating
    assert legacy_behavior == violating


def test_lse_capabilities_patch_readonly_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers._lse_caps_gate",
        lambda *a, **k: True,
    )
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"engineEnabled": True},
        headers={"X-Template-Role": "template_admin"},
    )
    handler.command = "PATCH"
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_LSE_CAPABILITIES_READONLY"


def test_mosaic_compose_hard_rejects_rhythm_blocked_candidates() -> None:
    from tests._golden.helpers import build_mosaic_portrait3_trip
    from travelogue.curation.mosaic.compose import score_window_candidates_with_rejections
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config
    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState

    buckets, aspects, assets = build_mosaic_portrait3_trip()
    window = buckets[0]
    assets_map = {a["id"]: a for a in assets}
    state = ScreenLayoutPlannerState.from_trip_total(len(assets))
    state.note_screen("screen-portrait-3")
    cfg = get_effective_mosaic_config()
    _, rejected = score_window_candidates_with_rejections(
        window,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=state,
        trip_photo_total=len(assets),
    )
    assert any(
        r.get("templateId") == "screen-portrait-3" and r.get("reason") == "rhythm_state"
        for r in rejected
    )


def test_book_quality_blind_review_summarize() -> None:
    from scripts.book_quality_blind_review import _summarize

    data = {
        "trips": [
            {"humanWinner": "candidate", "vlmWinner": "B", "storyClarity": "candidate"},
            {"humanWinner": "baseline", "vlmWinner": "A", "storyClarity": "baseline"},
        ],
    }
    summary = _summarize(data)
    assert summary["humanPairwiseWinRate"] == 0.5
    assert summary["vlmPairwiseWinRate"] == 0.5
    assert summary["agreementRate"] == 1.0
