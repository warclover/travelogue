"""Shared config helpers (logging, YAML, tri-state normalizers)."""

from __future__ import annotations

import logging
from typing import Literal

from travelogue.constants import VALID_ARC_MODES, VALID_NARRATIVE_SCOPES

TriState = Literal["true", "false", "auto"]

_log = logging.getLogger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def normalize_arc_mode(raw: object) -> str:
    val = str(raw or "legacy").strip().lower()
    if val not in VALID_ARC_MODES:
        _log.warning("invalid curate.arc_mode %r, using legacy", raw)
        return "legacy"
    return val


def normalize_narrative_scope(raw: object) -> str:
    val = str(raw or "frame").strip().lower()
    if val not in VALID_NARRATIVE_SCOPES:
        _log.warning("invalid narrative.scope %r, using frame", raw)
        return "frame"
    return val


def normalize_tri_state(raw: object, *, default: str = "auto") -> str:
    if isinstance(raw, bool):
        return "true" if raw else "false"
    val = str(raw or default).strip().lower()
    if val in ("true", "1", "on", "yes"):
        return "true"
    if val in ("false", "0", "off", "no"):
        return "false"
    if val == "auto":
        return "auto"
    _log.warning("invalid tri-state %r, using %s", raw, default)
    return default


def capability_allows(flag: object, *, ready: bool) -> tuple[bool, str | None]:
    """ALG-V3 §3.2.1 · Ready 层真值（不蕴含 MayCall / 实调）.

    Returns ``(allowed, degrade_reason)``. ``degrade_reason`` is ``llm_no_key`` only
    when the user explicitly set ``true`` but credentials are missing.
    """
    state = normalize_tri_state(flag, default="auto")
    if state == "false":
        return False, None
    if state == "true":
        if ready:
            return True, None
        return False, "llm_no_key"
    # auto
    return (True, None) if ready else (False, None)
