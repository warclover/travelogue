"""首页设置手风琴 · 静态契约（防遗漏 F5 清单）。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
HOME = STUDIO / "studio-home-v2.html"
SETTINGS_JS = STUDIO / "homepage-v2" / "settings-panel.js"
STORAGE_JS = STUDIO / "homepage-v2" / "storage-settings.js"
LLM_JS = STUDIO / "js" / "llm-settings.js"
ADVANCED_JS = STUDIO / "js" / "advanced.js"
BENTO_CSS = STUDIO / "homepage-v2" / "css" / "bento.css"


def test_settings_accordion_html_inventory() -> None:
    home = HOME.read_text(encoding="utf-8")
    for marker in (
        'class="v2-settings-zones"',
        'id="v2-settings-zone-appearance"',
        'id="v2-settings-zone-import"',
        'id="v2-settings-zone-ai"',
        'id="v2-settings-storage-section"',
        'id="v2-settings-zone-more"',
        "导入与分析",
        "导入偏好",
        'id="v2-theme-select"',
        'id="studio-cfg-clustering"',
        'id="studio-cfg-vision"',
        'id="studio-cfg-g1"',
        'id="studio-cfg-layout-scoring"',
        'id="v2-settings-experimental"',
        "实验选项（高级）",
        'id="studio-llm-settings-entry"',
        'id="studio-llm-settings-help"',
        'id="studio-llm-settings-badge"',
        'id="v2-settings-meta-appearance"',
        'id="v2-settings-meta-import"',
        'id="v2-settings-meta-ai"',
        'id="v2-settings-meta-storage"',
        'id="studio-storage-usage-line"',
        'id="studio-storage-mode-line"',
        'id="studio-cfg-copy-source"',
        'id="studio-storage-cleanup-btn"',
        'id="v2-settings-dev-section"',
        'id="v2-settings-dev-toggle"',
        'id="v2-settings-exit-section"',
        'id="v2-settings-exit-studio"',
        'data-seg-for="studio-cfg-clustering"',
        'data-seg-for="studio-cfg-vision"',
        'data-seg-for="studio-cfg-g1"',
        'data-seg-for="studio-cfg-layout-scoring"',
        'data-seg-for="studio-cfg-copy-source"',
        'id="v2-settings-zone-import"',
    ):
        assert marker in home, f"missing settings inventory marker: {marker}"
    # 默认折叠：勿再默认 open「导入与分析」
    assert 'id="v2-settings-zone-import" open' not in home
    # 不再动态注入 AI section
    assert 'aria-label="导入选项"' not in home
    assert "v2-settings-popover__section-label" not in home


def test_settings_accordion_js_behaviors() -> None:
    settings = SETTINGS_JS.read_text(encoding="utf-8")
    storage = STORAGE_JS.read_text(encoding="utf-8")
    llm = LLM_JS.read_text(encoding="utf-8")
    advanced = ADVANCED_JS.read_text(encoding="utf-8")
    css = BENTO_CSS.read_text(encoding="utf-8")

    assert "bindSegControls" in settings
    assert "focusZoneControl" in settings
    assert 'focusKey === "storage"' in settings
    assert 'focusKey === "ai"' in settings
    assert "syncMoreZone" in settings
    assert "refreshAiStatus" in settings
    assert "studio-llm-settings-root" in settings  # Modal 打开时不误关设置
    assert "syncImportMeta" in settings
    assert "syncAppearanceMeta" in settings
    assert "harnessEnabled()" in settings and "v2-settings-zone-more" in settings

    assert "v2-settings-meta-storage" in storage
    assert "占用较高，建议清理" in storage
    assert "refreshTripStorageMode" in storage
    assert "storage/cleanup" in storage

    assert "studio-llm-settings-entry" in llm
    assert "openLlmSettings" in llm
    assert "userDataDir" in llm and "tripsDir" in llm
    assert "showResumeAfterSave" in llm
    assert "LLM_KEY_LINKS" in llm
    # 不再 appendChild 注入 AI 区
    assert "appendChild(sec)" not in llm

    assert "syncSeg" in advanced
    assert "_patchQueued" in advanced
    assert "v2-settings-meta-import" in advanced

    assert ".v2-settings-zone" in css
    assert ".v2-settings-seg" in css
    assert ".v2-settings-native-select" in css
