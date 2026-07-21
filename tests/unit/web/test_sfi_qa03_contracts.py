"""Share-Face Integrity · QA-SFI-03 / AC-SFI-10·11 工程契约。

- AC-SFC-01/03/07：禁入句与 stale 主词不回退（复用 SFC 源契约）
- AC-SFC-11：无 Key 无「杂志文案已完成」
- AC-SFI-11 前置：FST W0 忙碌态（aria-busy · import_stage_stall）已落地
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"
DOMAIN = ROOT / "travelogue" / "domain"


def test_stale_primary_copy_not_regressed() -> None:
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    bento = (STUDIO / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    assert "分享图需更新" in dock or "分享图需更新" in bento
    for bad in ("长图可更新", "长图待更新", "长图已过期", "预览产物已过期"):
        assert bad not in dock
        assert bad not in bento


def test_share_face_copy_filter_still_wired() -> None:
    sfc = (DOMAIN / "share_face_copy.py").read_text(encoding="utf-8")
    assemble = (ROOT / "travelogue" / "render" / "assemble.py").read_text(
        encoding="utf-8"
    )
    assert "share_face_copy" in assemble or "apply_share_face" in assemble
    assert "stub_hits" in sfc


def test_no_magazine_copy_done_without_key_copy() -> None:
    """AC-SFC-11 · 无 Key 不得出现「杂志文案已完成」类完成态。"""
    targets = [
        STUDIO / "homepage-v2" / "first-success.js",
        STUDIO / "homepage-v2" / "bento.js",
        STUDIO / "js" / "llm-settings.js",
        STUDIO / "preview-toolbar-v3-sheet.js",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "杂志文案已完成" not in text, path.name


def test_fst_busy_shell_preflight_landed() -> None:
    """AC-SFI-11 前置核验：FST W0 忙碌态工程已合入（非空转）。"""
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert 'setAttribute("aria-busy", "true")' in run
    assert "import_stage_stall" in run
    fst_ac = (ROOT / "docs" / "ACCEPTANCE-FIRST-SESSION-TRUST-V1.md").read_text(
        encoding="utf-8"
    )
    assert "W0–W2 工程已合入" in fst_ac or "| **W0** |" in fst_ac


def test_chapter_titles_forbid_xu_suffix() -> None:
    src = (ROOT / "travelogue" / "curation" / "chapter_titles.py").read_text(
        encoding="utf-8"
    )
    assert 'f"{base}续"' not in src
