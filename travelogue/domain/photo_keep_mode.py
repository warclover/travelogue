"""P9-F3 · 照片处理三档（recommended / keep_bursts / keep_all）。

互斥模式 → 派生 photoCullEnabled / keepNearDuplicates / skipLowResExclusion。
旧客户端只传两布尔时不得静默跳过低分闸（见 PRD-KEEP-ALL-PHOTOS-V1 §4.3–4.4）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PHOTO_KEEP_MODES = ("recommended", "keep_bursts", "keep_all")
DEFAULT_PHOTO_KEEP_MODE = "recommended"


@dataclass(frozen=True)
class PhotoKeepResolved:
    mode: str
    photo_cull_enabled: bool
    keep_near_duplicates: bool
    skip_low_res_exclusion: bool


def normalize_photo_keep_mode(raw: Any) -> str | None:
    text = str(raw or "").strip().lower()
    if text in PHOTO_KEEP_MODES:
        return text
    return None


def derive_from_mode(mode: str) -> PhotoKeepResolved:
    m = normalize_photo_keep_mode(mode) or DEFAULT_PHOTO_KEEP_MODE
    if m == "keep_all":
        return PhotoKeepResolved(
            mode="keep_all",
            photo_cull_enabled=False,
            keep_near_duplicates=True,
            skip_low_res_exclusion=True,
        )
    if m == "keep_bursts":
        return PhotoKeepResolved(
            mode="keep_bursts",
            photo_cull_enabled=True,
            keep_near_duplicates=True,
            skip_low_res_exclusion=False,
        )
    return PhotoKeepResolved(
        mode="recommended",
        photo_cull_enabled=True,
        keep_near_duplicates=False,
        skip_low_res_exclusion=False,
    )


def infer_mode_from_bools(
    *,
    photo_cull_enabled: bool,
    keep_near_duplicates: bool,
) -> str:
    """读旧盘推断展示档；永不推断为 keep_all（旧路径未跳低分闸）。"""
    # PRD §4.4：cull=false ∧ keep=true → keep_bursts；keep=true → keep_bursts；else recommended
    if (not photo_cull_enabled and keep_near_duplicates) or keep_near_duplicates:
        return "keep_bursts"
    return "recommended"


def resolve_photo_keep_prefs(
    *,
    photo_keep_mode: Any = None,
    photo_cull_enabled: bool | None = None,
    keep_near_duplicates: bool | None = None,
) -> PhotoKeepResolved:
    """优先 photoKeepMode；缺省时按两布尔兼容，且 skip_low_res 恒为 False。"""
    mode = normalize_photo_keep_mode(photo_keep_mode)
    if mode:
        return derive_from_mode(mode)
    cull = True if photo_cull_enabled is None else bool(photo_cull_enabled)
    keep = bool(keep_near_duplicates)
    inferred = infer_mode_from_bools(
        photo_cull_enabled=cull,
        keep_near_duplicates=keep,
    )
    # 兼容路径：保留调用方布尔，不因推断改写；永不跳低分
    return PhotoKeepResolved(
        mode=inferred,
        photo_cull_enabled=cull,
        keep_near_duplicates=keep,
        skip_low_res_exclusion=False,
    )


def should_skip_low_res_exclusion(intent: dict | None) -> bool:
    """keep_all（或显式 skipLowResExclusion）时跳过低分硬丢。"""
    data = intent if isinstance(intent, dict) else {}
    if data.get("skipLowResExclusion") is True:
        return True
    return normalize_photo_keep_mode(data.get("photoKeepMode")) == "keep_all"
