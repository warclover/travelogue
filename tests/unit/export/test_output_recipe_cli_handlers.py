"""Output Recipe V1 · CLI + handler 自动化（AC-OR-03c / 05 / 07a）。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tests.studio_test_helpers import MockStudioHandler
from travelogue.cli import app
from travelogue.config.studio import OutputRecipeBandsConfig, OutputRecipeConfig
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

runner = CliRunner()


def _enable_recipe(handler: MockStudioHandler, *, enabled: bool = True) -> None:
    handler.app_config.studio.output_recipe = OutputRecipeConfig(
        enabled=enabled,
        bands=OutputRecipeBandsConfig(
            sparse_max=9,
            ambiguous_max=30,
            narrative_chapter_hint_at=50,
        ),
    )


def _write_kept_n(trip_dir: Path, kept_n: int) -> None:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    curation = data.setdefault("curation", {})
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = kept_n
    cull["finalLayoutEligibleCount"] = kept_n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_ac_or_03c_cli_ambiguous_requires_intent(tmp_path: Path) -> None:
    """Ambiguous + CLI 无 --intent/--platform → 非 0."""
    from travelogue.config import get_config

    trips = tmp_path / "trips"
    create_trip("amb-cli", trips)
    trip_dir = trips / "amb-cli"
    _write_kept_n(trip_dir, 18)

    cfg = get_config()
    cfg.studio.output_recipe = OutputRecipeConfig(enabled=True)

    with patch("travelogue.cli.render_cmds.get_config", return_value=cfg):
        with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
            result = runner.invoke(app, ["export-longshot", str(trip_dir)])
    assert result.exit_code != 0
    assert "E_OR_INTENT_REQUIRED" in (result.stdout + result.stderr)


def test_ac_or_05_handle_output_recipe_and_illegal_intent(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.export_handlers import (
        handle_longshot,
        handle_output_recipe,
    )
    from travelogue.web.studio_jobs import reset_job_store

    trips = tmp_path / "trips"
    create_trip("or-api", trips)
    _write_kept_n(trips / "or-api", 12)

    handler = MockStudioHandler(
        trips,
        path="/__travelogue/output-recipe?tripId=or-api&entrypoint=preview",
    )
    _enable_recipe(handler)
    handle_output_recipe(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["recipe"]["needs_intent"] is True
    assert body["intentOptions"]
    option_intents = {o["intent"] for o in body["intentOptions"]}
    assert "moments_grid" in option_intents
    assert "moments_scroll" in option_intents

    # 非法 intent
    handler_bad = MockStudioHandler(
        trips,
        json_body={"tripId": "or-api", "intent": "not_an_intent", "entrypoint": "preview"},
    )
    _enable_recipe(handler_bad)
    handle_longshot(handler_bad)
    assert handler_bad.response is not None
    st_bad, body_bad = handler_bad.response
    assert st_bad == 400
    assert body_bad["error"] == "E_OR_INVALID_INTENT"

    # Phase B0 · moments_grid 可启动 Job
    reset_job_store()
    handler2 = MockStudioHandler(
        trips,
        json_body={"tripId": "or-api", "intent": "moments_grid", "entrypoint": "preview"},
    )
    _enable_recipe(handler2)
    with patch(
        "travelogue.export.longshot.playwright_longshot_available",
        return_value=True,
    ):
        handle_longshot(handler2)
    assert handler2.response is not None
    st2, body2 = handler2.response
    assert st2 == 202
    assert body2.get("ok") is True
    assert body2.get("jobId")


def test_ac_or_07a_handle_longshot_chat_and_scroll(tmp_path: Path) -> None:
    """chat_longshot / moments_scroll 各至少启动一条 Job（202）。"""
    from travelogue.export.output_recipe import resolve_output_recipe
    from travelogue.web.studio_handlers.export_handlers import handle_longshot
    from travelogue.web.studio_jobs import reset_job_store

    trips = tmp_path / "trips"
    create_trip("or-export", trips)
    _write_kept_n(trips / "or-export", 20)

    for intent, expect_platform in (
        ("chat_longshot", "wechat_chat"),
        ("moments_scroll", "wechat_moments"),
    ):
        reset_job_store()
        recipe = resolve_output_recipe(
            kept_n=20,
            enabled=True,
            intent=intent,
            entrypoint="preview",
        )
        assert recipe.platform == expect_platform

        handler = MockStudioHandler(
            trips,
            json_body={
                "tripId": "or-export",
                "intent": intent,
                "entrypoint": "preview",
                "scale": 1,
            },
        )
        _enable_recipe(handler)
        with patch(
            "travelogue.export.longshot.playwright_longshot_available",
            return_value=True,
        ):
            handle_longshot(handler)
        assert handler.response is not None
        status, body = handler.response
        assert status == 202, body
        assert body.get("jobId")


def test_ac_or_07b_cli_moments_grid_green(tmp_path: Path) -> None:
    """AC-OR-07b · CLI `--intent moments_grid` 端到端绿（分支 D，无 Playwright）."""
    from travelogue.config import get_config

    trips = tmp_path / "trips"
    create_trip("or-grid-cli", trips, title="九宫格CLI")
    trip_dir = trips / "or-grid-cli"

    # seed 3 kept photos（与 photo_grid_pack 单测同构）
    from PIL import Image

    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids = []
    for i in range(3):
        aid = f"cli-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        (trip_dir / "source").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (640, 480), (20 + i * 30, 90, 150)).save(
            trip_dir / rel, format="JPEG", quality=90
        )
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": rel,
                "layoutEligible": True,
            }
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = 3
    cull["finalLayoutEligibleCount"] = 3
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    cfg = get_config()
    cfg.studio.output_recipe = OutputRecipeConfig(enabled=True)

    with patch("travelogue.cli.render_cmds.get_config", return_value=cfg):
        with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
            result = runner.invoke(
                app,
                ["export-longshot", str(trip_dir), "--intent", "moments_grid", "--scale", "1"],
            )
    assert result.exit_code == 0, result.stdout + result.stderr
    out = result.stdout + result.stderr
    assert "OK export-longshot" in out
    assert "photo_grid" in out
    finals = list(trip_dir.glob("*-moments-grid-*.png"))
    assert len(finals) == 3
    assert "有几张发几张" in out or "九宫格" in out


def test_ac_or_07b_cli_help_lists_moments_grid() -> None:
    """CLI help 须暴露 moments_grid（B0 抛光）."""
    result = runner.invoke(app, ["export-longshot", "--help"])
    assert result.exit_code == 0
    assert "moments_grid" in result.stdout


def test_ac_or_13_flag_off_skips_needs_intent(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.export_handlers import handle_output_recipe

    trips = tmp_path / "trips"
    create_trip("or-off", trips)
    _write_kept_n(trips / "or-off", 15)

    handler = MockStudioHandler(
        trips,
        path="/__travelogue/output-recipe?tripId=or-off&entrypoint=preview",
    )
    _enable_recipe(handler, enabled=False)
    handle_output_recipe(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["recipe"]["needs_intent"] is False
    assert body["recipe"]["platform"] == "wechat_chat"
    assert body["recipe"]["source"] == "flag_disabled"


def test_resolve_cli_command_prints_json(tmp_path: Path) -> None:
    from travelogue.config import get_config

    trips = tmp_path / "trips"
    create_trip("or-resolve", trips)
    trip_dir = trips / "or-resolve"
    _write_kept_n(trip_dir, 5)

    cfg = get_config()
    cfg.studio.output_recipe = OutputRecipeConfig(enabled=True)
    with patch("travelogue.cli.render_cmds.get_config", return_value=cfg):
        with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
            result = runner.invoke(app, ["resolve-output-recipe", str(trip_dir)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["band"] == "sparse"
    assert payload["intent"] == "chat_longshot"
