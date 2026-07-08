"""Read-only template admin state (layer-0 · avoids layout↔templating imports)."""

from __future__ import annotations

import json
import threading
from typing import Any

from travelogue.paths import ROOT

_ADMIN_STATE_PATH = ROOT / "runs" / "template_admin_state.json"
STATE_PATH = _ADMIN_STATE_PATH  # shared with templating.admin_store
_LOCK = threading.Lock()
_RUNTIME_CACHE: tuple[float, dict[str, Any]] | None = None


def _load_unlocked() -> dict[str, Any]:
    if not _ADMIN_STATE_PATH.is_file():
        return {"revision": 0, "templates": {}, "audit": [], "runtime": {}}
    try:
        data = json.loads(_ADMIN_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"revision": 0, "templates": {}, "audit": []}
    if not isinstance(data, dict):
        return {"revision": 0, "templates": {}, "audit": []}
    data.setdefault("revision", 0)
    data.setdefault("templates", {})
    data.setdefault("audit", [])
    data.setdefault("runtime", {})
    return data


def load_runtime_overrides() -> dict[str, Any]:
    """Return runtime overrides block from admin state (mtime-cached)."""
    global _RUNTIME_CACHE
    with _LOCK:
        try:
            mtime = _ADMIN_STATE_PATH.stat().st_mtime
        except OSError:
            mtime = -1.0
        cache = _RUNTIME_CACHE
        if cache is not None and cache[0] == mtime:
            return dict(cache[1])
        runtime = dict(_load_unlocked().get("runtime") or {})
        _RUNTIME_CACHE = (mtime, runtime)
        return dict(runtime)


def get_review_status(template_id: str) -> dict[str, Any]:
    """Review workflow status for a template (read-only)."""
    with _LOCK:
        row = dict((_load_unlocked().get("templates") or {}).get(template_id) or {})
    review = dict(row.get("review") or {})
    return {
        "templateId": template_id,
        "status": str(review.get("status") or "none"),
        "submittedAt": review.get("submittedAt"),
        "submittedBy": review.get("submittedBy"),
        "reviewedAt": review.get("reviewedAt"),
        "reviewedBy": review.get("reviewedBy"),
        "note": review.get("note"),
    }
