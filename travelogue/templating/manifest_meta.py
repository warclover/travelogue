"""Load templateMeta (discovery + guardrails) from manifest.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTROLLED_TAGS = frozenset(
    {
        "multi-day",
        "single-day",
        "event",
        "video-heavy",
        "map",
        "family",
        "travel",
        "outdoor",
        "urban",
    }
)
CONTROLLED_CATEGORIES = frozenset({"travel", "event", "family", "general"})


def _normalize_tags(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[str] = []
    for item in raw:
        tag = str(item).strip().lower()
        if tag in CONTROLLED_TAGS and tag not in out:
            out.append(tag)
    return tuple(out)


@lru_cache(maxsize=32)
def load_template_meta(manifest_path: str) -> dict[str, Any]:
    path = Path(manifest_path)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    meta = data.get("templateMeta")
    if not isinstance(meta, dict):
        return {}
    category = str(meta.get("category") or "general").strip().lower()
    if category not in CONTROLLED_CATEGORIES:
        category = "general"
    return {
        "category": category,
        "tags": _normalize_tags(meta.get("tags")),
        "style": str(meta.get("style") or "").strip() or None,
        "complexity": str(meta.get("complexity") or "").strip() or None,
        "bestFor": tuple(str(x).strip() for x in (meta.get("bestFor") or []) if str(x).strip()),
        "editableScopes": tuple(str(x).strip() for x in (meta.get("editableScopes") or []) if str(x).strip()),
        "lockedScopes": tuple(str(x).strip() for x in (meta.get("lockedScopes") or []) if str(x).strip()),
        "placeholders": meta.get("placeholders") if isinstance(meta.get("placeholders"), dict) else {},
    }
