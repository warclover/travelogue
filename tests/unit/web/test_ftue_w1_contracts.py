"""FTUE W1 · 敢发路径静态合同（AC-FTUE-06～10 · FE-04～08）。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"
VJ = ROOT / "templates" / "visual-journal"


def test_format_longshot_result_uses_resolve_publish_guide() -> None:
    src = (STUDIO / "js" / "longshot-client.js").read_text(encoding="utf-8")
    assert "resolvePublishGuide" in src
    assert "from \"./help-onboarding.js\"" in src


def test_shelf_longshot_emits_share_hint_event() -> None:
    src = (STUDIO / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    assert "longshot_success_share_hint_shown" in src
    assert "formatLongshotResult" in src


def test_import_run_maps_stage_hint_labels() -> None:
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "preparing_vision" in constants
    assert "正在准备本机视觉组件（仅第一次）" in constants
    assert "STAGE_HINT_LABELS" in run


def test_first_success_ftue_convert_hint() -> None:
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    fs = (STUDIO / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    assert "ftueConvertHint" in help_js
    assert "下一步可用自己的旅行照片再做一本" in help_js
    assert "ftueConvertHint" in fs


def test_inline_longshot_is_tertiary() -> None:
    hbs = (VJ / "partials" / "longshot-toolbar.hbs").read_text(encoding="utf-8")
    css = (VJ / "longshot.css").read_text(encoding="utf-8")
    assert "longshot-toolbar__btn--tertiary" in hbs
    assert "longshot-toolbar__btn--tertiary" in css


def test_cover_explain_no_system_sentence() -> None:
    shell = (STUDIO / "preview-toolbar" / "shell.js").read_text(encoding="utf-8")
    assert "备选有限，已选相对最合适的一款" not in shell


def test_stage_hints_module_frozen_copy() -> None:
    from travelogue.web.stage_hints import (
        PREPARING_BROWSER,
        PREPARING_VISION,
        PROCESSING_PHOTOS,
        stage_hint_text,
    )

    assert "本机视觉组件" in stage_hint_text(PREPARING_VISION)
    assert "仅第一次" in stage_hint_text(PREPARING_VISION)
    assert "长图组件" in stage_hint_text(PREPARING_BROWSER)
    assert "整理照片" in stage_hint_text(PROCESSING_PHOTOS)


def test_narrate_hook_no_fragment_word() -> None:
    narrate = (ROOT / "travelogue" / "services" / "narrate.py").read_text(encoding="utf-8")
    assert "张碎片拼成" not in narrate
    assert "张照片汇成" in narrate


def test_bootstrap_forces_vision_disabled() -> None:
    paths = (ROOT / "travelogue" / "paths.py").read_text(encoding="utf-8")
    assert "_force_bootstrap_vision_disabled" in paths
