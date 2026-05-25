"""Disk cache for LLM narrate responses (keyed by brief hash)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def brief_hash(brief: dict[str, Any]) -> str:
    raw = json.dumps(brief, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def cache_file(
    cache_dir: Path,
    *,
    provider: str,
    model: str,
    scope: str,
    brief: dict[str, Any],
) -> Path:
    digest = brief_hash(brief)
    safe_scope = scope.replace("/", "_").replace("\\", "_")
    return cache_dir / provider / model / f"{safe_scope}-{digest}.json"


def read_cached(
    cache_dir: Path,
    *,
    provider: str,
    model: str,
    scope: str,
    brief: dict[str, Any],
) -> dict[str, Any] | None:
    path = cache_file(cache_dir, provider=provider, model=model, scope=scope, brief=brief)
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
    provider: str,
    model: str,
    scope: str,
    brief: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    path = cache_file(cache_dir, provider=provider, model=model, scope=scope, brief=brief)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
