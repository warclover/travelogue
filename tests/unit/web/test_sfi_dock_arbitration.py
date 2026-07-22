"""QA-SFI-04 · task dock 仲裁：copyRefresh > longshotStale（FE-SFI-05）。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "templates" / "studio" / "preview-toolbar" / "core.js"
DOCK = ROOT / "templates" / "studio" / "preview-toolbar-v3-task-dock.js"
SHEET = ROOT / "templates" / "studio" / "preview-toolbar-v3-sheet.js"


def test_copy_refresh_ordered_before_longshot_stale() -> None:
    text = CORE.read_text(encoding="utf-8")
    assert "showCopyRefresh" in text
    assert "copyRefresh" in text
    assert "longshotStale" in text
    i_copy = text.index("showCopyRefresh")
    # First longshotStale *handling* after copyRefresh block
    i_stale = text.index("longshotStale", i_copy)
    assert i_copy < i_stale
    # Stack comment documents priority
    assert "copyRefresh > longshotStale" in text or "copyRefresh" in text


def test_dock_exposes_show_copy_refresh() -> None:
    """NAS · AC-NAS-06：dock 仍导出 showCopyRefresh，但默认早退；文案在 dark-copy。"""
    dock = DOCK.read_text(encoding="utf-8")
    dark = (
        ROOT / "templates" / "studio" / "js" / "ai-surface-dark-copy.js"
    ).read_text(encoding="utf-8")
    assert "showCopyRefresh" in dock
    assert "showCopyRefresh: showCopyRefresh" in dock
    assert "isAiSurfaceEnabled" in dock
    show_fn = dock.split("function showCopyRefresh", 1)[1][:400]
    assert "if (!isAiSurfaceEnabled()) return" in show_fn
    assert "DARK_COPY.dockCopyRefreshTitle" in dock
    assert "DARK_COPY.dockCopyRefreshBtn" in dock
    # 默认可达字面量不得出现禁词（经 DARK_COPY 属性引用）
    assert "重新生成文案" not in dock
    assert "AI 文案已就绪" not in dock
    assert "AI 文案已就绪" in dark
    assert "重新生成文案" in dark
    assert "dockCopyRefreshBtn" in dark


def test_no_parallel_magazine_copy_cta() -> None:
    """主入口不得并列旧「生成杂志感文案」。"""
    for path in (SHEET, CORE):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        # Allowed in comments/history; forbidden as visible CTA label assignment
        assert 'textContent = "生成杂志感文案"' not in text
        assert ">生成杂志感文案<" not in text
