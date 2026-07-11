"""Longshot 2.0 branch B · platform segment export (ADR-016).

Single P0 full capture → boundary → DP split → postprocess → atomic write.
P1 fallback is forbidden (D-LNG2-10).

Phase A: wechat_moments (crop + footer).
Phase B/C: aspect-fit platforms (fit_aspect WxH + footer; douyin single-file).
Phase C: instagram / weibo / douyin_cover / custom (CLI · aspect-fit).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.export.boundary_metrics import (
    BoundaryMetrics,
    count_photos_heuristic,
    parse_boundary_payload,
)
from travelogue.export.content_splitter import (
    clamp_breakpoints_to_height,
    photo_led_slice_ranges,
    plan_aspect_split,
    plan_moments_split,
    slice_canvas_png,
    slice_ranges,
)
from travelogue.export.longshot import (
    _BROWSER_POOL,
    CAPTURE_WIDTH,
    DEFAULT_EXPORT_SCALE,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _apply_copy_display,
    _capture_p0_with_metrics,
    _page_metrics,
    _resolve_longshot_url,
    _slug_title,
    _trip_title,
)
from travelogue.export.platform_profiles import (
    ASPECT_FIT_PLATFORM_IDS,
    DEFAULT_PLATFORM,
    PLATFORM_SEGMENT_IDS,
    PlatformProfile,
    file_prefix_for_platform,
    get_profile,
    is_single_file_output,
    output_canvas_size,
)
from travelogue.export.slide_postprocess import draw_page_footer, fit_aspect
from travelogue.render.engine import LONGSHOT_INDEX_NAME

_log = logging.getLogger(__name__)

MEMORY_BUDGET_BYTES = 400 * 1024 * 1024
MAX_WECHAT_SLICE_BYTES = 20 * 1024 * 1024
MAX_SCALE_DOWN_ATTEMPTS = 2


class PlatformExportWriter:
    """Atomic ``.part`` → rename writer (D-LNG2-14).

    Multi-page: ``{prefix}-{nn:02d}.{ext}``.
    Single-file (douyin_cover): ``{prefix}.{ext}`` when ``single_file=True``.
    """

    def __init__(
        self,
        directory: Path,
        prefix: str,
        *,
        ext: str = "png",
        single_file: bool = False,
    ) -> None:
        self.directory = Path(directory)
        self.prefix = prefix
        self.ext = ext.lstrip(".")
        self.single_file = bool(single_file)
        self._parts: list[Path] = []
        self._finals: list[Path] = []
        self._committed = False

    def part_path(self, nn: int) -> Path:
        if self.single_file:
            return self.directory / f"{self.prefix}.{self.ext}.part"
        return self.directory / f"{self.prefix}-{nn:02d}.{self.ext}.part"

    def final_path(self, nn: int) -> Path:
        if self.single_file:
            return self.directory / f"{self.prefix}.{self.ext}"
        return self.directory / f"{self.prefix}-{nn:02d}.{self.ext}"

    def write(self, nn: int, data: bytes) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        part = self.part_path(nn)
        part.write_bytes(data)
        if not part.is_file() or part.stat().st_size == 0:
            raise LongshotExportError("E_LNG_CAPTURE_FAILED", f"写入失败: {part}")
        self._parts.append(part)
        self._finals.append(self.final_path(nn))
        return part

    def commit(self) -> list[Path]:
        committed: list[Path] = []
        for part, final in zip(self._parts, self._finals):
            if final.exists():
                final.unlink()
            part.replace(final)
            committed.append(final)
        self._parts.clear()
        self._committed = True
        return committed

    def rollback(self) -> None:
        for part in list(self._parts):
            try:
                if part.exists():
                    part.unlink()
            except OSError:
                _log.debug("rollback unlink part failed: %s", part, exc_info=True)
        for orphan in self.directory.glob(f"{self.prefix}-*.{self.ext}.part"):
            try:
                orphan.unlink()
            except OSError:
                _log.debug("rollback orphan part failed: %s", orphan, exc_info=True)
        if self.single_file:
            orphan_single = self.directory / f"{self.prefix}.{self.ext}.part"
            try:
                if orphan_single.exists():
                    orphan_single.unlink()
            except OSError:
                _log.debug(
                    "rollback single part failed: %s", orphan_single, exc_info=True
                )
        self._parts.clear()
        self._finals.clear()

    def __enter__(self) -> PlatformExportWriter:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None or not self._committed:
            self.rollback()


def estimate_capture_memory_bytes(scroll_height_css: float, *, scale: int) -> int:
    width = CAPTURE_WIDTH * max(1, int(scale))
    height = max(1, int(round(float(scroll_height_css) * scale)))
    bpp = 4
    return int(width * height * bpp)


def auto_downgrade_scale(scroll_height_css: float, scale: int) -> int:
    scale = max(1, min(int(scale), 3))
    while scale > 1 and estimate_capture_memory_bytes(scroll_height_css, scale=scale) > MEMORY_BUDGET_BYTES:
        scale -= 1
    if estimate_capture_memory_bytes(scroll_height_css, scale=scale) > MEMORY_BUDGET_BYTES:
        raise LongshotExportError(
            "E_LNG2_CAPTURE_TOO_LARGE",
            "内容过长，请降低清晰度或改用微信群按章导出",
        )
    return scale


def _capture_full_p0_only(
    page: Any, *, scale: int, fmt: str
) -> tuple[bytes, BoundaryMetrics | None]:
    """Full-page P0 capture; returns bytes + capture-time boundary metrics."""
    try:
        data, method, metrics_payload = _capture_p0_with_metrics(
            page, scale=scale, fmt=fmt
        )
    except LongshotExportError:
        raise
    except Exception as exc:
        raise LongshotExportError(
            "E_LNG2_CAPTURE_P0_FAILED",
            "无法生成平台配图（不支持兼容模式），请改用微信群 · 按章导出",
        ) from exc
    if method != "p0":
        raise LongshotExportError(
            "E_LNG2_CAPTURE_P0_FAILED",
            "无法生成平台配图（不支持兼容模式），请改用微信群 · 按章导出",
        )
    boundaries = parse_boundary_payload(metrics_payload) if metrics_payload else None
    return data, boundaries


def _publish_guide(page_count: int, profile: PlatformProfile) -> str:
    guide = (profile.publish_guide or "").strip()
    if guide:
        return guide.replace("01→N", f"01→{page_count:02d}").replace(
            "01→09", f"01→{page_count:02d}"
        )
    if profile.id == "xiaohongshu":
        return (
            "发布步骤：保存到相册 → 小红书 → 发笔记 → 选图；"
            "详情写在笔记正文，配图是视觉提纲"
        )
    if profile.id in ASPECT_FIT_PLATFORM_IDS:
        return f"已生成 {page_count} 张平台配图，按编号顺序使用"
    return (
        f"发布步骤：1. 在文件夹按 01→{page_count:02d} 全选（图底 i/n 助 orientation）"
        " 2. 朋友圈 → 从相册选择 3. 按顺序发布 · 滑动可连读整卷长图。"
    )


def _resolve_pad_mode(
    pad_mode: str | None,
    profile: PlatformProfile,
    *,
    smart_crop_enabled: bool,
) -> str:
    raw = (pad_mode or profile.default_pad_mode or "letterbox").strip().lower()
    if raw in ("", "auto"):
        raw = profile.default_pad_mode or "letterbox"
    # douyin_cover defaults to smart_crop; allow even when experimental flag off
    if raw == "smart_crop" and not smart_crop_enabled and profile.id != "douyin_cover":
        _log.info("smart_crop requested but flag off; falling back to letterbox")
        return "letterbox"
    if raw not in ("letterbox", "smart_crop"):
        return "letterbox"
    return raw


def _smart_crop_flag_from_config() -> bool:
    try:
        from travelogue.config import get_config

        return bool(get_config().studio.longshot2.smart_crop_enabled)
    except Exception:
        return False


def export_platform_longshot(
    trip_dir: Path,
    *,
    platform: str = "wechat_moments",
    scale: int = DEFAULT_EXPORT_SCALE,
    fmt: str = "png",
    base_url: str | None = None,
    trip_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    timeout_ms: int = 180_000,
    progress: ProgressFn | None = None,
    copy_display: str = "full",
    slide_count: int | None = None,
    pad_mode: str | None = None,
    profile: PlatformProfile | None = None,
    smart_crop_enabled: bool | None = None,
) -> LongshotExportResult:
    """Branch B entry · moments / xhs / Phase C aspect-fit platforms."""
    trip_dir = trip_dir.resolve()
    longshot_html = trip_dir / LONGSHOT_INDEX_NAME
    if not longshot_html.is_file():
        raise LongshotExportError(
            "E_LNG_NO_LONGSHOT",
            "未找到 index-longshot.html，请先完成渲染",
        )

    profile = profile or get_profile(platform)
    if profile.id == DEFAULT_PLATFORM:
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            "wechat_chat 应走分支 A，请使用 export_trip_longshot",
        )
    if profile.id not in PLATFORM_SEGMENT_IDS:
        raise LongshotExportError(
            "E_LNG2_INVALID_PLATFORM",
            f"不支持的平台「{profile.id}」",
        )

    is_aspect = profile.id in ASPECT_FIT_PLATFORM_IDS
    single_file = is_single_file_output(profile)
    canvas_size = output_canvas_size(profile) if is_aspect else None
    if smart_crop_enabled is None:
        smart_crop_enabled = _smart_crop_flag_from_config()
    resolved_pad = _resolve_pad_mode(
        pad_mode, profile, smart_crop_enabled=bool(smart_crop_enabled)
    )

    scale = max(1, min(int(scale), 3))
    # Aspect-fit finals are PNG; capture may still use jpeg under size pressure
    fmt = "jpeg" if str(fmt).lower() == "jpeg" else "png"
    out_fmt = "png" if is_aspect else fmt
    out_ext = "png" if is_aspect else ("jpg" if fmt == "jpeg" else "png")
    title = _slug_title(_trip_title(trip_dir))
    prefix = file_prefix_for_platform(title, profile.id)

    url, server = _resolve_longshot_url(
        trip_dir, base_url=base_url, host=host, port=port, trip_id=trip_id
    )
    browser = _BROWSER_POOL.acquire()

    def _report(cur: int, total: int, hint: str) -> None:
        if progress:
            progress(cur, total, hint)

    W_OPEN, W_CAPTURE, W_SPLIT, W_WRITE = 10, 30, 50, 10
    W_TOTAL = W_OPEN + W_CAPTURE + W_SPLIT + W_WRITE

    page = None
    outputs: list[LongshotOutput] = []
    user_hint = ""
    publish_guide = ""
    page_count = 0
    target_page_count: int | None = (
        None if is_aspect else int(profile.target_pages or 9)
    )
    label_noun = {
        "wechat_moments": "朋友圈配图",
        "xiaohongshu": "小红书配图",
        "instagram": "Instagram 配图",
        "weibo": "微博配图",
        "douyin_cover": "抖音封面",
        "custom": "自定义配图",
    }.get(profile.id, "平台配图")

    try:
        _report(W_OPEN, W_TOTAL, "正在打开页面…")
        page = browser.new_page(viewport={"width": CAPTURE_WIDTH, "height": 844})
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        page.wait_for_function(
            "() => window.TravelogueLongshot && document.documentElement.dataset.longshot === 'on'",
            timeout=30_000,
        )
        # Moments photo_led defaults to pure photos (no narrative cutting through images).
        effective_copy = (
            "photos" if profile.id == "wechat_moments" else copy_display
        )
        _apply_copy_display(page, effective_copy)

        metrics = _page_metrics(page)
        scroll_h = float(metrics.get("scrollHeight") or 0)
        scale = auto_downgrade_scale(scroll_h, scale)

        canvas_bytes: bytes | None = None
        plan = None
        working_fmt = fmt
        scale_attempts = 0
        tried_jpeg = False
        boundaries: BoundaryMetrics | None = None

        while True:
            _report(W_OPEN + 5, W_TOTAL, "正在全页截图并采集切分边界…")
            scale = auto_downgrade_scale(scroll_h, scale)
            _log.info(
                "platform longshot capture estimate_bytes=%s scale=%s platform=%s",
                estimate_capture_memory_bytes(scroll_h, scale=scale),
                scale,
                profile.id,
            )
            canvas_bytes, boundaries = _capture_full_p0_only(
                page, scale=scale, fmt=working_fmt
            )
            if boundaries is None:
                raise LongshotExportError(
                    "E_LNG2_BOUNDARIES_MISSING",
                    "长图脚本过旧，无法在截图布局下采集切分边界。"
                    "请先重新渲染该游记后再导出朋友圈配图。",
                )

            photo_count = count_photos_heuristic(page)
            if boundaries.photo_cells:
                photo_count = max(photo_count, len(boundaries.photo_cells))
            scroll_h = boundaries.scroll_height_css or scroll_h

            _log.info(
                "platform longshot boundaries cells=%s scroll_h=%s method_hint=%s",
                len(boundaries.photo_cells),
                scroll_h,
                profile.segment,
            )

            if is_aspect:
                plan = plan_aspect_split(
                    scroll_height_css=boundaries.scroll_height_css,
                    boundaries_css=boundaries.as_points(),
                    scale=scale,
                    photo_count=photo_count,
                    slide_count=slide_count,
                    profile=profile,
                    hint_kind="xhs" if profile.id == "xiaohongshu" else "aspect",
                )
            else:
                plan = plan_moments_split(
                    scroll_height_css=boundaries.scroll_height_css,
                    boundaries_css=boundaries.as_points(),
                    scale=scale,
                    photo_count=photo_count,
                    photo_cells=boundaries.photo_cells,
                    segment=profile.segment,
                )
            # Align CSS×scale breakpoints to actual captured PNG height
            from io import BytesIO

            from PIL import Image as _PILImage

            actual_h = _PILImage.open(BytesIO(canvas_bytes)).height
            if plan.method == "photo_led":
                clamped = [
                    max(0, min(int(y), actual_h)) for y in plan.breakpoints
                ]
                fixed: list[int] = []
                for i in range(0, len(clamped) - 1, 2):
                    y0, y1 = clamped[i], clamped[i + 1]
                    if y1 <= y0:
                        y1 = min(actual_h, y0 + 1)
                    fixed.extend([y0, y1])
                clamped = fixed or [0, actual_h]
                ranges = photo_led_slice_ranges(clamped)
                plan = type(plan)(
                    breakpoints=clamped,
                    page_count=max(1, len(ranges)),
                    user_hint=plan.user_hint,
                    method=plan.method,
                )
            else:
                from travelogue.export.content_splitter import snap_breakpoints_to_legal

                clamped = clamp_breakpoints_to_height(plan.breakpoints, actual_h)
                # Moments only: re-snap to photo edges after height remap
                if profile.id == "wechat_moments":
                    legal = []
                    for c in boundaries.photo_cells:
                        legal.append(int(round(c.top_css * scale)))
                        legal.append(int(round(c.bottom_css * scale)))
                    for p in boundaries.as_points():
                        legal.append(p.y_canvas(scale))
                    if legal:
                        clamped = snap_breakpoints_to_legal(clamped, legal, actual_h)
                plan = type(plan)(
                    breakpoints=clamped,
                    page_count=max(1, len(clamped) - 1),
                    user_hint=plan.user_hint,
                    method=plan.method,
                )
                ranges = slice_ranges(plan.breakpoints)
            too_large = False
            for y0, y1 in ranges:
                slice_bytes = slice_canvas_png(canvas_bytes, y0, y1)
                if len(slice_bytes) > MAX_WECHAT_SLICE_BYTES:
                    too_large = True
                    break
            if not too_large:
                break

            if scale > 1 and scale_attempts < MAX_SCALE_DOWN_ATTEMPTS:
                scale -= 1
                scale_attempts += 1
                _report(
                    W_OPEN + 5,
                    W_TOTAL,
                    f"单张过大，降低清晰度至 {scale}× 并重新截图…",
                )
                continue
            if working_fmt == "png" and not tried_jpeg:
                working_fmt = "jpeg"
                tried_jpeg = True
                _report(W_OPEN + 10, W_TOTAL, "单张过大，改用 JPEG 重试…")
                continue
            raise LongshotExportError(
                "E_LNG2_SLICE_TOO_LARGE",
                "单张超过 20MB，请降低清晰度",
            )

        assert canvas_bytes is not None and plan is not None
        if plan.method == "photo_led":
            ranges = photo_led_slice_ranges(plan.breakpoints)
        else:
            ranges = slice_ranges(plan.breakpoints)
        page_count = len(ranges)
        user_hint = plan.user_hint
        publish_guide = _publish_guide(page_count, profile)
        if is_aspect or plan.method == "photo_led":
            target_page_count = page_count

        capture_done = W_OPEN + W_CAPTURE
        _report(
            capture_done,
            W_TOTAL,
            f"正在切分{label_noun}（0/{page_count}）…",
        )
        writer = PlatformExportWriter(
            trip_dir, prefix, ext=out_ext, single_file=single_file
        )
        try:
            with writer:
                for i, (y0, y1) in enumerate(ranges):
                    slice_bytes = slice_canvas_png(canvas_bytes, y0, y1)
                    if is_aspect and canvas_size:
                        w, h = canvas_size
                        slice_bytes = fit_aspect(
                            slice_bytes,
                            pad_mode=resolved_pad,
                            width=w,
                            height=h,
                            fmt=out_fmt,
                        )
                    elif len(slice_bytes) > MAX_WECHAT_SLICE_BYTES and working_fmt == "png":
                        raise LongshotExportError(
                            "E_LNG2_SLICE_TOO_LARGE",
                            "单张超过 20MB，请降低清晰度",
                        )
                    if not (single_file and page_count == 1):
                        slice_bytes = draw_page_footer(
                            slice_bytes, i + 1, page_count, fmt=out_fmt
                        )
                    writer.write(i + 1, slice_bytes)
                    split_pct = int(W_SPLIT * (i + 1) / max(page_count, 1))
                    _report(
                        capture_done + split_pct,
                        W_TOTAL,
                        f"正在切分{label_noun}（{i + 1}/{page_count}）…",
                    )
                finals = writer.commit()
            for path in finals:
                outputs.append(LongshotOutput(path=path, capture_method="p0"))
        except Exception:
            writer.rollback()
            raise

        _report(W_TOTAL, W_TOTAL, "写盘完成")
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                _log.debug("playwright page.close skipped", exc_info=True)
        _BROWSER_POOL.release()
        if server is not None:
            server.shutdown()
            server.server_close()

    return LongshotExportResult(
        outputs=outputs,
        capture_method="p0",
        title=title,
        segmented=len(outputs) > 1,
        segment_reason=f"platform_{profile.id}",
        user_hint=user_hint,
        platform=profile.id,
        profile_label=profile.label,
        target_page_count=target_page_count,
        publish_guide=publish_guide,
        page_count=page_count,
    )
