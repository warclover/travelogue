"""trip.meta.titleArt data model (PRD §8 · D-CAL-09, v0.3 路线C字段扩展)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ENGINE_ROUTE_B = "clean-pipeline-v1"
ENGINE_ROUTE_C = "diffusion-fixed-prompt-v1"


@dataclass(frozen=True)
class TitleArtResult:
    version: int = 1
    enabled: bool = False
    stale: bool = False
    engine: str = ENGINE_ROUTE_B
    template: str = ""
    font: str = ""
    main_source: str = "displayTitle"
    main_rendered: str = ""
    truncated: bool = False
    subtitle: str | None = None
    main_color: str = "#ffffff"
    seal_color: str = "#B03A2E"
    opening_style_id: str = ""
    position: dict[str, float] = field(default_factory=lambda: {"x": 0.5, "y": 0.28})
    asset_path: str = ""
    source_title: str = ""
    explain: list[str] = field(default_factory=list)
    # v0.3 · 路线 C 专属字段（路线 B 时留空/None）
    style_id: str | None = None
    prompt_version: str | None = None
    model_provider: str | None = None
    ocr_verified: bool | None = None
    fallback_from: str | None = None

    def to_meta_dict(self) -> dict[str, Any]:
        """Serialize to the exact ``trip.meta.titleArt`` shape (PRD §8)."""
        out: dict[str, Any] = {
            "version": self.version,
            "enabled": self.enabled,
            "stale": self.stale,
            "engine": self.engine,
            "template": self.template,
            "font": self.font,
            "mainSource": self.main_source,
            "mainRendered": self.main_rendered,
            "truncated": self.truncated,
            "subtitle": self.subtitle,
            "mainColor": self.main_color,
            "sealColor": self.seal_color,
            "openingStyleId": self.opening_style_id,
            "position": dict(self.position),
            "assetPath": self.asset_path,
            "sourceTitle": self.source_title,
            "explain": list(self.explain),
        }
        if self.engine == ENGINE_ROUTE_C:
            out.update(
                {
                    "styleId": self.style_id,
                    "promptVersion": self.prompt_version,
                    "modelProvider": self.model_provider,
                    "ocrVerified": self.ocr_verified,
                    "fallbackFrom": self.fallback_from,
                }
            )
        elif self.fallback_from:
            # 路线 B 展示但曾尝试过路线 C 并降级：仍记录 fallbackFrom 便于观测。
            out["fallbackFrom"] = self.fallback_from
        return out


def disabled_meta_dict(reason: str | None = None) -> dict[str, Any]:
    """Fail-open / 非白名单 / 空标题时写回的最小占位（≡ 现网 HTML 标题）。

    ``reason`` 默认不写（保持跟既有调用点完全一致的最小形状），仅在调用方
    想为某次 fail-open 留痕时显式传入（如 D-CAL-20 ④ 的 focal 冲突回退），
    便于事后从 trip.json 直接读出「这次为什么没生成艺术字」。
    """
    out: dict[str, Any] = {"version": 1, "enabled": False, "stale": False}
    if reason:
        out["reason"] = reason
    return out
