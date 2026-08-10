"""Share Narrative Readiness · W0 源码契约（AC-SNR-06/07/11）。

不跑浏览器：互斥接线、关闭命中、金色 CTA 人话标签防漂移。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_snr_w0_export_closes_ai_and_refine() -> None:
    """AC-SNR-07 · 打开导出设置 ⇒ 关 AI Sheet / 精修。"""
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert 'root._aiSheet.close("export_settings")' in longshot
    assert 'root._sheet.close("export_settings")' in longshot
    assert "D-SNR-08" in longshot


def test_snr_w0_ai_open_still_closes_export() -> None:
    """AC-SNR-07 · 打开 AI ⇒ closePeers 含导出。"""
    ai = (STUDIO / "preview-toolbar" / "ai-sheet.js").read_text(encoding="utf-8")
    assert "function closePeers" in ai
    assert "closeStudioExportPopover()" in ai
    assert "root._chapterPanel.close()" in ai
    assert 'root._sheet.close("ai_sheet")' in ai


def test_snr_w0_ai_close_hit_and_escape() -> None:
    """AC-SNR-06 · × stopPropagation + Esc；导出区 pointer-events 失活。"""
    ai = (STUDIO / "preview-toolbar" / "ai-sheet.js").read_text(encoding="utf-8")
    css = (STUDIO / "preview-toolbar" / "ai-sheet.css").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar" / "dock.css").read_text(encoding="utf-8")
    assert 'close("close_btn")' in ai
    assert "e.stopPropagation()" in ai
    assert 'e.key !== "Escape"' in ai
    assert 'close("escape")' in ai
    assert "keydown" in ai
    assert ".preview-ai-sheet__close" in css
    assert "width: 40px" in css or "width:40px" in css
    assert "D-SNR-09" in css
    assert "max(" in css
    assert "body.preview-ai-sheet-open .preview-toolbar__dock" in dock
    assert "body.preview-ai-sheet-open .preview-toolbar__export-zone-wrap" in dock
    assert "pointer-events: none" in dock
    assert "D-SNR-09" in dock
    assert "pointer-events: auto" in dock


def test_snr_w0_cta_human_labels_not_n_modes() -> None:
    """AC-SNR-11 · 多选人话「等 N 项」；小红书短标签「导出小红书」。"""
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert 'return "导出 · " + _platformTitle(ids[0]) + "等 " + ids.length + " 项"' in panel
    assert 'return _platformTitle(ids[0]) + "等" + ids.length + "项"' in panel
    assert 'if (platformId === "xiaohongshu") return "导出小红书"' in panel
    assert 'return ids.length + " 个模式"' not in panel
    assert 'return "导出 " + ids.length + " 个模式"' not in panel
    assert "D-SNR-11" in panel
    assert "D-SNR-11" in longshot
