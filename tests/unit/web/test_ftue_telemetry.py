"""FTUE Optimization V1 · telemetry allowlist + funnel emit contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.services.studio_homepage_telemetry import ALLOWED_STUDIO_HOMEPAGE_EVENTS

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"

FTUE_EVENTS = (
    "ftue_demo_album_click",
    "ftue_demo_album_success",
    "ftue_reveal_folder",
    "longshot_success_share_hint_shown",
    "help_funnel_reveal_folder",
)


def test_ftue_events_in_fe_and_be_allowlists() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in FTUE_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev


def test_ftue_demo_album_success_emitted() -> None:
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "ftue_demo_album_success" in run
    assert "useDemoAlbum" in run
    assert "重新生成（将覆盖）" in run


def test_ftue_reveal_folder_wired() -> None:
    shelf = (STUDIO / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "ftue_reveal_folder" in shelf
    assert "ftue_reveal_folder" in dock
    assert "ftue_reveal_folder" in longshot
