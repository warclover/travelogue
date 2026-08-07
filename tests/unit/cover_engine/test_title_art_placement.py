"""Unit tests · title_art placement_score (PRD §6.2 · D-CAL-13)."""

from __future__ import annotations

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.placement import best_placement, score_candidate
from travelogue.cover_engine.title_art.whitelist import placement_preset

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


def test_best_placement_detect_faces_exception_is_swallowed() -> None:
    img = Image.new("RGB", (1000, 1000), (200, 200, 200))
    preset = placement_preset("veil-footer")
    assert preset is not None

    def _boom(_img: Image.Image) -> list[tuple[int, int, int, int]]:
        raise RuntimeError("no detector")

    result = best_placement(img, [preset], detect_faces=_boom)
    assert result is not None
