"""Export writer dispatch by (platform, edition) — DPI W2 · S-07."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.export.longshot import (
    DEFAULT_EXPORT_SCALE,
    CancelCheckFn,
    CancelRegisterFn,
    LongshotExportResult,
    ProgressFn,
    export_journal_longshot,
)


def dispatch_export(
    trip_dir: Path,
    *,
    scale: int = DEFAULT_EXPORT_SCALE,
    fmt: str = "png",
    chapter: int | None = None,
    output: Path | None = None,
    base_url: str | None = None,
    trip_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    timeout_ms: int = 180_000,
    watermark: bool = True,
    progress: ProgressFn | None = None,
    copy_display: str = "full",
    segment_mode: str = "auto",
    platform: str | None = None,
    slide_count: int | None = None,
    pad_mode: str | None = None,
    profile: Any = None,
    include_appendix: bool = False,
    cancel_check: CancelCheckFn | None = None,
    cancel_register: CancelRegisterFn | None = None,
    include_zip: bool = True,
    include_pages: bool = True,
) -> LongshotExportResult:
    """Pick a writer. The only edition ``if`` in the export entry path."""
    from travelogue.export.platform_profiles import DEFAULT_PLATFORM, normalize_platform_id

    pid = normalize_platform_id(platform)
    if pid == "moments_grid":
        from travelogue.export.photo_grid_pack import export_photo_grid_pack

        return export_photo_grid_pack(
            trip_dir,
            scale=scale,
            fmt=fmt,
            progress=progress,
        )
    if pid == "poster_bric":
        from travelogue.export.poster_bric_pack import export_poster_bric_pack

        return export_poster_bric_pack(
            trip_dir,
            scale=scale,
            fmt=fmt,
            progress=progress,
            platform=pid,
        )
    if pid == "portfolio_pages":
        from travelogue.export.portfolio_pages import export_portfolio_bundle

        return export_portfolio_bundle(
            trip_dir,
            scale=scale,
            fmt=fmt,
            progress=progress,
            cancel_check=cancel_check,
            cancel_register=cancel_register,
            timeout_ms=timeout_ms,
            host=host,
            port=port,
            include_zip=include_zip,
            include_pages=include_pages,
        )
    if pid in ("xiaohongshu", "wechat_official", "album_spread"):
        from travelogue.export.collage_pack import export_collage_pack

        cfg = None
        try:
            from travelogue.config import get_config

            cfg = get_config()
        except Exception:
            cfg = None
        return export_collage_pack(
            trip_dir,
            platform=pid,
            scale=scale,
            fmt=fmt,
            progress=progress,
            slide_count=slide_count,
            cfg=cfg,
        )
    if pid == DEFAULT_PLATFORM:
        from travelogue.export.portfolio_wechat import (
            export_portfolio_wechat_from_kept,
            trip_is_portfolio,
        )

        if trip_is_portfolio(trip_dir):
            return export_portfolio_wechat_from_kept(
                trip_dir,
                scale=scale,
                fmt=fmt,
                progress=progress,
            )
    if pid != DEFAULT_PLATFORM:
        from travelogue.export.platform_longshot import export_platform_longshot

        return export_platform_longshot(
            trip_dir,
            platform=pid,
            scale=scale,
            fmt=fmt,
            base_url=base_url,
            trip_id=trip_id,
            host=host,
            port=port,
            timeout_ms=timeout_ms,
            progress=progress,
            copy_display=copy_display,
            slide_count=slide_count,
            pad_mode=pad_mode,
            profile=profile,
            cancel_check=cancel_check,
            cancel_register=cancel_register,
        )
    return export_journal_longshot(
        trip_dir,
        scale=scale,
        fmt=fmt,
        chapter=chapter,
        output=output,
        base_url=base_url,
        trip_id=trip_id,
        host=host,
        port=port,
        timeout_ms=timeout_ms,
        watermark=watermark,
        progress=progress,
        copy_display=copy_display,
        segment_mode=segment_mode,
        include_appendix=include_appendix,
        cancel_check=cancel_check,
        cancel_register=cancel_register,
    )
