"""Pipeline Throughput · import-time precheck warnings (G-PT-08 / M3).

Warn when Studio/import config is misaligned with the P7 fast path — never block.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)


def collect_throughput_precheck_warnings(cfg: Any) -> list[str]:
    """Return human-readable warnings for misaligned performance knobs.

    Does not mutate config and must not raise for normal AppConfig shapes.
    """
    warnings: list[str] = []
    try:
        vision = cfg.vision
        pipeline = cfg.pipeline
        layout = getattr(cfg, "layout", None)
        layout_scoring = getattr(layout, "scoring", None) if layout is not None else None
        if layout_scoring is None:
            layout_scoring = getattr(cfg, "layout_scoring", None)
        clustering = getattr(cfg, "clustering", None)
    except AttributeError:
        return warnings

    vision_on = str(getattr(vision, "enabled", "false")).lower() != "false"
    if vision_on and not bool(getattr(pipeline, "parallel_embed", True)):
        warnings.append(
            "性能配置未对齐：vision 已启用但 pipeline.parallel_embed=false"
            "（P7 快路径建议开启 parallel_embed）"
        )

    if vision_on and not bool(getattr(vision, "session_singleton", True)):
        warnings.append(
            "性能配置未对齐：vision.session_singleton=false"
            "（P7 快路径建议保持 session 单例）"
        )

    if layout_scoring is not None and not bool(
        getattr(layout_scoring, "skip_duplicate_signatures", True)
    ):
        warnings.append(
            "性能配置未对齐：layout_scoring.skip_duplicate_signatures=false"
            "（P7 快路径建议跳过重复签名）"
        )

    if clustering is not None and bool(getattr(clustering, "force_recluster", False)):
        warnings.append(
            "性能提示：clustering.force_recluster=true 将跳过聚类缓存"
            "（非必要勿开；UI「重新生成」才应 regenerate）"
        )

    return warnings


def emit_throughput_precheck_warnings(
    cfg: Any,
    *,
    logger: logging.Logger | None = None,
) -> list[str]:
    """Log warnings (non-blocking) and return the same list for callers/tests."""
    warnings = collect_throughput_precheck_warnings(cfg)
    log = logger or _log
    for msg in warnings:
        log.warning("%s", msg)
    return warnings
