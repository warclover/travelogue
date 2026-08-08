"""Title Art Engine configuration (PRD-COVER-CALLIGRAPHY-TITLE-V1 · CAL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TitleArtConfig:
    #: D-CAL-05 · 未过验收前默认关闭；显式开启后才会写 trip.meta.titleArt。
    enabled: bool = False
    #: D-CAL-14 · 路线 C 仅是候选；W0.5 Spike（2026-08-08，26 条真实/边界标题）
    #: 实测 OCR 回读通过率仅 57.7%，远低于生产可用门槛（见 AC-CAL-11），默认关
    #: 闭，走路线 B 兜底。
    route_c_enabled: bool = False
    route_c_style_id: str | None = None  # None → style_registry.default_style_id()
    model_provider: str = "wanxiang"
    model_name: str = "wanx2.1-t2i-plus"  # D-CAL-18 · 2026-08-07 实测字形优于 turbo
    ocr_verify: bool = True  # D-CAL-19


def title_art_config_from_dict(raw: dict[str, Any] | None) -> TitleArtConfig:
    raw = raw or {}
    return TitleArtConfig(
        enabled=bool(raw.get("enabled", False)),
        route_c_enabled=bool(raw.get("route_c_enabled", raw.get("routeCEnabled", False))),
        route_c_style_id=(
            str(raw.get("route_c_style_id", raw.get("routeCStyleId")) or "").strip() or None
        ),
        model_provider=str(raw.get("model_provider", raw.get("modelProvider", "wanxiang"))),
        model_name=str(raw.get("model_name", raw.get("modelName", "wanx2.1-t2i-plus"))),
        ocr_verify=bool(raw.get("ocr_verify", raw.get("ocrVerify", True))),
    )
