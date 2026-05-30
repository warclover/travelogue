"""Small helpers for reading config.yaml dicts (snake_case + camelCase keys)."""

from __future__ import annotations

from typing import Any


def cfg_get(raw: dict[str, Any], snake: str, camel: str, default: Any) -> Any:
    """Return ``raw[snake]`` if present, else ``raw[camel]``, else ``default``."""
    if snake in raw:
        return raw[snake]
    if camel in raw:
        return raw[camel]
    return default


def cfg_bool(raw: dict[str, Any], snake: str, camel: str, default: bool = False) -> bool:
    return bool(cfg_get(raw, snake, camel, default))


def cfg_int(raw: dict[str, Any], snake: str, camel: str, default: int = 0) -> int:
    return int(cfg_get(raw, snake, camel, default))


def cfg_float(raw: dict[str, Any], snake: str, camel: str, default: float = 0.0) -> float:
    return float(cfg_get(raw, snake, camel, default))


def cfg_str(raw: dict[str, Any], snake: str, camel: str, default: str = "") -> str:
    return str(cfg_get(raw, snake, camel, default))


def cfg_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    val = raw.get(key)
    return val if isinstance(val, dict) else {}
