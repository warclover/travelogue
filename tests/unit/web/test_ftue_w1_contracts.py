"""FTUE W1 · 敢发路径静态合同（AC-FTUE-06～10 · FE-04～08）。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"
VJ = ROOT / "templates" / "visual-journal"


def test_format_longshot_result_saved_confirm_not_publish_guide() -> None:
    """First-Session Trust · 默认成功文案 = 已保存，不塞 resolvePublishGuide。"""
    src = (STUDIO / "js" / "longshot-client.js").read_text(encoding="utf-8")
    assert "successLineForPlatform" in src
    assert "resolvePublishGuide" not in src


def test_shelf_longshot_emits_share_hint_event() -> None:
    src = (STUDIO / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    assert "formatLongshotResult" in src
    # FE-SR-08 / USR-03 · 书架成功面也提供换种分享
    assert "换种分享方式" in src
    assert "offerShelfSwitchShare" in src
    # D-FST-13 · 禁自动 reveal
    assert "shelf_longshot_auto_reveal" not in src
    assert "禁止自动 reveal" in src


def test_import_run_maps_stage_hint_labels() -> None:
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    logic = (STUDIO / "homepage-v2" / "import-run-logic.js").read_text(encoding="utf-8")
    assert "preparing_vision" in constants
    assert "vision_warmup" in constants
    assert "正在准备识图" in constants
    assert "resolveImportStageCopy" in logic
    assert "resolveImportStageCopy" in run
    pipeline = (
        ROOT / "travelogue" / "web" / "studio_pipeline.py"
    ).read_text(encoding="utf-8")
    assert "maybe_sleep_vision_warmup_inject" in pipeline
    assert "sfc_vision_warmup_shown" in (
        ROOT / "templates" / "studio" / "js" / "analytics.js"
    ).read_text(encoding="utf-8")
    assert "sfc_vision_warmup_shown" in run
    # FE-FST-02 · FirstSuccess 不阻塞于 refreshTrips
    assert "showFirstSuccess({ result: result })" in run


def test_first_success_ftue_convert_hint() -> None:
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    fs = (STUDIO / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    assert "ftueConvertHint" in help_js
    assert "下一步可用自己的画册照片再做一本" in help_js
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

    assert "准备识图" in stage_hint_text(PREPARING_VISION)
    assert "长图组件" in stage_hint_text(PREPARING_BROWSER)
    assert "整理照片" in stage_hint_text(PROCESSING_PHOTOS)


def test_narrate_hook_no_fragment_word() -> None:
    """行为断言：stub hook 不含说明书腔 / 碎片拼成语（非源码扫串）。"""
    import re

    from travelogue.services.narrate import run_narrate
    from travelogue.services.narrative_scope import SCOPE_FRAME

    trip = {
        "meta": {
            "title": "京都雨后",
            "places": ["京都"],
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-03",
            "hook": "",
        },
        "intent": {"placesUserSet": True},
        "assets": [
            {"id": "a1", "layoutEligible": True, "type": "image"},
            {"id": "a2", "layoutEligible": True, "type": "image"},
        ],
        "chapters": [{"id": "c1", "assetIds": ["a1", "a2"], "title": "一日"}],
    }
    run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    hook = str((trip.get("meta") or {}).get("hook") or "")
    assert "张碎片拼成" not in hook
    assert "汇成" not in hook
    assert "张照片" not in hook
    assert not re.search(r"关于.+的\d+天", hook)


def test_bootstrap_forces_vision_disabled() -> None:
    paths = (ROOT / "travelogue" / "paths.py").read_text(encoding="utf-8")
    assert "_force_bootstrap_vision_disabled" in paths
