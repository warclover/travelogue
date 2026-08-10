"""Unit tests · title_art placement_score (PRD §6.2 · D-CAL-13)."""

from __future__ import annotations

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.placement import (
    best_placement,
    focal_conflict,
    score_candidate,
)
from travelogue.cover_engine.title_art.whitelist import FALLBACK_PRESETS, placement_preset

pytestmark = pytest.mark.unit


def test_score_candidate_flat_region_scores_high_openness() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None
    cand = score_candidate(img, preset)
    assert cand.score > 0.8
    assert any("veil-footer" in line for line in cand.explain)


def test_score_candidate_no_faces_notes_skip_in_explain() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None
    cand = score_candidate(img, preset, faces=[])
    assert any("跳过" in line for line in cand.explain)


def test_score_candidate_face_overlap_lowers_score() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None
    baseline = score_candidate(img, preset, faces=[])
    box = (
        int(preset.rect["x"] * 1000),
        int(preset.rect["y"] * 1000),
        int(preset.rect["w"] * 1000),
        int(preset.rect["h"] * 1000),
    )
    overlapping_face = box  # 完全重叠人脸框
    penalized = score_candidate(img, preset, faces=[overlapping_face])
    assert penalized.score < baseline.score


def test_best_placement_picks_highest_scoring_preset() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None
    result = best_placement(img, [preset])
    assert result is not None
    assert result.box[2] > 0 and result.box[3] > 0


def test_best_placement_empty_presets_returns_none() -> None:
    img = Image.new("RGB", (100, 100), (0, 0, 0))
    assert best_placement(img, []) is None


def test_focal_conflict_true_when_trusted_focal_inside_rect() -> None:
    # D-CAL-20 优先顺位④/OQ-CAL-08：veil-footer 实际用的贴纸框（雾带上方）。
    rect = {"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22}
    asset = {"focalPoint": {"x": 0.5, "y": 0.25}}
    assert focal_conflict(asset, rect) is True


def test_focal_conflict_false_when_focal_outside_rect() -> None:
    rect = {"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22}
    asset = {"focalPoint": {"x": 0.5, "y": 0.8}}
    assert focal_conflict(asset, rect) is False


def test_focal_conflict_false_when_focal_untrusted() -> None:
    # 没有真实人脸信号、又恰好等于默认兜底值（0.5, 0.45）→ focal_is_trusted
    # 判定为不可信，不应误报冲突（跟 mark_title_safe 同一套判定口径）。
    rect = {"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22}
    asset = {"focalPoint": {"x": 0.5, "y": 0.45}}
    assert focal_conflict(asset, rect) is False


def test_focal_conflict_false_when_no_focal_point_at_all() -> None:
    rect = {"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22}
    assert focal_conflict({}, rect) is False


def test_score_candidate_paper_bg_skips_photo_signals_and_scores_max_openness() -> None:
    # OQ-CAL-09 收尾：folio-overlap 候选压在纸面栏上，图片里那块区域的原始
    # 像素跟实际渲染出来的纸面毫无关系——哪怕原图那块区域全黑（正常路径下
    # openness 会判定成 0），assume_paper_bg 候选也应跳过该信号给满分。
    img = Image.new("RGB", (1000, 1000), (0, 0, 0))
    preset = placement_preset("folio-overlap")
    assert preset is not None
    assert preset.assume_paper_bg is True
    cand = score_candidate(img, preset)
    assert cand.score == pytest.approx(1.0)
    assert any("纸面底色区" in line for line in cand.explain)


def test_best_placement_breaks_tie_by_larger_area() -> None:
    # assume_paper_bg 候选之间打分几乎总打平（openness 恒为满分），若不
    # 额外按面积排序，``max()`` 平分时固定选列表第一个，folio-overlap 的
    # 全高备选在"地点标签不占用"时也永远选不中——加一层面积次序修好这点。
    img = Image.new("RGB", (1000, 1000), (0, 0, 0))
    small = placement_preset("folio-overlap")
    large = FALLBACK_PRESETS["folio-overlap"][0]
    assert small is not None
    assert large.rect["h"] > small.rect["h"]

    result = best_placement(img, [small, large])
    assert result is not None
    assert result.preset is large


def test_best_placement_detect_faces_exception_is_swallowed() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None

    def _boom(_img: Image.Image) -> list[tuple[int, int, int, int]]:
        raise RuntimeError("no detector")

    result = best_placement(img, [preset], detect_faces=_boom)
    assert result is not None
