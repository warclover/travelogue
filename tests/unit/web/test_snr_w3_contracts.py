"""Share Narrative Readiness · W3 喜欢项零回退契约（AC-SNR-12）。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_snr_w3_six_platforms_still_present() -> None:
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    for pid in (
        "wechat_chat",
        "wechat_moments",
        "xiaohongshu",
        "wechat_official",
        "poster_bric",
        "album_spread",
    ):
        assert f"{pid}:" in panel or f'"{pid}"' in panel, pid


def test_snr_w3_narrow_gate_copy_present() -> None:
    gate = (STUDIO / "preview-toolbar" / "narrow-gate.js").read_text(encoding="utf-8")
    assert "preview-narrow-gate" in gate
    assert "返回首页制作" in gate
    assert "复制电脑打开地址" in gate


def test_snr_w3_ai_no_auto_consume_copy() -> None:
    ai = (STUDIO / "preview-toolbar" / "ai-sheet.js").read_text(encoding="utf-8")
    # SAS 信任句：不自动消耗额度（喜欢项零回退）
    assert "不自动消耗" in ai or "不自动" in ai


def test_snr_w3_scan_script_exists() -> None:
    script = ROOT / "scripts" / "snr_narrative_readiness_scan.py"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "旅行照片" in text
    assert "bare_date" in text or "bareDate" in text
