"""PFM · BE-PFM-17 CLI --edition / 作品集缺 --platform。"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from travelogue.cli import app
from travelogue.config import AppConfig, PortfolioPipelineConfig
from travelogue.config.edition import E_PORTFOLIO_PLATFORM_REQUIRED, E_PORTFOLIO_UNAVAILABLE
from travelogue.services.trip_factory import create_trip

runner = CliRunner()


def _stamp_portfolio(trip_dir: Path) -> None:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    studio = data.setdefault("studio", {})
    studio["edition"] = "portfolio"
    trip_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_export_longshot_portfolio_requires_platform(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("pf-cli", trips)
    trip_dir = trips / "pf-cli"
    _stamp_portfolio(trip_dir)

    with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
        result = runner.invoke(app, ["export-longshot", str(trip_dir)])
    text = result.stdout + result.stderr
    assert result.exit_code != 0
    assert E_PORTFOLIO_PLATFORM_REQUIRED in text
    assert "portfolio_pages" in text
    assert "wechat_chat" in text


def test_export_longshot_journal_omits_platform_still_defaults(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("j-cli", trips)
    trip_dir = trips / "j-cli"

    class _Ok:
        outputs = []
        user_hint = ""
        publish_guide = ""
        platform = "wechat_chat"

    with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
        with patch(
            "travelogue.export.longshot.export_trip_longshot",
            return_value=_Ok(),
        ) as export:
            result = runner.invoke(app, ["export-longshot", str(trip_dir)])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert export.call_args.kwargs["platform"] == "wechat_chat"


def test_export_longshot_portfolio_explicit_platform_proceeds(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("pf-ok", trips)
    trip_dir = trips / "pf-ok"
    _stamp_portfolio(trip_dir)

    class _Ok:
        outputs = []
        user_hint = ""
        publish_guide = ""
        platform = "wechat_chat"

    with patch("travelogue.cli.render_cmds._resolve", return_value=trip_dir):
        with patch(
            "travelogue.export.longshot.export_trip_longshot",
            return_value=_Ok(),
        ) as export:
            result = runner.invoke(
                app,
                ["export-longshot", str(trip_dir), "--platform", "wechat_chat"],
            )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert export.call_args.kwargs["platform"] == "wechat_chat"


def test_curate_edition_portfolio_flag_off(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("pf-off", trips)
    trip_dir = trips / "pf-off"
    result = runner.invoke(app, ["curate", str(trip_dir), "--edition", "portfolio"])
    text = result.stdout + result.stderr
    assert result.exit_code != 0
    assert E_PORTFOLIO_UNAVAILABLE in text


def test_curate_edition_portfolio_flag_on_stamps(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("pf-on", trips)
    trip_dir = trips / "pf-on"
    cfg = replace(
        AppConfig(),
        studio=replace(
            AppConfig().studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=True),
        ),
    )

    def _curate(trip, **_k):
        class _R:
            chapter_count = 0
            layout_summary = "ok"

        return _R()

    with patch("travelogue.cli.pipeline.get_config", return_value=cfg):
        with patch("travelogue.cli.pipeline.run_curate", side_effect=_curate):
            result = runner.invoke(
                app,
                ["curate", str(trip_dir), "--edition", "portfolio", "--layout", "auto"],
            )
    assert result.exit_code == 0, result.stdout + result.stderr
    data = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assert data["studio"]["edition"] == "portfolio"
