"""Title Art Engine configuration (PRD-COVER-CALLIGRAPHY-TITLE-V1 · CAL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TitleArtConfig:
    #: D-CAL-05 · 未过验收前默认关闭；显式开启后才会写 trip.meta.titleArt。
    enabled: bool = False
    #: D-CAL-14 / OQ-CAL-06 · 路线 C 为**用户可选高级项**总闸。
    #: W0.5b 后默认 ``True``：Studio 在 ``enabled=True`` 时展示「尝试 AI 手写体」
    #: 勾选框；用户**仍须勾选**才会尝试路线 C（不会自动走 AI）。
    #: 关掉本开关则勾选框隐藏，请求里的 ``routeC`` 也会被服务端静默忽略。
    route_c_enabled: bool = True
    route_c_style_id: str | None = None  # None → style_registry.default_style_id()
    model_provider: str = "wanxiang"
    model_name: str = "wanx2.1-t2i-plus"  # D-CAL-18 · 2026-08-07 实测字形优于 turbo
    ocr_verify: bool = True  # D-CAL-19 · 生产必须 True；仅测试可关
    #: Prompt 模板版本（style_registry）；默认 v2（逐字准确强化）。
    prompt_version: str = "v2"
    #: 路线 C 生成尝试次数（含首次）。OCR mismatch 后最多再生成 ``attempts-1`` 次。
    route_c_max_attempts: int = 2


def title_art_config_from_dict(raw: dict[str, Any] | None) -> TitleArtConfig:
    raw = raw or {}
    attempts_raw = raw.get("route_c_max_attempts", raw.get("routeCMaxAttempts", 2))
    try:
        attempts = int(attempts_raw)
    except (TypeError, ValueError):
        attempts = 2
    attempts = max(1, min(attempts, 3))
    return TitleArtConfig(
        enabled=bool(raw.get("enabled", False)),
        route_c_enabled=bool(raw.get("route_c_enabled", raw.get("routeCEnabled", True))),
        route_c_style_id=(
            str(raw.get("route_c_style_id", raw.get("routeCStyleId")) or "").strip() or None
        ),
        model_provider=str(raw.get("model_provider", raw.get("modelProvider", "wanxiang"))),
        model_name=str(raw.get("model_name", raw.get("modelName", "wanx2.1-t2i-plus"))),
        ocr_verify=bool(raw.get("ocr_verify", raw.get("ocrVerify", True))),
        prompt_version=str(
            raw.get("prompt_version", raw.get("promptVersion", "v2")) or "v2"
        ).strip()
        or "v2",
        route_c_max_attempts=attempts,
    )
