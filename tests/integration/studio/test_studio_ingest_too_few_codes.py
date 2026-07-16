"""P0 · Regular album too-few must surface E_INGEST_TOO_FEW (not E_DEMO_*)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.studio_test_helpers import make_test_album
from travelogue.demo.build import DemoError
from travelogue.web.studio_errors import job_error_payload, user_message
from travelogue.web.studio_pipeline import run_studio_pipeline


@pytest.mark.integration
def test_pipeline_three_photos_raises_ingest_too_few(tmp_path: Path) -> None:
    album = make_test_album(tmp_path, 3, name="few")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    with pytest.raises(DemoError) as excinfo:
        run_studio_pipeline(album, trips_dir=trips_dir, title="太少相册", dedupe=False)
    assert excinfo.value.code == "E_INGEST_TOO_FEW"
    assert excinfo.value.code != "E_DEMO_TOO_FEW"


@pytest.mark.integration
def test_pipeline_confirm_count_dupes_dedupe_to_too_few(tmp_path: Path) -> None:
    """Confirm-style folder can list 6 files while exact-dedupe leaves <4 assets."""
    album = make_test_album(tmp_path, 1, name="dupes")
    src = next(album.glob("*.jpg"))
    for i in range(5):
        shutil.copy2(src, album / f"copy-{i:02d}.jpg")
    assert len(list(album.glob("*.jpg"))) == 6

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    with pytest.raises(DemoError) as excinfo:
        run_studio_pipeline(album, trips_dir=trips_dir, title="连拍近似", dedupe=True)
    assert excinfo.value.code == "E_INGEST_TOO_FEW"

    payload = job_error_payload(excinfo.value.code, detail=str(excinfo.value))
    assert payload["code"] == "E_INGEST_TOO_FEW"
    msg = str(payload["message"])
    assert "至少需要 4 张照片" in msg
    assert "示例相册" not in msg
    assert "示例相册" not in user_message("E_INGEST_TOO_FEW", str(excinfo.value))
