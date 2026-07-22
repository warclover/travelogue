"""NAS · AI 产品面门控（No-AI Surface V1）。

默认关闭用户面 AI；工程栈保留。见 docs/PRD-NO-AI-SURFACE-V1.md §5 ·
docs/IMPLEMENTATION-NO-AI-SURFACE-V1.md BE-NAS-01～03。
"""

from __future__ import annotations

import os
from typing import Any

ENV_AI_SURFACE = "TRAVELOGUE_AI_SURFACE"

_TRUTHY = frozenset({"1", "true", "on", "yes"})


def _env_truthy(raw: str | None = None) -> bool:
    val = (raw if raw is not None else os.environ.get(ENV_AI_SURFACE, "")).strip().lower()
    return val in _TRUTHY


def resolve_ai_surface_enabled(cfg: Any | None = None) -> bool:
    """env ∪ studio.ai_surface_enabled；默认 False。"""
    if _env_truthy():
        return True
    if cfg is None:
        return False
    studio = getattr(cfg, "studio", None)
    if studio is None:
        return False
    return bool(getattr(studio, "ai_surface_enabled", False))


def ai_surface_disabled_body() -> dict[str, Any]:
    from travelogue.web.studio_errors import user_message

    return {
        "ok": False,
        "error": "E_AI_SURFACE_DISABLED",
        "message": user_message("E_AI_SURFACE_DISABLED", "当前版本不可用"),
    }
