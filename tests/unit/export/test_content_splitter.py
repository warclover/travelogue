"""Content-aware longshot split tests (Moments content_balanced + photo_led)."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from travelogue.export.content_splitter import (
    BoundaryPoint,
    breakpoints_cut_photo_interiors,
    compute_breakpoints_dp,
    compute_breakpoints_greedy,
    max_feasible_segments,
    photo_led_slice_ranges,
    plan_moments_split,
    slice_canvas_png,
    slice_ranges,
    snap_breakpoints_to_legal,
)


def test_dp_beats_equal_variance_on_clustered_boundaries() -> None:
    height = 9000
    # Dense uniform-ish boundaries so DP for 9 segments is feasible
    tops = list(range(0, height + 1, 100))
    points = [BoundaryPoint(float(y), "photo") for y in tops]
    bp = compute_breakpoints_dp(9, height, points, scale=1)
    assert bp is not None
    assert len(bp) == 10
    assert bp[0] == 0 and bp[-1] == height
    # Segment heights should be relatively balanced vs naive thirds of extremes
    heights = [bp[i + 1] - bp[i] for i in range(len(bp) - 1)]
    assert max(heights) - min(heights) < height // 3


def test_greedy_respects_weights() -> None:
    height = 3000
    pts = [
        BoundaryPoint(500, "card"),
        BoundaryPoint(1000, "cover"),
        BoundaryPoint(1010, "photo"),
        BoundaryPoint(2000, "photo"),
    ]
    bp = compute_breakpoints_greedy(3, height, pts, scale=1)
    assert bp[0] == 0 and bp[-1] == height
    assert 1000 in bp  # cover preferred near ideal


def test_greedy_no_geometric_never_invents_y() -> None:
    height = 3000
    pts = [BoundaryPoint(500, "photo"), BoundaryPoint(2500, "photo")]
    bp = compute_breakpoints_greedy(
        9, height, pts, scale=1, allow_geometric=False
    )
    legal = {0, 500, 2500, 3000}
    assert set(bp).issubset(legal)
    assert len(bp) < 10  # fewer than requested 9 segments


def test_snap_and_no_mid_photo() -> None:
    cells = [(100, 400), (500, 900), (1000, 1400)]
    bad = breakpoints_cut_photo_interiors([0, 250, 700, 1500], cells)
    assert 250 in bad
    snapped = snap_breakpoints_to_legal([0, 250, 700, 1500], [100, 400, 500, 900, 1000, 1400], 1500)
    assert breakpoints_cut_photo_interiors(snapped, cells) == []


def test_plan_moments_large_trip_targets_9() -> None:
    """content_balanced: enough boundaries → 9 contiguous segments, no mid-cell cuts."""
    from travelogue.export.platform_profiles import clear_platform_profiles_cache

    clear_platform_profiles_cache()
    height_css = 4000.0
    cells = [(i * 200.0, i * 200.0 + 180.0) for i in range(20)]
    tops = [float(t) for t, _ in cells]
    points = [BoundaryPoint(y, "photo") for y in tops]
    plan = plan_moments_split(
        scroll_height_css=height_css,
        boundaries_css=points,
        scale=2,
        photo_count=20,
        photo_cells=cells,
    )
    assert plan.page_count == 9
    assert plan.method in ("dp", "greedy")
    assert len(plan.breakpoints) == 10
    ranges = slice_ranges(plan.breakpoints)
    assert len(ranges) == 9
    cell_canvas = [
        (int(round(t * 2)), int(round(b * 2))) for t, b in cells
    ]
    assert breakpoints_cut_photo_interiors(plan.breakpoints, cell_canvas) == []
    # Contiguous cover of full canvas
    assert plan.breakpoints[0] == 0
    assert plan.breakpoints[-1] == int(round(height_css * 2))


def test_plan_moments_small_trip_allows_fewer_than_9() -> None:
    """content_balanced: 8 photos → up to feasible pages (not forced photo_led 8)."""
    from travelogue.export.platform_profiles import clear_platform_profiles_cache

    clear_platform_profiles_cache()
    cells = [(i * 300.0, i * 300.0 + 250.0) for i in range(8)]
    points = [BoundaryPoint(float(t), "photo") for t, _ in cells]
    plan = plan_moments_split(
        scroll_height_css=2400,
        boundaries_css=points,
        scale=1,
        photo_count=8,
        photo_cells=cells,
    )
    assert 1 <= plan.page_count <= 9
    assert plan.method in ("dp", "greedy")
    assert plan.breakpoints[0] == 0 and plan.breakpoints[-1] == 2400


def test_plan_moments_tiny_trip_allows_single() -> None:
    """content_balanced: few photos → may be 1–N pages (allow single)."""
    from travelogue.export.platform_profiles import clear_platform_profiles_cache

    clear_platform_profiles_cache()
    cells = [(0.0, 400.0), (450.0, 800.0)]
    points = [BoundaryPoint(0.0, "photo"), BoundaryPoint(450.0, "photo")]
    plan = plan_moments_split(
        scroll_height_css=800,
        boundaries_css=points,
        scale=1,
        photo_count=2,
        photo_cells=cells,
    )
    assert 1 <= plan.page_count <= 9
    assert "内容较少" in plan.user_hint or "连读" in plan.user_hint or "单张" in plan.user_hint


def test_plan_moments_photo_led_still_works_when_forced() -> None:
    """Explicit photo_led keeps discrete cell crops."""
    from travelogue.export.platform_profiles import clear_platform_profiles_cache

    clear_platform_profiles_cache()
    cells = [(i * 200.0, i * 200.0 + 180.0) for i in range(12)]
    plan = plan_moments_split(
        scroll_height_css=2400,
        boundaries_css=[],
        scale=1,
        photo_count=12,
        photo_cells=cells,
        segment="photo_led",
    )
    assert plan.method == "photo_led"
    assert plan.page_count == 9
    assert len(photo_led_slice_ranges(plan.breakpoints)) == 9


def test_resolve_moments_page_count_rules() -> None:
    from travelogue.export.platform_profiles import (
        PlatformProfile,
        clear_platform_profiles_cache,
        resolve_moments_page_count,
    )

    clear_platform_profiles_cache()
    # Default profile is content_balanced
    n, hint = resolve_moments_page_count(photo_count=80, max_feasible_segments=12)
    assert n == 9
    assert "连读" in hint or "01→09" in hint

    n2, hint2 = resolve_moments_page_count(photo_count=8, max_feasible_segments=5)
    assert n2 == 5
    assert "内容较少" in hint2 or "连读" in hint2

    n3, hint3 = resolve_moments_page_count(photo_count=3, max_feasible_segments=2)
    assert n3 == 2
    assert "单张" in hint3 or "内容较少" in hint3 or "微信群" in hint3

    photo_led = PlatformProfile(
        id="wechat_moments",
        label="朋友圈",
        segment="photo_led",
        capture="full_once",
        allow_p1=False,
        target_pages=9,
        min_pages=1,
        max_pages=9,
        tiny_photo_max=5,
    )
    n4, hint4 = resolve_moments_page_count(
        photo_count=20, max_feasible_segments=20, profile=photo_led
    )
    assert n4 == 9
    assert "完整" in hint4 or "选取" in hint4


def test_select_photo_led_indices_keeps_ends() -> None:
    from travelogue.export.content_splitter import select_photo_led_indices

    idx = select_photo_led_indices(20, 9)
    assert len(idx) == 9
    assert idx[0] == 0 and idx[-1] == 19
    assert idx == sorted(idx)


def test_clamp_breakpoints_scales_to_actual_height() -> None:
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
