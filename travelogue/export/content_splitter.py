"""Content-aware longshot split: DP + greedy fallback (Longshot 2.0 Phase A)."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Sequence

BOUNDARY_WEIGHT: dict[str, float] = {
    "cover": 1.5,
    "chapter_separator": 1.4,
    "chapter_start": 1.2,
    "photo": 1.0,
    "card": 0.9,
}


@dataclass(frozen=True)
class BoundaryPoint:
    y_css: float
    kind: str = "photo"

    def y_canvas(self, scale: int | float) -> int:
        return css_to_canvas(self.y_css, scale)


@dataclass(frozen=True)
class SplitPlan:
    breakpoints: list[int]  # canvas px, includes 0 and H
    page_count: int
    user_hint: str = ""
    method: str = "dp"  # dp | greedy


def css_to_canvas(y_css: float, scale: int | float) -> int:
    return int(round(float(y_css) * float(scale)))


def canvas_height(scroll_height_css: float, scale: int | float) -> int:
    return max(1, css_to_canvas(scroll_height_css, scale))


def boundary_cost(distance: float, kind: str) -> float:
    weight = BOUNDARY_WEIGHT.get(kind, 1.0)
    if weight <= 0:
        weight = 1.0
    return abs(float(distance)) / weight


def _normalize_boundaries(
    height: int,
    boundaries: Sequence[int] | Sequence[BoundaryPoint],
    *,
    scale: int | float = 1,
) -> list[tuple[int, str]]:
    """Return sorted unique (y_canvas, kind) including 0 and height."""
    points: list[tuple[int, str]] = [(0, "start"), (int(height), "end")]
    for item in boundaries:
        if isinstance(item, BoundaryPoint):
            y = item.y_canvas(scale)
            kind = item.kind
        elif isinstance(item, tuple) and len(item) >= 2:
            y, kind = int(item[0]), str(item[1])
        else:
            y, kind = int(item), "photo"  # type: ignore[arg-type]
        if 0 < y < height:
            points.append((y, kind))
    # Keep highest-weight kind on duplicate y
    by_y: dict[int, str] = {}
    for y, kind in points:
        prev = by_y.get(y)
        if prev is None or BOUNDARY_WEIGHT.get(kind, 1.0) > BOUNDARY_WEIGHT.get(prev, 1.0):
            by_y[y] = kind
    return sorted((y, by_y[y]) for y in by_y)


def nearest_boundary(
    ideal_y: float,
    candidates: Sequence[tuple[int, str]],
    *,
    exclude: set[int] | None = None,
) -> tuple[int, str] | None:
    """Pick candidate minimizing distance/weight (D-LNG2-29)."""
    exclude = exclude or set()
    best: tuple[int, str] | None = None
    best_cost = float("inf")
    for y, kind in candidates:
        if y in exclude or y <= 0:
            continue
        cost = boundary_cost(float(y) - float(ideal_y), kind)
        if cost < best_cost:
            best_cost = cost
            best = (y, kind)
    return best


def max_feasible_segments(
    height: int,
    boundaries: Sequence[int] | Sequence[BoundaryPoint],
    *,
    scale: int | float = 1,
    n_target: int = 9,
) -> int:
    """How many segments can be formed under min-height constraint."""
    pts = _normalize_boundaries(height, boundaries, scale=scale)
    ys = [y for y, _ in pts]
    if height <= 0 or len(ys) < 2:
        return 1
    min_seg = max(1, height // max(n_target * 2, 1))
    # Greedy pack: walk forward taking next boundary at least min_seg ahead
    count = 0
    cursor = 0
    i = 0
    while cursor < height:
        target = cursor + min_seg
        # find smallest y >= target, else height
        while i < len(ys) and ys[i] < target:
            i += 1
        if i >= len(ys):
            if cursor < height:
                count += 1
            break
        nxt = ys[i]
        if nxt <= cursor:
            i += 1
            continue
        count += 1
        cursor = nxt
        if cursor >= height:
            break
    return max(1, count)


def compute_breakpoints_dp(
    n: int,
    height: int,
    boundaries: Sequence[int] | Sequence[BoundaryPoint],
    *,
    scale: int | float = 1,
) -> list[int] | None:
    """DP: choose n-1 interior cuts minimizing segment-height variance.

    Returns full breakpoint list ``[0, ..., height]`` or None if infeasible.
    """
    n = int(n)
    height = int(height)
    if n <= 1:
        return [0, height]
    pts = _normalize_boundaries(height, boundaries, scale=scale)
    ys = [y for y, _ in pts]
    if len(ys) < n + 1:
        # Need at least n+1 points (0 + n-1 cuts + H). Cuts must be interior.
        interior = [y for y in ys if 0 < y < height]
        if len(interior) < n - 1:
            return None

    min_seg = max(1, height // max(n * 2, 1))
    # Index into ys
    m = len(ys)
    # dp[k][j] = min variance*const for k segments ending at ys[j]
    # Store sum of squared lengths; variance = sum_sq/n - mean^2, mean fixed = H/n
    # Minimizing sum of squared segment lengths is equivalent.
    INF = float("inf")
    dp: list[list[float]] = [[INF] * m for _ in range(n + 1)]
    prev: list[list[int | None]] = [[None] * m for _ in range(n + 1)]
    dp[0][0] = 0.0

    for k in range(1, n + 1):
        for j in range(1, m):
            yj = ys[j]
            for i in range(j):
                yi = ys[i]
                seg = yj - yi
                if seg < min_seg and j != m - 1:
                    continue
                if seg <= 0:
                    continue
                if dp[k - 1][i] >= INF:
                    continue
                cost = dp[k - 1][i] + float(seg) * float(seg)
                if cost < dp[k][j]:
                    dp[k][j] = cost
                    prev[k][j] = i

    # Prefer ending exactly at height (last index)
    end_j = m - 1
    if dp[n][end_j] >= INF:
        return None

    # Reconstruct
    cuts: list[int] = []
    k, j = n, end_j
    while k > 0:
        cuts.append(ys[j])
        i = prev[k][j]
        if i is None:
            return None
        j = i
        k -= 1
    cuts.append(ys[0])
    cuts.reverse()
    # Ensure unique monotonic
    out: list[int] = []
    for y in cuts:
        if not out or y > out[-1]:
            out.append(y)
    if out[0] != 0:
        out.insert(0, 0)
    if out[-1] != height:
        out.append(height)
    if len(out) != n + 1:
        return None
    return out


def compute_breakpoints_greedy(
    n: int,
    height: int,
    boundaries: Sequence[int] | Sequence[BoundaryPoint],
    *,
    scale: int | float = 1,
) -> list[int]:
    """Greedy: place cuts near ideal equal spacing using weighted nearest."""
    n = max(1, int(n))
    height = int(height)
    pts = _normalize_boundaries(height, boundaries, scale=scale)
    if n <= 1:
        return [0, height]

    ideal_step = height / n
    chosen: list[int] = [0]
    used: set[int] = {0, height}
    for i in range(1, n):
        ideal = ideal_step * i
        # Prefer candidates after previous cut + min_seg
        min_seg = max(1, height // max(n * 2, 1))
        prev = chosen[-1]
        candidates = [(y, k) for y, k in pts if y >= prev + min_seg and y < height]
        if not candidates:
            candidates = [(y, k) for y, k in pts if prev < y < height]
        pick = nearest_boundary(ideal, candidates, exclude=used)
        if pick is None:
            # Force geometric cut clamped to remaining interior
            y = int(round(ideal))
            y = max(prev + 1, min(height - (n - i), y))
            if y in used or y <= prev or y >= height:
                continue
            chosen.append(y)
            used.add(y)
        else:
            chosen.append(pick[0])
            used.add(pick[0])
    chosen.append(height)
    # Deduplicate / sort
    out = sorted(set(chosen))
    if out[0] != 0:
        out.insert(0, 0)
    if out[-1] != height:
        out.append(height)
    return out


def plan_moments_split(
    *,
    scroll_height_css: float,
    boundaries_css: Sequence[float] | Sequence[BoundaryPoint],
    scale: int,
    photo_count: int,
    target_pages: int = 9,
    min_pages: int = 6,
    max_pages: int = 9,
    tiny_photo_max: int = 5,
) -> SplitPlan:
    """Full moments split plan: resolve N then DP (greedy fallback)."""
    from travelogue.export.platform_profiles import get_profile, resolve_moments_page_count

    scale = max(1, int(scale))
    h = canvas_height(scroll_height_css, scale)
    pts: list[BoundaryPoint]
    if boundaries_css and isinstance(boundaries_css[0], BoundaryPoint):
        pts = list(boundaries_css)  # type: ignore[arg-type]
    else:
        pts = [BoundaryPoint(float(y), "photo") for y in boundaries_css]  # type: ignore[arg-type]

    canvas_pts = [(p.y_canvas(scale), p.kind) for p in pts]
    feasible = max_feasible_segments(h, canvas_pts, scale=1, n_target=target_pages)

    profile = get_profile("wechat_moments")
    n, hint = resolve_moments_page_count(
        photo_count=photo_count,
        max_feasible_segments=feasible,
        profile=profile,
    )
    n = max(1, min(int(n), max_pages, feasible))

    bp = compute_breakpoints_dp(n, h, canvas_pts, scale=1)
    method = "dp"
    if bp is None:
        bp = compute_breakpoints_greedy(n, h, canvas_pts, scale=1)
        method = "greedy"
        n = max(1, len(bp) - 1)
        if photo_count <= tiny_photo_max:
            hint = (
                f"内容较少，已生成 {n} 张朋友圈配图。"
                "建议改用微信群长图以获得更完整阅读体验。"
            )
        elif n < target_pages:
            hint = f"内容较少，已生成 {n} 张朋友圈配图（目标 {target_pages} 张）。"

    return SplitPlan(breakpoints=bp, page_count=n, user_hint=hint, method=method)


def plan_xhs_split(
    *,
    scroll_height_css: float,
    boundaries_css: Sequence[float] | Sequence[BoundaryPoint],
    scale: int,
    photo_count: int,
    slide_count: int | None = None,
) -> SplitPlan:
    """Xiaohongshu split plan: auto/user N then DP (greedy fallback)."""
    from travelogue.export.platform_profiles import get_profile, resolve_xhs_slide_count

    scale = max(1, int(scale))
    h = canvas_height(scroll_height_css, scale)
    if boundaries_css and isinstance(boundaries_css[0], BoundaryPoint):
        pts = list(boundaries_css)  # type: ignore[arg-type]
    else:
        pts = [BoundaryPoint(float(y), "photo") for y in boundaries_css]  # type: ignore[arg-type]

    canvas_pts = [(p.y_canvas(scale), p.kind) for p in pts]
    profile = get_profile("xiaohongshu")
    # Use a generous n_target for feasibility packing
    feasible = max_feasible_segments(h, canvas_pts, scale=1, n_target=9)
    n, hint = resolve_xhs_slide_count(
        photo_count=photo_count,
        slide_count=slide_count,
        max_feasible_segments=feasible,
        profile=profile,
    )
    n = max(1, min(int(n), int(profile.max_pages or 18), feasible))

    bp = compute_breakpoints_dp(n, h, canvas_pts, scale=1)
    method = "dp"
    if bp is None:
        bp = compute_breakpoints_greedy(n, h, canvas_pts, scale=1)
        method = "greedy"
        n = max(1, len(bp) - 1)
        hint = f"已生成 {n} 张 3:4 配图 · 更多细节可写在笔记正文"

    return SplitPlan(breakpoints=bp, page_count=n, user_hint=hint, method=method)


def slice_ranges(breakpoints: Sequence[int]) -> list[tuple[int, int]]:
    bps = list(breakpoints)
    return [(bps[i], bps[i + 1]) for i in range(len(bps) - 1) if bps[i + 1] > bps[i]]


def clamp_breakpoints_to_height(breakpoints: Sequence[int], height: int) -> list[int]:
    """Map planned breakpoints onto actual capture height (CSS×scale vs PNG drift).

    Scales by ``height / planned_end`` so page count stays stable when the PNG is
    shorter or taller than the CSS-derived plan; then enforces monotonic ``[0, height]``.
    """
    height = max(1, int(height))
    raw = [int(y) for y in breakpoints]
    if not raw:
        return [0, height]
    planned_end = max(raw[-1], 1)
    out: list[int] = [0]
    for y in raw:
        yy = int(round(y * height / planned_end))
        yy = max(0, min(yy, height))
        if yy > out[-1]:
            out.append(yy)
    if out[-1] != height:
        out.append(height)
    dedup: list[int] = []
    for y in out:
        if not dedup or y > dedup[-1]:
            dedup.append(y)
    if len(dedup) < 2:
        return [0, height]
    return dedup


def slice_canvas_png(data: bytes, y0: int, y1: int) -> bytes:
    """Crop PNG/JPEG bytes to vertical range [y0, y1) in canvas pixels."""
    from PIL import Image

    img = Image.open(BytesIO(data))
    y0 = max(0, min(int(y0), img.height))
    y1 = max(0, min(int(y1), img.height))
    if y1 <= y0:
        # Degenerate: emit 1px strip from bottom of valid region
        y0 = max(0, min(y0, img.height - 1))
        y1 = min(img.height, y0 + 1)
    cropped = img.crop((0, y0, img.width, y1))
    buf = BytesIO()
    fmt = "JPEG" if (img.format or "").upper() in ("JPEG", "JPG") else "PNG"
    if fmt == "JPEG":
        cropped.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        cropped.save(buf, format="PNG")
    return buf.getvalue()


def segment_height_variance(breakpoints: Sequence[int]) -> float:
    ranges = slice_ranges(breakpoints)
    if not ranges:
        return 0.0
    heights = [y1 - y0 for y0, y1 in ranges]
    mean = sum(heights) / len(heights)
    return sum((h - mean) ** 2 for h in heights) / len(heights)
