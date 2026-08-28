"""CLG W1 · 源合同锁（AC-CLG-09 / 14 / 15 · BLK-01 游记帮助）。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_f2_does_not_post_edition() -> None:
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    start = longshot.index("function handleCrossingGatePrimary")
    end = longshot.index("function handleCrossingGateSecondary")
    chunk = longshot[start:end]
    assert "postJson" not in chunk
    assert "/edition" not in chunk
    assert "root._onPortfolioToJournal" in chunk


def test_clg_handshake_skips_draft_and_blk05() -> None:
    wizard = (STUDIO / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    assert "shouldOpenSiblingInsteadOfOverwrite(_clgHandshake, _existingJournal)" in wizard
    assert 'albumPath = String(opts.albumPath || "").trim()' in wizard
    open_fn = wizard[wizard.index("export function openImportWizard") :]
    assert "restoreSessionIfAny(opts)" in open_fn
    album_branch = open_fn[: open_fn.index("if (opts.forceStep")]
    assert "afterFolderPicked(albumPath" in album_branch
    assert "restoreSessionIfAny" not in album_branch


def test_journal_help_wechat_longshot_untouched() -> None:
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    assert 'title: "怎么把长图发到微信群"' in help_js
    assert "过河可以出小红书、海报和印刷；长图要在游记里做。" in help_js


def test_sheet_escape_stays_on_f2() -> None:
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert 'if (pop.classList.contains("is-clg-open"))' in longshot
    assert "closeCrossingGateSheet(pop)" in longshot
    assert "CLG_SIBLING_TIMEOUT_MS" in longshot
    assert "crossingOpenJournalFailedSibling" in longshot
