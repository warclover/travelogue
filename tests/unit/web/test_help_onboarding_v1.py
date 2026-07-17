"""PRD-HELP-ONBOARDING-V1 · W0/W1 静态门禁（合同文案 · seen · 触点接线）。"""
from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
HELP_JS = STUDIO / "js" / "help-onboarding.js"
FIRST_SUCCESS = STUDIO / "homepage-v2" / "first-success.js"
INIT_V3 = STUDIO / "preview-toolbar" / "init-v3.js"
LONGSHOT = STUDIO / "preview-toolbar" / "longshot.js"
TASK_DOCK = STUDIO / "preview-toolbar-v3-task-dock.js"
HOME_HTML = STUDIO / "studio-home-v2.html"


def test_help_copy_contract_locked() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    assert "当前为本机文案；先翻一翻验货。满意就点预览页下方的『长图』" in help_js
    assert "验货没问题就点『长图』，生成可发微信的长图" in help_js
    assert "长图已保存到本机" in help_js
    assert "打开微信，按文件名顺序发到群聊" in help_js
    assert "可点『在文件夹中显示』找到文件" in help_js
    assert "应用排版" not in help_js
    assert "导出与更多" not in help_js
    assert "写给编辑的一句话" not in help_js


def test_help_seen_gate_global_only() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    assert "travelogue.studio.help.previewLongshotSeen" in help_js
    assert "travelogue.studio.help.exportPulseSeen" in help_js
    assert "migrateLongshotHelpSeen" in help_js
    assert "isHelpL1Blocked" in help_js
    assert "markLongshotHelpSeen" in help_js
    # 不再写 per-trip 门禁键
    assert 'LEGACY_EXPORT_PULSE_SEEN + "." + tripId' not in help_js
    assert "EXPORT_PULSE_SEEN_KEY + \".\" + tripId" not in LONGSHOT.read_text(encoding="utf-8")


def test_first_success_scheme_a() -> None:
    fs = FIRST_SUCCESS.read_text(encoding="utf-8")
    html = HOME_HTML.read_text(encoding="utf-8")
    assert "HELP_COPY.openPreviewCta" in fs
    assert "HELP_COPY.saveLongshotSecondary" in fs
    assert "HELP_COPY.firstSuccessNext" in fs
    assert 'v2-success-next-hint' in html
    assert "当前为本机文案；先翻一翻验货。满意就点预览页下方的『长图』" in html
    # 主 CTA 不再按 quick_share 切成「保存长图」
    assert '_successMode === "fine_craft" ? "打开卷轴预览' not in fs
    assert 'open.textContent = _successMode === "fine_craft"' not in fs
    assert "help_funnel_skip_preview" in fs


def test_preview_longshot_tip_and_busy_gate() -> None:
    init = INIT_V3.read_text(encoding="utf-8")
    longshot = LONGSHOT.read_text(encoding="utf-8")
    help_js = HELP_JS.read_text(encoding="utf-8")
    assert "maybeShowLongshotHelp" in init
    assert "onLongshotHelpTargetClick" in init
    assert "preview-help-longshot-tip" in help_js
    assert "queueLongshotHelpIdleEval" in longshot
    assert "isHelpL1Blocked" in help_js
    assert "studio-modal-open" in help_js


def test_task_dock_success_saved_confirm() -> None:
    """First-Session Trust supersede AC-FTUE-09 · 默认面已保存确认；H4 按需。"""
    dock = TASK_DOCK.read_text(encoding="utf-8")
    assert "长图已保存" in dock
    assert "怎么发到微信群？" in dock
    assert 'itemId: "H4"' in dock or "itemId: 'H4'" in dock
    assert "longshot_success_share_hint_shown" in dock
    assert "guide.text.replace" not in dock
    assert "已保存到本机 · 拖进微信群即可" not in dock


def test_import_folder_scaffold_markers() -> None:
    html = HOME_HTML.read_text(encoding="utf-8")
    assert "不知道选哪个文件夹？" in html
    assert "同一次旅行放同一文件夹（50–100 张最佳）" in html
    assert "手机照片需先传到电脑" in html
    assert "每个文件夹会生成一篇" in html
    assert "试试用自己的照片做一篇" in html
    assert 'data-help-item="H1"' in html


def test_help_w2_drawer_and_refine_save_markers() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    drawer = (STUDIO / "js" / "help-drawer.js").read_text(encoding="utf-8")
    css = (STUDIO / "help-drawer.css").read_text(encoding="utf-8")
    init = INIT_V3.read_text(encoding="utf-8")
    sheet = (STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    home_boot = (STUDIO / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    home_css = (STUDIO / "studio-home-v2.css").read_text(encoding="utf-8")
    preview_css = (STUDIO / "preview-toolbar.css").read_text(encoding="utf-8")

    assert "「完成」和「更新版面」有什么区别" in help_js
    assert "『完成』只是退出精修，不是更新版面" in help_js
    assert "replayHelpHints" in help_js
    assert "已重置。下次进入预览会再提示如何保存长图" in help_js

    assert "openHelpDrawer" in drawer
    assert "maybeInjectRefineSaveHint" in drawer
    assert "studio-help-drawer" in css
    assert "createHelpOpenButton" in init
    assert "isHelpOpen" in sheet
    assert "maybeInjectRefineSaveHint" in sheet
    assert "initHelpEntry" in home_boot
    assert "help-drawer.css" in home_css
    assert "help-drawer.css" in preview_css
    task_dock = TASK_DOCK.read_text(encoding="utf-8")
    assert "studio-help-open" not in task_dock


def test_help_w3_platform_pick_markers() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    longshot = LONGSHOT.read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    modal = (STUDIO / "studio-modal.js").read_text(encoding="utf-8")
    dock = TASK_DOCK.read_text(encoding="utf-8")
    assert "会按平台切成多张；页脚有顺序。失败可改回微信群长图" in help_js
    assert "maybeShowPlatformPickTip" in help_js
    assert "maybeShowPlatformPickTip" in longshot
    assert "platformPickTip" in panel
    assert "travelogue.studio.help.platformPickSeen" in help_js
    assert 'helpItemId: "H3"' in longshot
    assert "helpItemId" in modal
    assert 'itemId: "H4"' in dock
    assert "appendHelpDeepLink" in dock
    assert "helpDeepLinkPending" in dock
    assert '"H3"' in dock
    assert "helpDeepLinkPending" in help_js
    assert "isLongshotHelpActive" in help_js
    assert "isHelpLongshotDeferred" in help_js
    assert "切换分享平台、展开首尾装帧时也会再提示" in help_js
    assert "isLayoutPending: getLayoutPending" in INIT_V3.read_text(encoding="utf-8")
