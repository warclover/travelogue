"""Longshot 2.0 branch B · platform segment export (ADR-016).

Single P0 full capture → boundary → DP split → postprocess → atomic write.
P1 fallback is forbidden (D-LNG2-10).

Phase A: wechat_moments (crop + footer).
Phase B: xiaohongshu (fit_aspect 3:4 + footer).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.export.boundary_metrics import collect_boundaries, count_photos_heuristic
from travelogue.export.content_splitter import (
    clamp_breakpoints_to_height,
    plan_moments_split,
    plan_xhs_split,
    slice_canvas_png,
    slice_ranges,
)
from travelogue.export.longshot import (
    CAPTURE_WIDTH,
    DEFAULT_EXPORT_SCALE,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _BROWSER_POOL,
    _apply_copy_display,
    _capture_p0,
    _page_metrics,
    _resolve_longshot_url,
    _slug_title,
    _trip_title,
)
from travelogue.export.platform_profiles import (
    DEFAULT_PLATFORM,
    PLATFORM_SEGMENT_IDS,
    PlatformProfile,
    file_prefix_for_platform,
    get_profile,
)
from travelogue.export.slide_postprocess import draw_page_footer, fit_aspect
from travelogue.render.engine import LONGSHOT_INDEX_NAME

_log = logging.getLogger(__name__)

MEMORY_BUDGET_BYTES = 400 * 1024 * 1024
MAX_WECHAT_SLICE_BYTES = 20 * 1024 * 1024
MAX_SCALE_DOWN_ATTEMPTS = 2


class PlatformExportWriter:
    """Atomic ``.part`` → rename writer (D-LNG2-14)."""

    def __init__(self, directory: Path, prefix: str, *, ext: str = "png") -> None:
        self.directory = Path(directory)
        self.prefix = prefix
        self.ext = ext.lstrip(".")
        self._parts: list[Path] = []
        self._finals: list[Path] = []
        self._committed = False

    def part_path(self, nn: int) -> Path:
        return self.directory / f"{self.prefix}-{nn:02d}.{self.ext}.part"

    def final_path(self, nn: int) -> Path:
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


def _capture_full_p0_only(page: Any, *, scale: int, fmt: str) -> bytes:
    try:
        data, method = _capture_p0(page, scale=scale, fmt=fmt)
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
    return data


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
    return (
        f"发布步骤：1. 在文件夹按 01→{page_count:02d} 全选（图底 i/n 助 orientation）"
        " 2. 朋友圈 → 从相册选择 3. 按顺序发布 · 滑动可连读"
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
    if raw == "smart_crop" and not smart_crop_enabled:
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
    """Branch B entry · wechat_moments / xiaohongshu."""
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

    is_xhs = profile.id == "xiaohongshu"
    if smart_crop_enabled is None:
        smart_crop_enabled = _smart_crop_flag_from_config()
    resolved_pad = _resolve_pad_mode(
        pad_mode, profile, smart_crop_enabled=bool(smart_crop_enabled)
    )

    scale = max(1, min(int(scale), 3))
    # xhs final output is always PNG 1080×1440; capture may still use jpeg under size pressure
    fmt = "jpeg" if str(fmt).lower() == "jpeg" else "png"
    out_fmt = "png" if is_xhs else fmt
    out_ext = "png" if is_xhs else ("jpg" if fmt == "jpeg" else "png")
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
        None if is_xhs else int(profile.target_pages or 9)
    )
    label_noun = "小红书配图" if is_xhs else "朋友圈配图"

    try:
        _report(W_OPEN, W_TOTAL, "正在打开页面…")
        page = browser.new_page(viewport={"width": CAPTURE_WIDTH, "height": 844})
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        page.wait_for_function(
            "() => window.TravelogueLongshot && document.documentElement.dataset.longshot === 'on'",
            timeout=30_000,
        )
        _apply_copy_display(page, copy_display)

        metrics = _page_metrics(page)
        scroll_h = float(metrics.get("scrollHeight") or 0)
        scale = auto_downgrade_scale(scroll_h, scale)

        canvas_bytes: bytes | None = None
        plan = None
        working_fmt = fmt
        scale_attempts = 0
        tried_jpeg = False

        while True:
            _report(W_OPEN + 5, W_TOTAL, "正在采集切分边界…")
            boundaries = collect_boundaries(page)
            photo_count = count_photos_heuristic(page)
            scroll_h = boundaries.scroll_height_css or scroll_h
            scale = auto_downgrade_scale(scroll_h, scale)

            _log.info(
                "platform longshot capture estimate_bytes=%s scale=%s platform=%s",
                estimate_capture_memory_bytes(scroll_h, scale=scale),
                scale,
                profile.id,
            )
            _report(W_OPEN + 10, W_TOTAL, "正在全页截图…")
            canvas_bytes = _capture_full_p0_only(page, scale=scale, fmt=working_fmt)

            if is_xhs:
                plan = plan_xhs_split(
                    scroll_height_css=boundaries.scroll_height_css,
                    boundaries_css=boundaries.as_points(),
                    scale=scale,
                    photo_count=photo_count,
                    slide_count=slide_count,
                )
            else:
                plan = plan_moments_split(
                    scroll_height_css=boundaries.scroll_height_css,
                    boundaries_css=boundaries.as_points(),
                    scale=scale,
                    photo_count=photo_count,
                )
            # Align CSS×scale breakpoints to actual captured PNG height
            from io import BytesIO

            from PIL import Image as _PILImage

            actual_h = _PILImage.open(BytesIO(canvas_bytes)).height
            clamped = clamp_breakpoints_to_height(plan.breakpoints, actual_h)
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
        ranges = slice_ranges(plan.breakpoints)
        page_count = len(ranges)
        user_hint = plan.user_hint
        publish_guide = _publish_guide(page_count, profile)
        if is_xhs:
            target_page_count = page_count

        capture_done = W_OPEN + W_CAPTURE
        _report(
            capture_done,
            W_TOTAL,
            f"正在切分{label_noun}（0/{page_count}）…",
        )
        writer = PlatformExportWriter(trip_dir, prefix, ext=out_ext)
        try:
            with writer:
                for i, (y0, y1) in enumerate(ranges):
                    slice_bytes = slice_canvas_png(canvas_bytes, y0, y1)
                    if is_xhs:
                        slice_bytes = fit_aspect(
                            slice_bytes,
                            pad_mode=resolved_pad,
                            fmt=out_fmt,
                        )
                    elif len(slice_bytes) > MAX_WECHAT_SLICE_BYTES and working_fmt == "png":
                        raise LongshotExportError(
                            "E_LNG2_SLICE_TOO_LARGE",
                            "单张超过 20MB，请降低清晰度",
                        )
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
