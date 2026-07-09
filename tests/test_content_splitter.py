"""Unit tests for Longshot 2.0 content_splitter (AC-LNG2-02*)."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from travelogue.export.content_splitter import (
    BoundaryPoint,
    boundary_cost,
    canvas_height,
    compute_breakpoints_dp,
    compute_breakpoints_greedy,
    css_to_canvas,
    max_feasible_segments,
    nearest_boundary,
    plan_moments_split,
    segment_height_variance,
    slice_canvas_png,
    slice_ranges,
)
from travelogue.export.platform_profiles import resolve_moments_page_count

pytestmark = pytest.mark.unit


def test_css_to_canvas_scale_2_and_3() -> None:
    assert css_to_canvas(100, 2) == 200
    assert css_to_canvas(100.4, 2) == 201
    assert css_to_canvas(50, 3) == 150
    assert canvas_height(844, 2) == 1688


def test_boundary_cost_prefers_higher_weight() -> None:
    # Same distance: cover cheaper than photo
    assert boundary_cost(10, "cover") < boundary_cost(10, "photo")
    assert boundary_cost(10, "chapter_separator") < boundary_cost(10, "card")


def test_nearest_boundary_weight_prefers_cover() -> None:
    candidates = [
        (90, "photo"),
        (110, "cover"),
        (200, "card"),
    ]
    pick = nearest_boundary(100, candidates)
    assert pick is not None
    assert pick[1] == "cover"


def test_dp_does_not_cut_inside_photo_cells() -> None:
    """AC-LNG2-02: breakpoints only on legal boundaries (photo tops)."""
    # Photo cells occupy [100,200), [200,300), ... — cuts only at tops
    height = 1000
    photo_tops = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    bp = compute_breakpoints_dp(5, height, photo_tops)
    assert bp is not None
    assert bp[0] == 0 and bp[-1] == height
    for y in bp:
        assert y in photo_tops
    # No cut strictly inside a cell (between tops)
    for y0, y1 in slice_ranges(bp):
        assert y1 - y0 >= height // (5 * 2)


def test_dp_variance_better_than_naive_equal_when_skewed() -> None:
    """AC-LNG2-02c: DP should beat naive equal-spacing snapped poorly."""
    height = 900
    # Dense early, sparse late
    boundaries = [0, 50, 100, 150, 200, 250, 300, 600, 900]
    dp = compute_breakpoints_dp(3, height, boundaries)
    assert dp is not None
    # Greedy equal ideals at 300, 600
    greedy = compute_breakpoints_greedy(3, height, boundaries)
    assert segment_height_variance(dp) <= segment_height_variance(greedy) + 1e-6


def test_greedy_fallback_when_dp_infeasible() -> None:
    height = 500
    # Only one interior point — cannot DP into 5 segments
    boundaries = [0, 250, 500]
    assert compute_breakpoints_dp(5, height, boundaries) is None
    greedy = compute_breakpoints_greedy(3, height, boundaries)
    assert greedy[0] == 0 and greedy[-1] == 500
    assert len(greedy) >= 2


def test_plan_moments_large_trip_targets_9() -> None:
    """AC-LNG2-01 style: enough boundaries → 9 pages."""
    height_css = 9000
    # 40 photo tops evenly
    tops = [i * (height_css / 40) for i in range(41)]
    points = [BoundaryPoint(y, "photo") for y in tops]
    plan = plan_moments_split(
        scroll_height_css=height_css,
        boundaries_css=points,
        scale=2,
        photo_count=80,
    )
    assert plan.page_count == 9
    assert len(plan.breakpoints) == 10
    assert plan.breakpoints[0] == 0
    assert plan.breakpoints[-1] == canvas_height(height_css, 2)


def test_plan_moments_small_trip_6_to_9() -> None:
    """AC-LNG2-01b / D-LNG2-21: 8–12 photos → 6–9 pages."""
    height_css = 2400
    # Sparse legal cuts → feasible ≈6–7 segments (not full 9)
    tops = [0, 400, 800, 1200, 1600, 2000, 2400]
    points = [BoundaryPoint(float(y), "photo") for y in tops]
    plan = plan_moments_split(
        scroll_height_css=height_css,
        boundaries_css=points,
        scale=1,
        photo_count=10,
    )
    assert 6 <= plan.page_count <= 9
    if plan.page_count < 9:
        assert "内容较少" in plan.user_hint


def test_plan_moments_tiny_trip_no_pad_to_6() -> None:
    """AC-LNG2-01t / D-LNG2-22: 1–5 photos → 1–5 pages."""
    height_css = 800
    tops = [0, 200, 400, 600, 800]
    points = [BoundaryPoint(float(y), "photo") for y in tops]
    plan = plan_moments_split(
        scroll_height_css=height_css,
        boundaries_css=points,
        scale=1,
        photo_count=3,
    )
    assert 1 <= plan.page_count <= 5
    assert "微信群" in plan.user_hint


def test_resolve_moments_page_count_rules() -> None:
    n, hint = resolve_moments_page_count(photo_count=80, max_feasible_segments=12)
    assert n == 9
    n2, hint2 = resolve_moments_page_count(photo_count=10, max_feasible_segments=7)
    assert 6 <= n2 <= 9
    assert "内容较少" in hint2
    n3, hint3 = resolve_moments_page_count(photo_count=3, max_feasible_segments=4)
    assert 1 <= n3 <= 5
    assert "微信群" in hint3


def test_clamp_breakpoints_scales_to_actual_height() -> None:
    """Capture taller/shorter than CSS plan must keep page count, not append a tail page."""
    from travelogue.export.content_splitter import clamp_breakpoints_to_height

    planned = [0, 450, 900, 1350, 1800, 2400, 3000]
    tall = clamp_breakpoints_to_height(planned, 6000)
    assert len(tall) == 7
    assert tall[0] == 0 and tall[-1] == 6000
    short = clamp_breakpoints_to_height(planned, 2800)
    assert len(short) == 7
    assert short[0] == 0 and short[-1] == 2800


def test_slice_canvas_png_vertical_crop() -> None:
    img = Image.new("RGB", (428, 900), (10, 20, 30))
    # paint a red band at y=300..400
    for y in range(300, 400):
        for x in range(428):
            img.putpixel((x, y), (255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    sliced = slice_canvas_png(raw, 300, 400)
    out = Image.open(BytesIO(sliced))
    assert out.size == (428, 100)
    assert out.getpixel((0, 0)) == (255, 0, 0)


def test_max_feasible_segments_respects_min_height() -> None:
    height = 900
    boundaries = list(range(0, 901, 50))
    n = max_feasible_segments(height, boundaries, n_target=9)
    assert n >= 6
