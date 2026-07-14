"""PRD-REFINE-FEEDBACK-LOOP-V1 · M1 静态门禁（首尾 tip · 精选诚实文案 · pending 3a）。"""
from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
HELP_JS = STUDIO / "js" / "help-onboarding.js"
FEATURES = STUDIO / "preview-toolbar" / "features.js"
BOOKENDS = STUDIO / "preview-toolbar" / "bookends.js"
LONGSHOT = STUDIO / "preview-toolbar" / "longshot.js"
SHEET = STUDIO / "preview-toolbar-v3-sheet.js"
TASK_DOCK = STUDIO / "preview-toolbar-v3-task-dock.js"


def test_bookends_pick_tip_contract() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    bookends = BOOKENDS.read_text(encoding="utf-8")
    assert "点下方缩略图，即可更换封面或封底" in help_js
    assert "bookendsPickSeen" in help_js
    assert "maybeShowBookendsPickTip" in help_js
    assert "maybeShowBookendsPickTip" in bookends
    assert "换封面 · 点选一张" in help_js
    assert "换封底 · 点选一张" in bookends or "bookendsOpeningLabel" in bookends
    assert "已换封面" in help_js
    assert 'id: "H6"' in help_js
    assert "怎么换封面封底" in help_js
    assert "clearBookendsPickSeen" in help_js


def test_featured_honest_copy_no_false_rerender_promise() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    features = FEATURES.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    assert "featuredPromotedToast" in features
    assert "已标为精选 · 会优先出现在『放映精选』" in help_js
    assert "已标为精选 · 点更新版面后生效" not in features
    # D-FEED-03 · 3a：promote 后不再 setLayoutPending(true)
    promote_block = features.split("promote-tier")[1].split("catch")[0]
    assert "setLayoutPending(true)" not in promote_block
    assert "不会立刻重排整本" in sheet
    assert "改精选请先点下方『更新版面』" not in help_js
    assert "精选不会立刻重排整本" in help_js
    # 拼图仍可说「点更新版面后生效」（渲染类）
    assert "已标记为拼图 · 点更新版面后生效" in features


def test_export_block_copy_media_only() -> None:
    longshot = LONGSHOT.read_text(encoding="utf-8")
    dock = TASK_DOCK.read_text(encoding="utf-8")
    assert "你改过精选或拼图" not in longshot
    assert "你改过拼图或版式相关设置" in longshot
    assert "改过精选或拼图后" not in dock
    assert "改过拼图或版式后" in dock


def test_m2_demote_and_featured_rerank_markers() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    features = FEATURES.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert "featuredDemotedToast" in help_js
    assert 'tier = "material"' in features or 'tier: "material"' in features
    assert "取消精选" in features
    assert "runFeaturedRerank" in features
    assert "runFeaturedRerank" in init
    assert 'data-action="featured-rerank"' in sheet
    assert "按精选重排" in sheet
    assert "featuredRerankTitle" in help_js
    assert "structure_locked" in features
    assert "help_funnel_tier_rerank_confirm" in features
    assert "按精选改构图" in help_js


def test_p0_dock_present_empty_toast_cover() -> None:
    """P0 收口：Dock 次 CTA、放映空池、toast→H2、封面更换 toast。"""
    help_js = HELP_JS.read_text(encoding="utf-8")
    features = FEATURES.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    dock = TASK_DOCK.read_text(encoding="utf-8")
    drawers_css = (STUDIO / "preview-toolbar" / "drawers.css").read_text(encoding="utf-8")
    entry = (
        Path(__file__).resolve().parents[3] / "travelogue" / "web" / "studio_entry.py"
    ).read_text(encoding="utf-8")

    assert "showFeaturedRerankCue" in dock
    assert "onFeaturedRerank" in init
    assert "showFeaturedRerankDockCue" in features
    assert "attachFeaturedHelpLinkOnToast" in features
    assert 'itemId: "H2"' in features or "itemId: 'H2'" in features
    assert "preview-toolbar__toast-link" in drawers_css
    assert "featuredPresentEmpty" in help_js
    assert "preview-sheet__present-empty" in sheet
    assert "featuredPresentEmptyText" in init
    assert "coverAssetId" in entry
    assert "featuredRerankDoneCover" in help_js
    assert "cover_changed" in features
