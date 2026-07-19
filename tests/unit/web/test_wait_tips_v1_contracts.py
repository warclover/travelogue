"""Wait Tips V1 · 文案契约 / dismiss / 不碰 Help seen / 挂载锚点。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
COPY_JS = STUDIO / "homepage-v2" / "wait-tips-copy.js"
CTRL_JS = STUDIO / "homepage-v2" / "wait-tips.js"
IMPORT_JS = STUDIO / "homepage-v2" / "import-run.js"
ANALYTICS = STUDIO / "js" / "analytics.js"
HELP_JS = STUDIO / "js" / "help-onboarding.js"
OVERLAYS = STUDIO / "homepage-v2" / "css" / "overlays.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_wait_tips_six_cards_match_prd_section4() -> None:
    copy = _read(COPY_JS)
    assert 'COPY_VERSION = "0.2.0"' in copy
    assert 'id: "WT-01"' in copy
    assert 'id: "WT-06"' in copy
    assert "可翻的卷轴，可发的长图" in copy
    assert "回忆，只放在你身边" in copy
    assert "分章配文排版，交给它" in copy
    assert "先翻卷轴，再存长图" in copy
    assert "没有照片？先用示例" in copy
    assert "一趟旅行，一个文件夹" in copy
    # WT-02 禁止功能说明式标题
    assert "照片留在本机" not in copy
    # 禁区
    assert "主链" not in copy
    assert "为的是" not in copy
    assert "微信" not in copy
    assert "精修" not in copy
    assert "API Key" not in copy
    assert "杂志" not in copy


def test_wait_tips_dismiss_key_and_no_help_seen() -> None:
    copy = _read(COPY_JS)
    ctrl = _read(CTRL_JS)
    assert "travelogue.waitTips.dismissed" in copy
    assert "DISMISS_KEY" in ctrl
    assert "localStorage.setItem" in ctrl or "_lsSet(DISMISS_KEY" in ctrl
    # 不得碰 Help seen
    assert "helpL1" not in ctrl
    assert "capabilityCard" not in ctrl
    assert "markHelp" not in ctrl
    assert "clearCapabilityCardSeen" not in ctrl


def test_wait_tips_host_hooks_in_import_run() -> None:
    imp = _read(IMPORT_JS)
    assert 'from "./wait-tips.js"' in imp
    assert "scheduleWaitTips" in imp
    assert "unmountWaitTips" in imp
    assert "pauseWaitTips" in imp
    assert "resumeWaitTips" in imp
    assert "notifyWaitTipsJob" in imp
    assert "beforeEl: cancelBtn" in imp
    assert "mountWaitTipsRestoreChip" in imp
    ctrl = _read(CTRL_JS)
    assert "remountWaitTipsIfImporting" in ctrl
    assert "force: true" in ctrl or "opts.force" in ctrl
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    assert "remountWaitTipsIfImporting" in help_js


def test_wait_tips_analytics_allowlist() -> None:
    analytics = _read(ANALYTICS)
    for ev in (
        "wait_tips_show",
        "wait_tips_auto_advance",
        "wait_tips_manual_nav",
        "wait_tips_pause",
        "wait_tips_dismiss",
        "wait_tips_suppress_short_wait",
    ):
        assert ev in analytics


def test_wait_tips_css_and_a11y_markers() -> None:
    ctrl = _read(CTRL_JS)
    css = _read(OVERLAYS)
    assert "aria-roledescription" in ctrl
    assert "轮播" in ctrl
    assert "prefers-reduced-motion" in ctrl
    assert "v2-wait-tips" in css
    assert "v2-wait-tips__label" in css


def test_wait_tips_does_not_alter_help_busy_contract() -> None:
    """Tips 不是 L1；Help 忙碌态合同仍在 help-onboarding。"""
    help_js = _read(HELP_JS)
    assert "isHelpL1Blocked" in help_js or "busy" in help_js.lower()
    ctrl = _read(CTRL_JS)
    assert "openHelpDrawer" not in ctrl


def test_wait_tips_w2_help_replay() -> None:
    help_js = _read(HELP_JS)
    drawer = _read(STUDIO / "js" / "help-drawer.js")
    assert "replayWaitTips" in help_js
    assert "重播等待提示" in help_js
    assert "remountWaitTipsIfImporting" in help_js
    assert "已重新打开功能介绍与使用技巧" in help_js
    assert "clearWaitTipsDismissed" in help_js
    assert "WAIT_TIPS_DISMISS_KEY" in help_js
    assert "waitTips.dismissed" in _read(COPY_JS)
    assert "replayWaitTips" in drawer
    assert "重播等待提示" in drawer
