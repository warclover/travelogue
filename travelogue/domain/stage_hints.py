"""FTUE W1 · frozen stageHint keys and user-visible copy (AC-FTUE-07).

Share-Face Closeout W0 · vision_warmup 人话主句（D-SFC-04）。

Lives in domain so export/curation can emit hints without importing web.
"""

from __future__ import annotations

import os
import time

# Enum keys (may appear in job.stageHint); FE maps via STAGE_HINT_LABELS.
PREPARING_VISION = "preparing_vision"
VISION_WARMUP = "vision_warmup"
PREPARING_BROWSER = "preparing_browser"
PROCESSING_PHOTOS = "processing_photos"
# PRD-PIPELINE-PERF-V1 · R5.1 · two-state progressive readiness
LAYOUT_PREVIEW_READY = "layout_preview_ready"
EXPORT_READY = "export_ready"

# SFC · 识图准备主句（禁止 HF/CLIP/权重文件名）
_VISION_WARMUP_COPY = "正在准备识图（首次可能较慢）"

# SFC · vision 失败降级 toast（D-SFC-05 · AC-SFC-05）
VISION_DOWNGRADE_NOTICE = "识图未启用，已用时间与张数整理"

# BLK-06 / AC-SFC-04 · 测试注入：人为延长 vision_warmup 可见窗口（毫秒，上限 60s）
_VISION_WARMUP_DELAY_ENV = "TRAVELOGUE_SFC_VISION_WARMUP_DELAY_MS"
_VISION_WARMUP_DELAY_CAP_MS = 60_000

STAGE_HINT_COPY: dict[str, str] = {
    PREPARING_VISION: _VISION_WARMUP_COPY,
    VISION_WARMUP: _VISION_WARMUP_COPY,
    PREPARING_BROWSER: "正在准备长图组件（仅第一次）…",
    PROCESSING_PHOTOS: "正在整理照片…",
    LAYOUT_PREVIEW_READY: "版面已就绪，可先预览",
    EXPORT_READY: "高清图与导出准备完成",
}


def stage_hint_text(key_or_text: str) -> str:
    """Resolve frozen key → user copy; pass through unknown/custom hints."""
    raw = (key_or_text or "").strip()
    if not raw:
        return ""
    return STAGE_HINT_COPY.get(raw, raw)


def maybe_sleep_vision_warmup_inject() -> float:
    """AC-SFC-04 可测锁：按环境变量睡眠，返回实际睡眠秒数。"""
    raw = (os.environ.get(_VISION_WARMUP_DELAY_ENV) or "").strip()
    if not raw:
        return 0.0
    try:
        ms = int(raw)
    except ValueError:
        return 0.0
    if ms <= 0:
        return 0.0
    seconds = min(ms, _VISION_WARMUP_DELAY_CAP_MS) / 1000.0
    time.sleep(seconds)
    return seconds
