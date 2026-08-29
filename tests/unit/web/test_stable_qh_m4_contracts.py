"""Stable-QH M4 · 瘦身观感源码契约（T-M4-01～08）。"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_STUDIO = _ROOT / "templates" / "studio"
_VJ = _ROOT / "templates" / "visual-journal"


def test_m4_01_assemble_no_draft_system_hook_bypass() -> None:
    assemble = (_ROOT / "travelogue" / "render" / "assemble.py").read_text(encoding="utf-8")
    assert "show_cover_hook = show_hook_on_cover(hook)" in assemble
    assert "show_hook_in_draft" not in assemble


def test_m4_02_chapter_titles_forbid_date_er() -> None:
    """First-Session Trust supersede · 禁「日期续」；用时段 / （n）。"""
    src = (_ROOT / "travelogue" / "curation" / "chapter_titles.py").read_text(encoding="utf-8")
    assert 'f"{base}·二"' not in src
    assert 'f"{base}·{n + 1}"' not in src
    assert 'f"{base}续"' not in src
    assert "（{n + 1}）" in src or "（" in src
    assert "慢慢翻" not in src


def test_m4_03_shelf_badge_demotes_when_resume_owns_cta() -> None:
    logic = (_STUDIO / "homepage-v2" / "shelf-actions-logic.js").read_text(encoding="utf-8")
    shelf = (_STUDIO / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "shelfShowCoverLongshotBadge" in logic
    assert "shelfShowCoverLongshotBadge" in shelf
    assert "按原配方重出" in logic


def test_m4_06_longshot_export_cooperative_cancel_cta() -> None:
    """LCC V1 supersedes Stable-QH honest-only cancel (OUT-06)."""
    dock = (_STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    assert "取消导出" in dock
    assert "导出开始后无法取消" not in dock
    assert "hooks.onCancelExport" in dock
    longshot = (_STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "longshot_export_cancel" in longshot
    assert "已取消导出" in longshot
    assert "停止导出？" in longshot
    assert "isLiveLongshotExport" in longshot
    assert "cancelOrphanLongshotJob" in longshot
    assert "_longshotCancelConfirmP" in longshot
    idx = longshot.index("function cancelPreviewLongshotExport")
    chunk = longshot[idx : idx + 2800]
    assert "if (_longshotCancelConfirmP) return _longshotCancelConfirmP" in chunk
    assert "nextLongshotExportGen()" in chunk


def test_m4_07_capture_object_fit_split() -> None:
    css = (_VJ / "longshot.css").read_text(encoding="utf-8")
    js = (_VJ / "longshot.js").read_text(encoding="utf-8")
    assert "object-fit: cover" in css
    assert "object-fit: contain" in css
    assert 'objectFit = isCover ? "cover" : "contain"' in js
    assert 'objectFit = "fill"' not in js
    # 捕获态规则块内不再使用 fill
    assert "longshot-capturing" in css
    for block in css.split("body.longshot-capturing"):
        if "object-fit: fill" in block and (
            "cover-hero__media" in block or "media-card__visual" in block
        ):
            raise AssertionError("capture object-fit still uses fill for cover/media")


def test_m4_08_experimental_settings_folded() -> None:
    html = (_STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-settings-experimental"' in html
    assert "实验选项" in html
    assert "导入后先确认章节" in html
    assert "结构确认（G1）" not in html
    assert "beam 评分" not in html
