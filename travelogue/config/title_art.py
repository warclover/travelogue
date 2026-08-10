"""Title Art Engine configuration (PRD-COVER-CALLIGRAPHY-TITLE-V1 · CAL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TitleArtConfig:
    #: D-CAL-05 · 2026-08-09 AC-CAL-BLIND 通过（W3 单一评委协议，艺术字侧胜率
    #: 91.7%）后默认改为开启；仍受路线 B fail-open 兜底（非白名单/focal 冲突/
    #: 生成失败均静默回落现网 CSS 标题），无需人工再确认单个 trip。
    enabled: bool = True
    #: D-CAL-14 / OQ-CAL-06 · 路线 C 为可退回的优先路径总闸。
    #: Studio 在 ``enabled=True`` 时展示「优先 AI 手写体」勾选框，且**默认勾选**；
    #: 用户可取消（偏好记 localStorage）；仍须点击「生成装帧标题」才会触发，
    #: 不会在渲染管线自动走 AI。效果不好 / OCR 不过时按既有分层回退路线 B。
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
        enabled=bool(raw.get("enabled", True)),
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
