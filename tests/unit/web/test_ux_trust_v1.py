# -*- coding: utf-8 -*-
"""Trust V1 · 静态门禁与标题启发式单测."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def assess_magazine_title_risk(title: str | None):
    """Mirror of longshot.js assessMagazineTitleRisk (附录 D · MF-TRU-07)."""
    t = (title or "").strip()
    if not t:
        return {"level": "severe", "reason": "empty"}
    if re.search(r"[\ufffd\x00-\x08]", t) or "�" in t:
        return {"level": "severe", "reason": "garbled"}
    if len(t) < 2:
        return {"level": "severe", "reason": "too_short"}
    if len(t) > 40:
        half = len(t) // 2
        if t[:half] == t[half : half * 2]:
            return {"level": "soft", "reason": "repeat_long"}
    if re.search(r"\S\+\S", t) and not re.match(r"^[A-Za-z0-9]+\+[A-Za-z0-9]+", t):
        return {"level": "soft", "reason": "plus_join"}
    if re.search(r"\+\s|\s\+", t) or re.search(r"^\+|\+$", t):
        return {"level": "soft", "reason": "plus_join"}
    return None


# 附录 D 正例 / 负例（PRD-UX-TRUST-V1 · MF-TRU-07）
APPENDIX_D_CASES = [
    # id, title, expect_level_or_None, expect_reason_or_None
    ("H+_empty", "", "severe", "empty"),
    ("H+_garbled", "�", "severe", "garbled"),
    ("H+_short", "啊", "severe", "too_short"),
    ("H+_repeat", ("京都" * 22), "soft", "repeat_long"),
    ("H~_plus_typo", "贵州+州兴义", "soft", "plus_join"),
    ("H-_art_plus", "A+B 旅行手记", None, None),
    ("H-_kyoto", "京都三日", None, None),
    ("H-_xingyi", "兴义夏天", None, None),
]


def test_preview_mode_module_exists():
    text = _read("templates/studio/preview-toolbar/preview-mode.js")
    assert "setPreviewRefineMode" in text
    assert "data-preview-refine" in text
    assert "syncInspectChromeVisibility" in text


def test_init_v3_sets_refine_default_and_drops_copy_stale():
    text = _read("templates/studio/preview-toolbar/init-v3.js")
    assert "ensurePreviewRefineDefault" in text
    assert "setPreviewRefineMode(true)" in text
    assert "setPreviewRefineMode(false)" in text
    assert "travelogue:copy-saved" in text
    assert "F-TRU-STALE-05" in text


def test_css_hides_inspect_chrome_when_refine_off():
    drawers = _read("templates/studio/preview-toolbar/drawers.css")
    assert 'data-preview-refine="off"' in drawers
    assert "featured-star" in drawers
    shell = _read("templates/studio/preview-toolbar/shell.css")
    assert "folio-plate-meta" in shell


def test_share_guards_and_inline_edit():
    share = _read("templates/studio/preview-toolbar/share.js")
    assert "setPreviewRefineMode(false)" in share
    assert "data-editable" in share
    assert "保存图片" in share
    assert 'aria-label="保存图片"' in share
    assert "platform: \"wechat_chat\"" in share or "platform: 'wechat_chat'" in share
    assert "stripEditableChrome" in share
    inline = _read("templates/visual-journal/inline-edit.js")
    assert "isSharePreview" in inline
    assert "data-preview-refine" in inline


def test_longshot_trust_contracts():
    text = _read("templates/studio/preview-toolbar/longshot.js")
    logic = _read("templates/studio/preview-toolbar/longshot-logic.js")
    share = _read("templates/studio/preview-toolbar/share.js")
    bundle = text + logic + share
    assert "EXPORT_SIDE_EFFECT_KEY" in text
    assert "writeExportSideEffect" in text
    assert "assessMagazineTitleRisk" in text
    assert "copy_gate_shown" in text
    assert "maybeCopyGateThenExport" in text
    assert "暂时不改，继续导出" in text
    assert "正在导出朋友圈长图连读" in text or "正在导出朋友圈九宫格" in text
    assert "服务已停止，长图还没有导出" in bundle
    assert "disconnectExportFeedback" in text
    assert "回到预览" in bundle
    assert "onError:" in text
    assert "EXPORT_RESUME_PLATFORM_KEY" in text
    assert "readResumePlatform" in text
    assert "syncPrefsPlatform" in text
    assert "导出排队超时" in text
    assert "长图还在排队" in text


def test_share_strips_editable_and_hint():
    share = _read("templates/studio/preview-toolbar/share.js")
    assert "stripEditableChrome" in share
    assert "screenplay-toolbar__hint" in share
    assert 'data-inline-edit", "off"' in share or "data-inline-edit\", \"off\"" in share
    inline = _read("templates/visual-journal/inline-edit.js")
    assert "if (isSharePreview()) return;" in inline
    journal = _read("templates/visual-journal/journal.css")
    assert 'data-preview-share="on"] [data-editable]' in journal


def test_layout_rerender_has_timeout():
    core = _read("templates/studio/preview-toolbar/core.js")
    assert "LAYOUT_RERENDER_TIMEOUT_MS" in core
    assert "E_LAYOUT_TIMEOUT" in core
    assert "layout_rerender_timeout" in core


def test_copy_gate_06b_marks_seen_on_first_show():
    text = _read("templates/studio/preview-toolbar/longshot.js")
    assert "F-TRU-COPY-06b" in text
    # seen 写在 gate shown 路径，而非仅 fix 成功后
    idx_shown = text.index("copy_gate_shown")
    idx_seen = text.index("首次出示即记 seen")
    idx_fix = text.index('trackStudioEvent("copy_gate_fix"')
    assert idx_shown < idx_seen < idx_fix


def test_assess_magazine_title_risk_markers():
    text = _read("templates/studio/preview-toolbar/longshot-logic.js")
    assert 'reason: "empty"' in text
    assert 'reason: "garbled"' in text
    assert 'reason: "plus_join"' in text
    assert 'reason: "too_short"' in text


@pytest.mark.parametrize(
    "case_id,title,level,reason",
    APPENDIX_D_CASES,
    ids=[c[0] for c in APPENDIX_D_CASES],
)
def test_appendix_d_title_risk_table(case_id, title, level, reason):
    """AC-TRU-01 / 01b · 附录 D 表驱动."""
    got = assess_magazine_title_risk(title)
    if level is None:
        assert got is None, case_id
    else:
        assert got is not None, case_id
        assert got["level"] == level, case_id
        assert got["reason"] == reason, case_id


def test_save_magazine_title_value_exported():
    text = _read("templates/studio/preview-toolbar/inline-edit.js")
    assert "export function saveMagazineTitleValue" in text
    assert "document.title" in text


def test_sheet_calls_on_sheet_closed():
    text = _read("templates/studio/preview-toolbar-v3-sheet.js")
    assert "onSheetClosed" in text


def test_task_dock_show_error_supports_disconnect_link():
    text = _read("templates/studio/preview-toolbar-v3-task-dock.js")
    assert "linkHref" in text
    assert "linkText" in text


def test_homepage_p2_denoise_no_user_facing_bento():
    """AC-TRU-22 / F-TRU-HOME-01～04 · 用户可见表面无 Bento；CTA 与导入偏好说明保留."""
    html = _read("templates/studio/studio-home-v2.html")
    stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    aria_labels = re.findall(r'aria-label="([^"]*)"', stripped)
    titles = re.findall(r'\btitle="([^"]*)"', stripped)
    visible_bits = aria_labels + titles
    visible_bits += re.findall(r">([^<>{}]+)<", stripped)
    joined = "\n".join(visible_bits)
    assert "Bento" not in joined
    assert "Bento" not in aria_labels
    assert 'id="v2-settings-desc"' in html
    assert "导入 · 外观 · AI 文案（可选）" in html
    assert 'id="v2-cta"' in html
    assert "开始制作我的游记" in html
    assert "你的游记画册" in _read("templates/studio/homepage-v2/shelf.js")
    assert "v2-shelf__title-h1" in _read("templates/studio/homepage-v2/css/shelf.css")


def test_inspect_forbidden_selectors_documented_in_css():
    """INSPECT-06 禁止选择器在 refine=off / share 下被 CSS 隐藏."""
    drawers = _read("templates/studio/preview-toolbar/drawers.css")
    shell = _read("templates/studio/preview-toolbar/shell.css")
    for sel in (
        "preview-toolbar__featured-star",
        "preview-toolbar__collage-ctrl",
    ):
        assert sel in drawers
    assert "folio-plate-meta" in shell
    assert 'data-preview-refine="off"' in drawers
    assert 'data-preview-share="on"' in drawers
