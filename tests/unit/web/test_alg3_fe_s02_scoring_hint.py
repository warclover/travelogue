"""ALG-V3 FE-ALG3-S02 · scoring hint mentions early search stop."""

from __future__ import annotations

from tests._repo_root import repo_root

_HINT_ID = 'id="studio-cfg-layout-scoring-hint"'
_REQUIRED = "搜索可能按时长提前结束"


def test_fe_s02_layout_scoring_hint_mentions_early_stop() -> None:
    html = (
        repo_root(__file__) / "templates" / "studio" / "studio-home-v2.html"
    ).read_text(encoding="utf-8")
    assert _HINT_ID in html
    idx = html.index(_HINT_ID)
    window = html[idx : idx + 280]
    assert _REQUIRED in window, window
    # Neutral copy (FE-ALG3-X01 / VC-05): no upgrade / AI-stronger marketing in the hint.
    assert "升级" not in window
    assert "AI更强" not in window
    assert "AI 更强" not in window
