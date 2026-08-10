"""Unified ACP disk cache shell · D-ACP-06 (W1a: generic KV; narrate stays dual-track)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def content_sig(*parts: Any, prompt_version: str = "v1") -> str:
    """Stable short digest for cache keys."""
    raw = json.dumps(
        {"parts": list(parts), "promptVersion": prompt_version},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def cache_path(cache_dir: Path, *, agent: str, sig: str) -> Path:
    safe_agent = agent.replace("/", "_").replace("\\", "_")
    return cache_dir / safe_agent / f"{sig}.json"


def read_cached(cache_dir: Path, *, agent: str, sig: str) -> dict[str, Any] | None:
    path = cache_path(cache_dir, agent=agent, sig=sig)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_cached(
    cache_dir: Path,
    *,
    agent: str,
    sig: str,
    payload: dict[str, Any],
) -> None:
    path = cache_path(cache_dir, agent=agent, sig=sig)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
