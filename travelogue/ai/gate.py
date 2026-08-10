"""ACP call-front gate · D-ACP-14 (AND) + D-ACP-13 timeout knobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.llm.ready import probe_llm_ready, resolve_llm_may_call, resolve_ready_provider


@dataclass(frozen=True)
class GateDecision:
    """Result of the ACP pre-call gate."""

    allow: bool
    reason: str
    """Machine reason: ``ok`` | ``capability_disabled`` | ``surface_off`` | ``no_key`` | ``stub``."""

    provider: str = "stub"


def check_gate(*, cfg: AppConfig | None = None) -> GateDecision:
    """D-ACP-14: ``ai_capability.enabled`` ∧ ``aiSurfaceEnabled`` ∧ valid non-stub Key.

    When ``ai_capability.enabled`` is False, returns ``allow=False`` with
    ``capability_disabled`` — callers treating ACP as opt-in should pass through
    to legacy paths instead of forcing fallback.
    """
    app_cfg = cfg or get_config()
    acp = getattr(app_cfg, "ai_capability", None)
    if acp is None or not bool(getattr(acp, "enabled", False)):
        return GateDecision(allow=False, reason="capability_disabled", provider="stub")

    if not resolve_llm_may_call(cfg=app_cfg):
        return GateDecision(allow=False, reason="surface_off", provider="stub")

    provider = resolve_ready_provider(cfg=app_cfg)
    if provider == "stub":
        return GateDecision(allow=False, reason="stub", provider="stub")
    if not probe_llm_ready(cfg=app_cfg):
        return GateDecision(allow=False, reason="no_key", provider=provider)
    return GateDecision(allow=True, reason="ok", provider=provider)


def acp_instrumentation_active(*, cfg: AppConfig | None = None) -> bool:
    """True when ACP wrappers should enforce gate/budget (not mere pass-through)."""
    app_cfg = cfg or get_config()
    acp = getattr(app_cfg, "ai_capability", None)
    return bool(acp is not None and getattr(acp, "enabled", False))


def timeout_sec(*, cfg: AppConfig | None = None) -> float:
    app_cfg = cfg or get_config()
    acp = getattr(app_cfg, "ai_capability", None)
    if acp is None:
        return 8.0
    return float(getattr(acp, "timeout_sec", 8.0) or 8.0)
