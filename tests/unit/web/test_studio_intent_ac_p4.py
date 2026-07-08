"""Phase 4 automated acceptance helpers (AC-P4-02 · AC-P4-05)."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import get_config
from travelogue.curation.photo_cull import _build_user_line
from travelogue.media.user_tier import resolve_dual_folders


def test_ac_p4_02_cull_user_line_mentions_featured_count() -> None:
    """Success overlay second line includes featured retention copy."""
    line = _build_user_line({"layoutEligibleCount": 10, "featuredCount": 2})
    assert "精选 2 张" in line
    assert "经挑选 10 张" in line


def test_ac_p4_02_cull_user_line_without_featured_omits_clause() -> None:
    line = _build_user_line({"layoutEligibleCount": 8, "featuredCount": 0})
    assert line == "经挑选 8 张进入排版"
    assert "精选" not in line


def test_ac_p4_05_dual_folder_resolver_detects_featured_material(tmp_path: Path) -> None:
    """Appendix A layout: 精选 + 素材 folders resolve for tier ingest."""
    root = tmp_path / "album"
    root.mkdir()
    (root / "精选").mkdir()
    (root / "素材上传").mkdir()
    (root / "精选" / "a.jpg").write_bytes(b"x")
    (root / "素材上传" / "b.jpg").write_bytes(b"y")
    feat, mat, mode = resolve_dual_folders(root, get_config().ingest)
    assert feat is not None and feat.name == "精选"
    assert mat is not None and mat.name == "素材上传"
    assert mode == "auto"
