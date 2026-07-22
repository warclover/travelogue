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

FST_EVENTS = (
    "import_ui_terminal_ms",
    "import_stage_stall",
    "longshot_progress_mode",
    "longshot_success_visible_ms",
    "longshot_reveal_auto_blocked",
    "share_surface_blocked",
)

SFC_EVENTS = (
    "sfc_vision_warmup_shown",
    "sfc_stub_blanked",
    "sfc_title_fallback",
    "sfc_g1_suppressed_sparse",
    "sfc_stale_label_impression",
    "stub_hits",
)

SFI_EVENTS = (
    "copy_refresh_shown",
    "copy_refresh_clicked",
    "copy_refresh_done",
    "copy_refresh_failed",
    "outlier_isolated",
    "export_renamed",
    "album_rerender_batch",
)


def test_ftue_events_in_fe_and_be_allowlists() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in FTUE_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev


def test_fst_events_in_fe_and_be_allowlists() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    for ev in FST_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev
    assert "import_ui_terminal_ms" in run
    assert "import_stage_stall" in run
    assert "longshot_progress_mode" in dock
    assert "longshot_reveal_auto_blocked" in dock
    assert "aria-busy" in dock
    assert "focusDockPrimary" in dock or "preventScroll" in dock


def test_sfc_events_in_fe_and_be_allowlists() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in SFC_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "sfc_vision_warmup_shown" in run
    assert "sfc_title_fallback" in run
    fs = (STUDIO / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    assert "sfc_g1_suppressed_sparse" in fs


def test_sfi_events_in_fe_and_be_allowlists() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in SFI_EVENTS:
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    assert "copy_refresh_shown" in dock
    assert "copy_refresh_clicked" in dock
    assert "copy_refresh_done" in core
    assert "copy_refresh_failed" in core
    assert "这次没写完，稍后再试" in core


def test_ftue_demo_album_success_emitted() -> None:
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "ftue_demo_album_success" in run
    assert "useDemoAlbum" in run
    assert "再做一遍" in run


def test_ftue_reveal_folder_wired() -> None:
    shelf = (STUDIO / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "ftue_reveal_folder" in shelf
    assert "ftue_reveal_folder" in dock
    assert "ftue_reveal_folder" in longshot
