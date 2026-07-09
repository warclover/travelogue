"""Studio POST /import passes template_mode to worker (PRD §6.3 · M50-GAP-06)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.web.studio_handlers.import_handlers import handle_import

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()


def test_handle_import_forwards_template_mode_manual(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    album = tmp_path / "album"
    album.mkdir()
    captured: dict = {}

    def _capture(_job, payload: dict, **_kwargs) -> None:
        captured.update(payload)

    handler = MockStudioHandler(
        trips_dir,
        json_body={
            "albumPath": str(album),
            "title": "模板测试",
            "template_mode": "manual",
            "template_id": "visual-journal",
        },
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess", side_effect=_capture):
        with patch("travelogue.web.studio_handlers.import_handlers.assert_album_importable"):
            handle_import(handler)

    assert handler.response is not None
    status, _body = handler.response
    assert status == 202
    assert captured.get("template_mode") == "manual"
    assert captured.get("template_id") == "visual-journal"
