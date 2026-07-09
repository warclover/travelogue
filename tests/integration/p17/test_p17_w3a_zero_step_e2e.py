"""P17 W3a zero-step import E2E · AC-P17-23."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from tests.integration.studio.test_studio_server import (
    _distinct_album,
    _free_port,
    _get_json,
    _post_json,
)
from tests.studio_test_helpers import wait_for_job
from travelogue.services.validate import validate_trip
from travelogue.web.serve import TripPreviewHandler
from travelogue.web.studio_jobs import reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline

pytestmark = [pytest.mark.e2e, pytest.mark.w3a_gate]


def _start_server(trips_dir: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.mark.integration
def test_ac_p17_23_quick_share_pipeline_zero_step(tmp_path: Path) -> None:
    """导入→成稿单路径：无 layoutDensity intent、有 screens、可渲染。"""
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="零步测试",
        place="测试",
        dedupe=False,
        mode="quick_share",
        layout_density="hero_first",
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert result.import_mode == "quick_share"
    assert "layoutDensity" not in trip.get("intent", {})
    screens = [s for ch in trip.get("chapters") or [] for s in ch.get("screens") or []]
    assert len(screens) >= 1
    assert (result.trip_dir / "index.html").is_file()
    assert validate_trip(trip, level="schema") == []


def test_ac_p17_23_studio_import_job_quick_share_no_extra_step(tmp_path: Path) -> None:
    """HTTP 导入 job：quick_share 一次提交直达 preview，无二次排版确认。"""
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {
                "albumPath": str(album),
                "title": "零步 E2E",
                "place": "测试",
                "mode": "quick_share",
                "layoutDensity": "hero_first",
            },
        )
        assert status == 202
        job_id = body["jobId"]

        def _fetch() -> dict:
            _status, payload = _get_json(f"{base}/__travelogue/status?jobId={job_id}")
            assert _status == 200
            return payload

        last = wait_for_job(_fetch, timeout_sec=180, poll_sec=0.05)
        assert last.get("status") == "succeeded", last
        trip_id = last["tripId"]
        trip = json.loads((trips_dir / trip_id / "trip.json").read_text(encoding="utf-8"))
        assert "layoutDensity" not in trip.get("intent", {})
        assert (trips_dir / trip_id / "index.html").is_file()
        result = last.get("result") or {}
        assert str(result.get("importMode") or result.get("import_mode") or "").lower() in (
            "quick_share",
            "",
        )
    finally:
        server.shutdown()
        server.server_close()
