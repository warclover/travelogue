"""G1: lock structure → narrate → dual render (fixture workspace)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.orchestrator.run import run_trip
from travelogue.paths import FIXTURES_DIR, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip_surfaces
from travelogue.services.narrate import run_narrate

RENDER_GOLDEN = FIXTURES_DIR / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def g1_workspace(tmp_path: Path) -> Path:
    if not RENDER_GOLDEN.is_file():
        pytest.skip("fixture missing")
    if not DEMO_ASSETS.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "trips" / "g1-fixture"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    trip = json.loads(RENDER_GOLDEN.read_text(encoding="utf-8"))

    def _touch(rel: str) -> None:
        if not rel:
            return
        path = ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file():
            path.write_bytes(b"\x00")

    for a in trip.get("assets", []):
        _touch(a.get("displayFile", ""))
        for e in a.get("srcset") or []:
            _touch(e.get("file", ""))
        voice = a.get("voice") or {}
        _touch(voice.get("audioFile", ""))
        if a.get("type") == "video":
            _touch(a.get("displayFile", ""))
    trip["exportLayout"] = "auto"
    trip["layoutEngine"] = "screens"
    trip["meta"]["hook"] = ""
    trip["epilogue"] = ""
    for ch in trip.get("chapters", []):
        ch["lead"] = ""
    trip["pipeline"] = {
        "status": "structure_locked",
        "locks": {"structure": True, "copy": False},
        "runs": [],
    }
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_g1_narrate_then_dual_render(g1_workspace: Path) -> None:
    trip_path = g1_workspace / "trip.json"
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assert trip["pipeline"]["status"] == "structure_locked"

    before_hook = trip["meta"].get("hook", "")
    result = run_narrate(trip, provider="stub")
    assert "meta.hook" in result.fields_updated
    assert trip["meta"]["hook"] and trip["meta"]["hook"] != before_hook
    assert all(ch.get("lead") for ch in trip["chapters"])
    assert len({ch["lead"] for ch in trip["chapters"]}) == len(trip["chapters"])
    assert trip["pipeline"]["status"] == "copy_draft"
    trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    web, mobile = render_trip_surfaces(trip_path, validate=False)
    web_html = web.read_text(encoding="utf-8")
    mobile_html = mobile.read_text(encoding="utf-8")
    assert trip["meta"]["hook"] in web_html
    assert 'data-layout="web"' in web_html
    assert 'data-layout="mobile"' in mobile_html


def test_run_trip_from_lock_structure(g1_workspace: Path) -> None:
    run_result = run_trip(
        g1_workspace / "trip.json",
        from_stage="lock_structure",
        until="render",
        validate=False,
        skip_locked=True,
        narrate_provider="stub",
    )
    assert "narrate" in run_result.stages
    assert "render" in run_result.stages
    trip = json.loads((g1_workspace / "trip.json").read_text(encoding="utf-8"))
    assert trip["meta"]["hook"]
    assert (g1_workspace / "index.html").is_file()
    assert (g1_workspace / "index-mobile.html").is_file()


def test_narrate_before_structure_locked_rejected(g1_workspace: Path) -> None:
    trip = json.loads((g1_workspace / "trip.json").read_text(encoding="utf-8"))
    trip["pipeline"]["status"] = "structure_draft"
    trip["pipeline"]["locks"]["structure"] = False
    from travelogue.services.pipeline_state import assert_stage_allowed

    with pytest.raises(Exception) as exc:
        assert_stage_allowed(trip, "narrate")
    assert "structure_locked" in str(exc.value)
