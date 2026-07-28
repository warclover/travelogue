"""FTUE Optimization V1 · W0 static contracts (AC-FTUE-02/03/04)."""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"


def test_empty_state_resume_not_in_html() -> None:
    html = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-bench-resume"' not in html
    assert 'id="v2-bench-quick-actions"' in html
    bento = (STUDIO / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    assert "syncBenchResumeButton" in bento
    assert "removeChild(resumeBtn)" in bento


def test_wizard_demo_album_cta() -> None:
    html = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-wizard-demo-album"' in html
    assert "试用《斯里兰卡见闻录》" in html
    assert "上传小文件夹（建议 ≤200MB）" in html
    assert "小文件夹试用" not in html
    wiz = (STUDIO / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    assert "startDemoAlbumImport" in wiz
    assert "useDemoAlbum: true" in wiz
    assert "ftue_demo_album_click" in wiz
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "resolveDemoAlbumExists" in run
    assert "打开示例" in run
    assert "再做一遍" in run
    assert "ftue_demo_album_success" in run


def test_capability_card_ftue_copy() -> None:
    cap = (STUDIO / "js" / "capability-card.js").read_text(encoding="utf-8")
    assert "照片留在本机，也能做成可发的游记" in cap
    assert "开始制作我的游记" in cap
    assert "开始导入" not in cap
    # 书架已有作品时不挡主 CTA
    assert "tripsTotal" in cap
