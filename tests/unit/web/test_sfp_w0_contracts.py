"""Share-Face Purity · FE/源码契约（W0–W2）。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_chapter_export_mutual_exclusion_wired() -> None:
    chap = (STUDIO / "preview-toolbar" / "chapter-panel.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.css").read_text(encoding="utf-8")
    assert "closeStudioExportPopover" in chap
    assert "_chapterPanel.close" in longshot
    assert "z-index: 520" in dock or "z-index:520" in dock


def test_stale_badge_is_reorder_not_update() -> None:
    shelf = (STUDIO / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    bento = (STUDIO / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    picker = (STUDIO / "homepage-v2" / "bento-preview-picker-logic.js").read_text(encoding="utf-8")
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    assert 'STALE_BADGE = "可重排"' in shelf
    assert 'STALE_BADGE = "可重排"' in bento
    assert 'return "可重排"' in picker
    assert "可更新" not in shelf
    assert "可更新" not in bento
    assert "可更新" not in picker
    assert "版式算法有更新，可点重新排版" in shelf
    assert "「可重排」是什么意思" in help_js


def test_xhs_copy_pack_in_export_settings() -> None:
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert 'data-action="copy-xhs-pack"' in panel
    assert "标题和话题已备好" in panel
    assert "copy-xhs-pack" in longshot
    assert "sfp_xhs_copy_pack_copied" in longshot


def test_no_ai_promise_in_xhs_copy_ui() -> None:
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    for bad in ("AI 已写好", "杂志文案已完成", "AI 正文"):
        assert bad not in panel
        assert bad not in dock
