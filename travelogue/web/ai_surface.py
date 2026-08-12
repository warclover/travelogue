"""NAS · AI 产品面门控（No-AI Surface V1）。

默认关闭用户面 AI；工程栈保留。见 docs/PRD-NO-AI-SURFACE-V1.md §5 ·
docs/IMPLEMENTATION-NO-AI-SURFACE-V1.md BE-NAS-01～03。

SAS · D-SAS-07：连接配置（status / settings / ping）不要求开闸，可先配 Key；
烧模型动作（narrate 等）仍走本模块门控。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ENV_AI_SURFACE = "TRAVELOGUE_AI_SURFACE"

_TRUTHY = frozenset({"1", "true", "on", "yes"})


def _env_truthy(raw: str | None = None) -> bool:
    val = (raw if raw is not None else os.environ.get(ENV_AI_SURFACE, "")).strip().lower()
    return val in _TRUTHY


def resolve_ai_surface_enabled(cfg: Any | None = None) -> bool:
    """env ∪ studio.ai_surface_enabled；默认 False。

    配置旗标须为真正的 ``True``（避免 MagicMock 等 truthy 伪阳）。
    """
    if _env_truthy():
        return True
    if cfg is None:
        return False
    studio = getattr(cfg, "studio", None)
    if studio is None:
        return False
    return getattr(studio, "ai_surface_enabled", False) is True


def resolve_ai_surface_for_request(handler: Any | None = None) -> bool:
    """请求时读盘最新配置（对齐 GET /config），避免 serve 启动时 pin 的 app_config 过期。

    仅用于烧模型类硬门闩；连接 API 见 handlers 内「不要求开闸」注释。
    """
    if _env_truthy():
        return True
    path = getattr(handler, "studio_config_path", None) if handler is not None else None
    if path:
        p = Path(path)
        if p.is_file():
            from travelogue.config import load_config

            return resolve_ai_surface_enabled(load_config(p))
    from travelogue.config import get_config

    return resolve_ai_surface_enabled(get_config(reload=True))


def ai_surface_disabled_body() -> dict[str, Any]:
    from travelogue.web.studio_errors import user_message

    return {
        "ok": False,
        "error": "E_AI_SURFACE_DISABLED",
        "message": user_message("E_AI_SURFACE_DISABLED", "当前版本不可用"),
    }
