"""PFM W0 · import reject, schema isolation, homepage default-hidden entry."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.config import AppConfig, PortfolioPipelineConfig
from travelogue.config.edition import E_PORTFOLIO_UNAVAILABLE
from travelogue.config.runtime import config_override
from travelogue.web.studio_handlers.import_handlers import handle_import
from travelogue.web.studio_jobs import reset_job_store

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[3]
_STUDIO = _REPO / "templates" / "studio"
_SCHEMA = _REPO / "schemas" / "trip.schema.json"


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _enabled_cfg() -> AppConfig:
    base = AppConfig()
    return replace(
        base,
        studio=replace(
            base.studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=True),
        ),
    )


def test_import_portfolio_rejected_when_flag_off(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": str(album), "edition": "portfolio", "forceStub": True},
    )
    with config_override(AppConfig()):
        handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body["error"] == E_PORTFOLIO_UNAVAILABLE
    assert "作品集" in body["message"]


def test_import_journal_omits_edition_and_proceeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": str(album), "title": "奈良", "force": True, "forceStub": True},
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
            return_value="album",
        ):
            handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload.get("edition") in (None, "", "journal")


def test_import_portfolio_accepted_when_flag_on(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={
            "albumPath": str(album),
            "edition": "portfolio",
            "title": "奈良作品集",
            "force": True,
            "forceStub": True,
        },
    )
    with config_override(_enabled_cfg()):
        with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
            with patch(
                "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
                return_value="album",
            ):
                handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload["edition"] == "portfolio"


def test_layout_engine_enum_has_no_third_value() -> None:
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    enum = schema["properties"]["layoutEngine"]["enum"]
    assert enum == ["legacy", "screens"]
    studio = schema["$defs"]["tripStudio"]["properties"]
    assert studio["edition"]["enum"] == ["journal", "portfolio"]
    assert "folio" not in studio["edition"]["enum"]


def test_homepage_portfolio_entry_exists_but_hidden_by_default() -> None:
    html = (_STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-cta-portfolio"' in html
    assert "做一本作品集" in html
    assert 'id="v2-cta-portfolio" hidden' in html or 'hidden>做一本作品集' in html
    assert "开始制作我的画册" in html
    edition = html[html.index('id="v2-wizard-edition"') : html.index('id="v2-wizard-edition"') + 80]
    assert "hidden" in edition
    assert "v2-wizard-page-count" not in html
    constants = (_STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    assert "E_PORTFOLIO_UNAVAILABLE" in constants
